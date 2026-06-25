from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.config import settings
from app.db.base import get_db
from app.models import User
from app.security import decode_session_token


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get(settings.session_cookie_name) or ""
    telegram_id = decode_session_token(token) if token else None
    if not telegram_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if user.is_blocked:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account blocked")
    return user
