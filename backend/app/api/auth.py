from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db.base import get_db
from app.deps import get_current_user
from app.models import LoginToken, User
from app.schemas import ExchangeTokenRequest, TelegramLoginRequest, UserOut
from app.security import clear_session_cookie, create_session_token, set_session_cookie
from app.services.telegram_auth import TelegramAuthError, verify_telegram_auth_payload

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Magic-link tokens live 10 minutes and are single-use.
LOGIN_TOKEN_TTL = timedelta(minutes=10)

# Shared secret that authorizes the bot to mint login tokens.
# Empty => endpoint disabled.
_BOT_AUTH_HEADER = "X-Bot-Token"


def _get_or_create_user(db: Session, telegram_id: int, username: str | None) -> User:
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        user = User(telegram_id=telegram_id, username=username, balance_rub=0)
        db.add(user)
        db.commit()
        db.refresh(user)
    elif username and user.username != username:
        user.username = username
        db.commit()
    return user


@router.post("/telegram")
def telegram_login(payload: TelegramLoginRequest, response: Response, db: Session = Depends(get_db)) -> dict:
    try:
        telegram_id, username = verify_telegram_auth_payload(payload.model_dump())
    except TelegramAuthError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))
    user = _get_or_create_user(db, telegram_id, username)
    token = create_session_token(telegram_id)
    set_session_cookie(response, token)
    return UserOut.from_user(user).model_dump()


@router.post("/issue-token")
def issue_login_token(request: Request, db: Session = Depends(get_db)) -> dict:
    """Called by the bot when a user sends /start.

    Requires a shared secret (X-Bot-Token header) matching LOGIN_BOT_TOKEN.
    Returns a one-time magic-link token bound to the telegram_id.

    Accepts telegram_id/username as query params so the bot can call it with a
    plain GET-style POST (no JSON body needed).
    """
    expected = getattr(settings, "login_bot_token", "") or ""
    if not expected or request.headers.get(_BOT_AUTH_HEADER, "") != expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    data = request.query_params
    try:
        telegram_id = int(data.get("telegram_id") or 0)
    except (TypeError, ValueError):
        telegram_id = 0
    if telegram_id <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="telegram_id required")
    username = (data.get("username") or "").strip() or None

    # Provisionally create the user so the token always resolves, even on first login.
    _get_or_create_user(db, telegram_id, username)

    import secrets
    from app.models import utc_now
    row = LoginToken(
        token=secrets.token_urlsafe(32),
        telegram_id=telegram_id,
        username=username,
        expires_at=utc_now() + LOGIN_TOKEN_TTL,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"token": row.token, "expires_in": int(LOGIN_TOKEN_TTL.total_seconds())}


@router.post("/exchange")
def exchange_login_token(payload: ExchangeTokenRequest, response: Response, db: Session = Depends(get_db)) -> dict:
    """Website calls this with a magic-link token to obtain a session cookie."""
    from app.models import utc_now
    row = db.scalar(select(LoginToken).where(LoginToken.token == payload.token))
    now = utc_now()
    if not row:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    if row.used_at is not None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token already used")
    if row.expires_at < now:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")

    row.used_at = now
    db.commit()

    user = _get_or_create_user(db, row.telegram_id, row.username)
    session = create_session_token(user.telegram_id)
    set_session_cookie(response, session)
    return UserOut.from_user(user).model_dump()


@router.get("/me")
def me(user: User = Depends(get_current_user)) -> dict:
    return UserOut.from_user(user).model_dump()


@router.post("/logout")
def logout(response: Response) -> dict:
    clear_session_cookie(response)
    return {"status": "ok"}
