import hashlib
import time

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.deps import get_current_user
from app.models import PaymentInvoice, User
from app.plans import PLAN_BY_ID
from app.schemas import CreatePaymentRequest, PaymentCreatedOut, PaymentStatusOut
from app.services import cryptobot
from app.services.promo import apply_promo_percent, compute_payable, record_redemption
from app.services.subscription import activate_subscription

router = APIRouter(prefix="/api/payments", tags=["payments"])


def _new_invoice_id(db: Session) -> int:
    last = int(db.scalar(select(func.coalesce(func.max(PaymentInvoice.invoice_id), 0))) or 0)
    return max(last + 1, int(time.time()))


@router.post("/create")
def create_payment(payload: CreatePaymentRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    plan = PLAN_BY_ID.get(payload.plan_id)
    if not plan:
        raise HTTPException(status_code=400, detail="Unknown plan")

    amount_rub = int(plan["price_rub"])
    percent = 0
    if payload.promo_code:
        percent = apply_promo_percent(db, user, payload.promo_code, amount_rub)
    payable = compute_payable(amount_rub, percent)

    result = cryptobot.create_invoice(
        telegram_id=user.telegram_id,
        amount_rub=payable,
        description=f"TrumpVPN — {plan['title']} ({percent}% скидка)" if percent else f"TrumpVPN — {plan['title']}",
    )

    invoice_id = int(result["invoice_id"])
    invoice_hash = hashlib.sha256(f"{invoice_id}:{user.telegram_id}:{payable}".encode()).hexdigest()[:32]
    invoice = PaymentInvoice(
        invoice_id=invoice_id,
        invoice_hash=invoice_hash,
        user_id=user.id,
        amount_rub=amount_rub,
        payable_rub=payable,
        months=int(plan["months"]),
        kind="purchase",
        plan_id=plan["id"],
        promo_code_text=payload.promo_code.strip().upper() if payload.promo_code else None,
        promo_discount_percent=percent,
        pay_url=result["pay_url"],
        status="active",
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)

    return PaymentCreatedOut(
        invoice_id=invoice.invoice_id,
        pay_url=invoice.pay_url,
        amount_rub=invoice.amount_rub,
        payable_rub=invoice.payable_rub,
        status=invoice.status,
    ).model_dump()


@router.get("/status/{invoice_id}")
def payment_status(invoice_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    invoice = db.scalar(
        select(PaymentInvoice).where(
            PaymentInvoice.invoice_id == invoice_id,
            PaymentInvoice.user_id == user.id,
        )
    )
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # If still active, poll CryptoBot and settle on paid.
    if invoice.status == "active":
        try:
            remote = cryptobot.get_invoice(invoice.invoice_id)
            if str(remote.get("status", "")).lower() == "paid":
                _settle_paid(db, invoice, user)
        except Exception:
            pass

    return PaymentStatusOut(invoice_id=invoice.invoice_id, status=invoice.status, paid=invoice.status == "paid").model_dump()


@router.get("/history")
def payment_history(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[dict]:
    rows = db.scalars(
        select(PaymentInvoice)
        .where(PaymentInvoice.user_id == user.id)
        .order_by(PaymentInvoice.created_at.desc())
    ).all()
    return [
        {
            "invoice_id": r.invoice_id,
            "amount_rub": r.amount_rub,
            "payable_rub": r.payable_rub,
            "months": r.months,
            "plan_id": r.plan_id,
            "status": r.status,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "paid_at": r.paid_at.isoformat() if r.paid_at else None,
        }
        for r in rows
    ]


def _settle_paid(db: Session, invoice: PaymentInvoice, user: User) -> None:
    from app.models import utc_now
    invoice.status = "paid"
    invoice.paid_at = utc_now()
    db.flush()
    record_redemption(db, user, invoice.id)
    activate_subscription(db, user, months=invoice.months)
