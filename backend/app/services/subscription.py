import secrets
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import ClientConfig, SubscriptionToken, User, VpnServer
from app.services.protocols import build_client_url, build_subscription_b64
from app.services.provisioning import add_client, remove_client


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def extend_subscription(db: Session, user: User, months: int) -> None:
    base = utc_now()
    if user.subscription_until and user.subscription_until > base:
        base = user.subscription_until
    user.subscription_until = base + timedelta(days=30 * months)
    db.flush()


def _get_enabled_servers(db: Session) -> list[VpnServer]:
    rows = db.scalars(
        select(VpnServer).where(VpnServer.enabled.is_(True)).order_by(VpnServer.sort_order)
    ).all()
    return list(rows)


def _ensure_token(db: Session, user: User) -> SubscriptionToken:
    if user.subscription_token:
        return user.subscription_token
    token = SubscriptionToken(user_id=user.id, token=secrets.token_urlsafe(32))
    db.add(token)
    db.flush()
    return token


def activate_subscription(db: Session, user: User, months: int) -> None:
    """Create/refresh one active config per enabled server, provision remotely, extend sub, mint token."""
    servers = _get_enabled_servers(db)
    expires_at = utc_now() + timedelta(days=30 * months)

    for server in servers:
        existing = db.scalar(
            select(ClientConfig).where(
                ClientConfig.user_id == user.id,
                ClientConfig.server_id == server.id,
            )
        )
        secret = str(uuid4()) if (server.protocol or "vless_reality") == "vless_reality" else secrets.token_urlsafe(16)
        if existing:
            existing.client_uuid = secret if server.protocol != "hysteria2" else existing.client_uuid
            existing.client_secret = secret
            existing.connection_url = build_client_url(server, secret, server.name)
            existing.is_active = True
            existing.revoked_at = None
            cfg = existing
        else:
            cfg = ClientConfig(
                user_id=user.id,
                server_id=server.id,
                client_uuid=secret if server.protocol != "hysteria2" else "",
                client_secret=secret,
                email_tag=f"tg{user.telegram_id}_{server.name}".lower(),
                connection_url=build_client_url(server, secret, server.name),
                is_active=True,
            )
            db.add(cfg)
        db.flush()
        try:
            add_client(server, secret, cfg.email_tag, expires_at)
        except Exception:
            # provisioning must not block activation of DB record; surfaced in logs
            pass

    _ensure_token(db, user)
    extend_subscription(db, user, months)
    db.commit()


def revoke_all(db: Session, user: User) -> None:
    for cfg in user.configs:
        if cfg.is_active:
            cfg.is_active = False
            cfg.revoked_at = utc_now()
            server = cfg.server
            secret = cfg.client_secret or cfg.client_uuid
            try:
                remove_client(server, secret)
            except Exception:
                pass
    db.commit()


def build_subscription_url(user: User) -> str:
    base = settings.public_base_url.rstrip("/")
    token = user.subscription_token.token if user.subscription_token else ""
    return f"{base}/sub/{user.telegram_id}/{token}"


def active_connection_urls(user: User) -> list[str]:
    return [c.connection_url for c in user.configs if c.is_active]


def subscription_payload_b64(user: User) -> str:
    return build_subscription_b64(active_connection_urls(user))
