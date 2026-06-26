from sqlalchemy import select

from app.db.base import SessionLocal
from app.models import PromoCode, VpnServer

# 4 placeholder servers. Real configs (host/public_key/ssh_key) supplied by user later.
_SEED_SERVERS = [
    {"name": "DE — Германия", "protocol": "vless_reality", "host": "de.example.com", "port": 443,
     "sni": "www.cloudflare.com", "public_key": "", "short_id": "", "ssh_host": "de.example.com", "sort_order": 0},
    {"name": "NL — Нидерланды", "protocol": "vless_reality", "host": "nl.example.com", "port": 443,
     "sni": "www.cloudflare.com", "public_key": "", "short_id": "", "ssh_host": "nl.example.com", "sort_order": 1},
    {"name": "FI — Финляндия", "protocol": "hysteria2", "host": "fi.example.com", "port": 443,
     "sni": "www.cloudflare.com", "ssh_host": "fi.example.com", "sort_order": 2},
    {"name": "US — США", "protocol": "vless_reality", "host": "us.example.com", "port": 443,
     "sni": "www.cloudflare.com", "public_key": "", "short_id": "", "ssh_host": "us.example.com", "sort_order": 3},
]


def seed_dev() -> None:
    with SessionLocal() as db:
        for s in _SEED_SERVERS:
            exists = db.scalar(select(VpnServer).where(VpnServer.name == s["name"]))
            if not exists:
                db.add(VpnServer(**s))
        if not db.scalar(select(PromoCode).where(PromoCode.code == "WELCOME10")):
            db.add(PromoCode(code="WELCOME10", kind="discount_percent", value_int=10, enabled=True))
        db.commit()
