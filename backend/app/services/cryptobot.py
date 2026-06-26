from typing import Any
from uuid import uuid4

import httpx

from app.config import settings


def _headers() -> dict[str, str]:
    if not settings.crypto_pay_api_token:
        raise RuntimeError("CRYPTO_PAY_API_TOKEN is empty")
    return {"Crypto-Pay-API-Token": settings.crypto_pay_api_token}


def create_invoice(telegram_id: int, amount_rub: int, description: str) -> dict[str, Any]:
    payload_tag = f"tg:{telegram_id}:{uuid4().hex[:12]}"
    body = {
        "currency_type": "fiat",
        "fiat": "RUB",
        "amount": str(int(amount_rub)),
        "description": description,
        "payload": payload_tag,
        "expires_in": max(300, settings.crypto_pay_invoice_expires_in),
        "accepted_assets": settings.crypto_pay_accepted_assets,
        "allow_anonymous": False,
    }
    url = f"{settings.crypto_pay_base_url.rstrip('/')}/createInvoice"
    resp = httpx.post(url, json=body, headers=_headers(), timeout=20.0)
    resp.raise_for_status()
    data = resp.json()
    if not data.get("ok"):
        raise RuntimeError(data.get("error", "CryptoPay createInvoice failed"))
    result = data.get("result", {})
    if not result.get("invoice_id") or not result.get("pay_url"):
        raise RuntimeError("CryptoPay returned incomplete invoice data")
    return result


def get_invoice(invoice_id: int) -> dict[str, Any]:
    url = f"{settings.crypto_pay_base_url.rstrip('/')}/getInvoices"
    resp = httpx.post(url, json={"invoice_ids": str(invoice_id)}, headers=_headers(), timeout=20.0)
    resp.raise_for_status()
    data = resp.json()
    if not data.get("ok"):
        raise RuntimeError(data.get("error", "CryptoPay getInvoices failed"))
    items = data.get("result", {}).get("items", [])
    if not items:
        raise RuntimeError("Invoice not found in CryptoPay")
    return items[0]
