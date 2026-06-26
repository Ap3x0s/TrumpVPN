from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.models import User
from app.services.subscription import subscription_payload_b64

router = APIRouter(tags=["subscription"])


@router.get("/sub/{telegram_id}/{token}", response_class=PlainTextResponse)
def subscription(telegram_id: int, token: str, db: Session = Depends(get_db)) -> str:
    user = db.scalar(select(User).where(User.telegram_id == telegram_id))
    if not user or not user.subscription_token:
        raise HTTPException(status_code=404, detail="Not found")
    if user.subscription_token.token != token:
        raise HTTPException(status_code=404, detail="Not found")
    return subscription_payload_b64(user)


@router.get("/sub/{telegram_id}/{token}/preview", response_class=PlainTextResponse)
def subscription_preview(telegram_id: int, token: str, db: Session = Depends(get_db)) -> str:
    user = db.scalar(select(User).where(User.telegram_id == telegram_id))
    if not user or not user.subscription_token or user.subscription_token.token != token:
        raise HTTPException(status_code=404, detail="Not found")
    urls = [c.connection_url for c in user.configs if c.is_active]
    return "<html><body><pre>" + "\n".join(urls) + "</pre></body></html>"
