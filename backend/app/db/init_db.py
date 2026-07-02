from sqlalchemy import select

from app.db.base import SessionLocal
from app.models import PromoCode, VpnServer

# 4 production servers. All VLESS + Reality. Real connection params
# (host/public_key/short_id/ssh_*) are filled when the user provisions the
# servers; they stay empty here until provided. Country order on the landing.
_SEED_SERVERS = [
    {"name": "Нидерланды", "country_code": "NL", "protocol": "vless_reality",
     "host": "nl.example.com", "port": 443, "sni": "www.cloudflare.com",
     "public_key": "", "short_id": "", "ssh_host": "nl.example.com", "sort_order": 0},
    {"name": "Польша", "country_code": "PL", "protocol": "vless_reality",
     "host": "pl.example.com", "port": 443, "sni": "www.cloudflare.com",
     "public_key": "", "short_id": "", "ssh_host": "pl.example.com", "sort_order": 1},
    {"name": "Финляндия", "country_code": "FI", "protocol": "vless_reality",
     "host": "fi.example.com", "port": 443, "sni": "www.cloudflare.com",
     "public_key": "", "short_id": "", "ssh_host": "fi.example.com", "sort_order": 2},
    {"name": "Германия", "country_code": "DE", "protocol": "vless_reality",
     "host": "de.example.com", "port": 443, "sni": "www.cloudflare.com",
     "public_key": "", "short_id": "", "ssh_host": "de.example.com", "sort_order": 3},
]


def seed_dev() -> None:
    """Idempotent seed. Also re-seeds the server list if it changed
    (wipes placeholder rows and inserts the current _SEED_SERVERS)."""
    with SessionLocal() as db:
        existing_names = {r[0] for r in db.execute(select(VpnServer.name)).all()}

        # If the DB has stale placeholder servers (e.g. old "US — США"),
        # wipe and reseed so the country list matches reality.
        desired_names = {s["name"] for s in _SEED_SERVERS}
        if existing_names and not existing_names.issubset(desired_names):
            db.query(VpnServer).delete()
            db.commit()
            existing_names = set()

        for s in _SEED_SERVERS:
            if s["name"] not in existing_names:
                db.add(VpnServer(**s))

        if not db.scalar(select(PromoCode).where(PromoCode.code == "WELCOME10")):
            db.add(PromoCode(code="WELCOME10", kind="discount_percent", value_int=10, enabled=True))
        db.commit()
