from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Response

from app.config import settings


def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_session_token(telegram_id: int) -> str:
    payload = {
        "sub": str(telegram_id),
        "iat": int(_now().timestamp()),
        "exp": int((_now() + timedelta(seconds=settings.session_ttl_seconds)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_session_token(token: str) -> int | None:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError:
        return None
    try:
        return int(payload.get("sub") or 0)
    except (TypeError, ValueError):
        return None


def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        max_age=settings.session_ttl_seconds,
        httponly=True,
        samesite="lax",
        secure=False,  # set True behind HTTPS in prod
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(settings.session_cookie_name, path="/")
