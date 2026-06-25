from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas import TelegramLoginRequest, UserOut
from app.security import clear_session_cookie, create_session_token, set_session_cookie
from app.services.telegram_auth import TelegramAuthError, verify_telegram_auth_payload

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/telegram")
def telegram_login(payload: TelegramLoginRequest, response: Response, db: Session = Depends(get_db)) -> dict:
    try:
        telegram_id, username = verify_telegram_auth_payload(payload.model_dump())
    except TelegramAuthError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        user = User(telegram_id=telegram_id, username=username, balance_rub=0)
        db.add(user)
        db.commit()
        db.refresh(user)
    elif username and user.username != username:
        user.username = username
        db.commit()
    token = create_session_token(telegram_id)
    set_session_cookie(response, token)
    return UserOut.from_user(user).model_dump()


@router.get("/me")
def me(user: User = Depends(get_current_user)) -> dict:
    return UserOut.from_user(user).model_dump()


@router.post("/logout")
def logout(response: Response) -> dict:
    clear_session_cookie(response)
    return {"status": "ok"}
