from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas import RedeemPromoRequest, UserOut
from app.services.promo import apply_promo_percent
from app.services.subscription import build_subscription_url

router = APIRouter(prefix="/api/cabinet", tags=["cabinet"])


@router.get("/me")
def cabinet_me(user: User = Depends(get_current_user)) -> dict:
    return UserOut.from_user(user).model_dump()


@router.get("/keys")
def cabinet_keys(user: User = Depends(get_current_user)) -> dict:
    if not user.subscription_token:
        return {"active": False, "subscription_url": None, "subscription_until": None, "configs": []}
    configs = [
        {"server": c.server.name, "protocol": c.server.protocol, "url": c.connection_url, "active": c.is_active}
        for c in sorted(user.configs, key=lambda x: x.server.sort_order)
    ]
    return {
        "active": user.subscription_until is not None,
        "subscription_url": build_subscription_url(user),
        "subscription_until": user.subscription_until.isoformat() if user.subscription_until else None,
        "configs": configs,
    }


@router.post("/redeem-promo")
def redeem_promo(payload: RedeemPromoRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    # Preview the discount that would apply on next purchase (no purchase yet).
    percent = apply_promo_percent(db, user, payload.code, amount_rub=199)
    if percent == 0:
        raise HTTPException(status_code=400, detail="Промокод недействителен")
    return {"status": "ok", "discount_percent": percent, "message": f"Скидка {percent}% применится к следующей покупке."}
