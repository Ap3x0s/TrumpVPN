from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import PromoCode, PromoRedemption, User


class PromoError(Exception):
    pass


def _normalize(code: str) -> str:
    return (code or "").strip().upper()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def compute_payable(amount_rub: int, percent: int) -> int:
    pct = max(0, min(95, int(percent or 0)))
    return max(1, round(amount_rub * (100 - pct) / 100)) if amount_rub > 0 else 0


def _validation_error(db: Session, promo: PromoCode, user: User) -> str | None:
    if not promo.enabled:
        return "Promo code is disabled"
    now = _now()
    if promo.starts_at and now < promo.starts_at:
        return "Promo is not active yet"
    if promo.ends_at and now > promo.ends_at:
        return "Promo has expired"
    if promo.max_uses_per_user > 0:
        used = db.scalar(
            select(PromoRedemption)
            .where(PromoRedemption.promo_code_id == promo.id, PromoRedemption.user_id == user.id)
        )
        if used:
            return "Promo already used"
    if promo.max_uses_total > 0:
        total = db.scalar(
            select(PromoRedemption).where(PromoRedemption.promo_code_id == promo.id)
        )
        if total:
            return "Promo usage limit reached"
    return None


def apply_promo_percent(db: Session, user: User, code_raw: str, amount_rub: int) -> int:
    """Attach a discount promo to the user (pending). Returns percent 1..95, or 0 if invalid."""
    code = _normalize(code_raw)
    if len(code) < 2:
        return 0
    promo = db.scalar(select(PromoCode).where(PromoCode.code == code))
    if not promo or promo.kind != "discount_percent":
        return 0
    if _validation_error(db, promo, user):
        return 0
    percent = max(1, min(95, int(promo.value_int or 0)))
    user.pending_discount_promo_id = promo.id
    db.flush()
    return percent


def record_redemption(db: Session, user: User, payment_invoice_id: int) -> None:
    """Called after a successful payment to record the redemption for the applied promo."""
    if not user.pending_discount_promo_id:
        return
    promo = db.get(PromoCode, user.pending_discount_promo_id)
    if not promo:
        return
    db.add(PromoRedemption(
        promo_code_id=promo.id,
        user_id=user.id,
        payment_invoice_id=payment_invoice_id,
        kind=promo.kind,
        value_int=int(promo.value_int or 0),
    ))
    user.pending_discount_promo_id = None
    db.flush()
