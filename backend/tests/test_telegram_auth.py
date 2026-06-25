import hashlib
import hmac
import time
from unittest.mock import patch

import pytest

from app.services.telegram_auth import verify_telegram_auth_payload, TelegramAuthError

BOT_TOKEN = "123456:ABC-test-token"


def _make_signed_payload(bot_token: str, fields: dict[str, str]) -> dict:
    data = dict(fields)
    check_parts = [f"{k}={data[k]}" for k in sorted(data.keys())]
    data_check_string = "\n".join(check_parts)
    secret_key = hashlib.sha256(bot_token.encode("utf-8")).digest()
    data["hash"] = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()
    return data


def test_valid_payload_returns_telegram_id():
    fields = {
        "id": "42424242",
        "first_name": "Evgen",
        "username": "evgen",
        "auth_date": str(int(time.time())),
    }
    payload = _make_signed_payload(BOT_TOKEN, fields)
    with patch("app.services.telegram_auth.settings") as s:
        s.tg_bot_token = BOT_TOKEN
        tid, username = verify_telegram_auth_payload(payload)
    assert tid == 42424242
    assert username == "evgen"


def test_bad_signature_raises():
    fields = {"id": "1", "auth_date": str(int(time.time()))}
    payload = _make_signed_payload(BOT_TOKEN, fields)
    payload["hash"] = "0" * 64
    with patch("app.services.telegram_auth.settings") as s:
        s.tg_bot_token = BOT_TOKEN
        with pytest.raises(TelegramAuthError):
            verify_telegram_auth_payload(payload)


def test_expired_payload_raises():
    fields = {"id": "1", "auth_date": str(int(time.time()) - 10 * 86400)}
    payload = _make_signed_payload(BOT_TOKEN, fields)
    with patch("app.services.telegram_auth.settings") as s:
        s.tg_bot_token = BOT_TOKEN
        with pytest.raises(TelegramAuthError):
            verify_telegram_auth_payload(payload)
