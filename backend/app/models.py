from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utc_now() -> datetime:
    from datetime import timezone
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    subscription_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    balance_rub: Mapped[int] = mapped_column(Integer, default=0)
    pending_discount_promo_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)

    configs: Mapped[list["ClientConfig"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    payments: Mapped[list["PaymentInvoice"]] = relationship(back_populates="user")
    subscription_token: Mapped["SubscriptionToken | None"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")


class VpnServer(Base):
    __tablename__ = "vpn_servers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    protocol: Mapped[str] = mapped_column(String(32), default="vless_reality", index=True)
    host: Mapped[str] = mapped_column(String(255))
    port: Mapped[int] = mapped_column(Integer, default=443)
    sni: Mapped[str] = mapped_column(String(255), default="www.cloudflare.com")
    public_key: Mapped[str] = mapped_column(String(255), default="")
    short_id: Mapped[str] = mapped_column(String(32), default="")
    fingerprint: Mapped[str] = mapped_column(String(32), default="chrome")
    hy2_obfs: Mapped[str | None] = mapped_column(String(32), nullable=True)
    hy2_obfs_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    hy2_alpn: Mapped[str] = mapped_column(String(64), default="h3")
    hy2_insecure: Mapped[bool] = mapped_column(Boolean, default=False)
    ssh_host: Mapped[str] = mapped_column(String(255))
    ssh_port: Mapped[int] = mapped_column(Integer, default=22)
    ssh_user: Mapped[str] = mapped_column(String(64), default="root")
    ssh_key_path: Mapped[str] = mapped_column(String(500), default="")
    remote_add_script: Mapped[str] = mapped_column(String(500), default="/opt/vpn/add_vless_user.sh")
    remote_remove_script: Mapped[str] = mapped_column(String(500), default="/opt/vpn/remove_vless_user.sh")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    configs: Mapped[list["ClientConfig"]] = relationship(back_populates="server")


class ClientConfig(Base):
    __tablename__ = "client_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    server_id: Mapped[int] = mapped_column(ForeignKey("vpn_servers.id"), index=True)
    client_uuid: Mapped[str] = mapped_column(String(36), index=True)  # vless uuid
    client_secret: Mapped[str] = mapped_column(String(255), default="")  # hy2 password
    email_tag: Mapped[str] = mapped_column(String(128), default="")
    connection_url: Mapped[str] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user: Mapped[User] = relationship(back_populates="configs")
    server: Mapped[VpnServer] = relationship(back_populates="configs")


class SubscriptionToken(Base):
    __tablename__ = "subscription_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    token: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    user: Mapped[User] = relationship(back_populates="subscription_token")


class PaymentInvoice(Base):
    __tablename__ = "payment_invoices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    invoice_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    invoice_hash: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    amount_rub: Mapped[int] = mapped_column(Integer)
    payable_rub: Mapped[int] = mapped_column(Integer, default=0)
    months: Mapped[int] = mapped_column(Integer, default=1)
    kind: Mapped[str] = mapped_column(String(32), default="purchase")
    plan_id: Mapped[str] = mapped_column(String(16), default="")
    promo_code_text: Mapped[str | None] = mapped_column(String(64), nullable=True)
    promo_discount_percent: Mapped[int] = mapped_column(Integer, default=0)
    pay_url: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="active", index=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user: Mapped[User] = relationship(back_populates="payments")


class PromoCode(Base):
    __tablename__ = "promo_codes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    kind: Mapped[str] = mapped_column(String(32), index=True, default="discount_percent")
    value_int: Mapped[int] = mapped_column(Integer, default=0)  # percent 1..95
    max_uses_total: Mapped[int] = mapped_column(Integer, default=0)  # 0 = unlimited
    max_uses_per_user: Mapped[int] = mapped_column(Integer, default=1)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class PromoRedemption(Base):
    __tablename__ = "promo_redemptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    promo_code_id: Mapped[int] = mapped_column(ForeignKey("promo_codes.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    payment_invoice_id: Mapped[int | None] = mapped_column(ForeignKey("payment_invoices.id"), nullable=True, index=True)
    kind: Mapped[str] = mapped_column(String(32))
    value_int: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, index=True)
