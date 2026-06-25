import hashlib
import hmac
import time
from typing import Any

from app.config import settings


class TelegramAuthError(Exception):
    """Raised when a Telegram Login Widget payload is invalid."""


def verify_telegram_auth_payload(payload: dict[str, Any], bot_token: str = "") -> tuple[int, str | None]:
    """Verify a Telegram Login Widget callback payload.

    Ported from _verify_telegram_auth_payload (onefile_vpn.py). Raises TelegramAuthError on failure.
    Returns (telegram_id, username|None).
    """
    token = (bot_token or settings.tg_bot_token or "").strip()
    if not token:
        raise TelegramAuthError("Telegram auth is not configured")

    data = {k: v for k, v in payload.items() if v is not None}
    auth_date = int(data.get("auth_date") or 0)
    now_ts = int(time.time())
    if auth_date <= 0 or auth_date < now_ts - 86400 or auth_date > now_ts + 600:
        raise TelegramAuthError("Telegram auth expired")

    provided_hash = str(data.pop("hash", "") or "").strip().lower()
    if not provided_hash:
        raise TelegramAuthError("Invalid Telegram auth payload")

    check_parts = [f"{key}={data[key]}" for key in sorted(data.keys())]
    data_check_string = "\n".join(check_parts)
    secret_key = hashlib.sha256(token.encode("utf-8")).digest()
    expected_hash = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected_hash, provided_hash):
        raise TelegramAuthError("Telegram auth signature mismatch")

    telegram_id = int(data.get("id") or 0)
    if telegram_id <= 0:
        raise TelegramAuthError("Invalid Telegram user")
    username = str(data.get("username") or "").strip() or None
    return telegram_id, username
