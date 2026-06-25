# TrumpVPN Core Path — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the MVP web app for TrumpVPN — landing → Telegram login → CryptoBot payment → subscription activation → personal cabinet with subscription URL + QR across 4 servers.

**Architecture:** Modular monolith monorepo. `backend/` = FastAPI serving a clean JSON-API (SQLite via SQLAlchemy 2.0). `frontend/` = React 18 + Vite + TS SPA. nginx proxies `/api/*` and `/sub/*` to FastAPI, serves the SPA build otherwise. Telegram-only auth via Login Widget (hash verified server-side). Subscription model: one subscription → one config per server (4 total) → single base64 subscription URL importable into HAPP/Hiddify.

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy 2.0, Pydantic v2, httpx, paramiko, PyJWT, pytest; React 18, Vite 5, TypeScript 5, react-router-dom 6, `qrcode`; SQLite + WAL.

**Domain logic source:** valuable logic is ported (not copied wholesale) from `_reference/onefile_vpn.py` — TG-auth verification, `build_vless_url`/`build_hysteria2_url`, CryptoBot invoice calls, SSH provisioning, subscription base64 assembly. The monolithic file is NOT used at runtime.

---

## File Structure (locked in)

### Backend — `backend/`
```
backend/
├─ pyproject.toml                  # deps + tool config (or requirements.txt)
├─ .env.example
├─ app/
│  ├─ __init__.py
│  ├─ main.py                      # FastAPI app factory, CORS, router include, startup
│  ├─ config.py                    # Settings (pydantic-settings)
│  ├─ db/
│  │  ├─ __init__.py
│  │  ├─ base.py                   # DeclarativeBase, engine, session factory, get_db dep
│  │  └─ init_db.py                # create_all + seed plans/servers (dev)
│  ├─ models.py                    # all SQLAlchemy models (one focused file)
│  ├─ deps.py                      # auth dependencies: get_current_user, require_subscription
│  ├─ security.py                  # JWT encode/decode + cookie helpers
│  ├─ schemas.py                   # Pydantic request/response schemas
│  ├─ plans.py                     # PLAN_CATALOG constant (3 tiers)
│  ├─ services/
│  │  ├─ __init__.py
│  │  ├─ telegram_auth.py          # _verify_telegram_auth_payload (ported)
│  │  ├─ protocols.py              # build_vless_url, build_hysteria2_url, build_subscription_b64
│  │  ├─ cryptobot.py              # create_invoice, get_invoice (ported)
│  │  ├─ promo.py                  # validate + apply promo discount
│  │  ├─ provisioning.py           # run_ssh, add_vless_client, add_hysteria2_client, remove_*
│  │  └─ subscription.py           # activate_subscription (create configs + token + ssh)
│  └─ api/
│     ├─ __init__.py
│     ├─ router.py                 # aggregates all sub-routers
│     ├─ auth.py                   # /api/auth/*
│     ├─ public.py                 # /api/public/config, /api/plans
│     ├─ payments.py               # /api/payments/*
│     ├─ cabinet.py                # /api/cabinet/*
│     └─ subscription.py           # /sub/{telegram_id}/{token}
└─ tests/
   ├─ conftest.py                  # in-memory sqlite fixture
   ├─ test_protocols.py
   ├─ test_telegram_auth.py
   ├─ test_promo.py
   ├─ test_subscription_service.py
   └─ test_api_*.py
```

### Frontend — `frontend/`
```
frontend/
├─ package.json
├─ vite.config.ts                  # proxy /api + /sub to :8000 in dev
├─ index.html
└─ src/
   ├─ main.tsx
   ├─ App.tsx                      # routes
   ├─ styles.css                   # design system: aurora bg, glass tokens
   ├─ lib/
   │  ├─ api.ts                    # fetch wrapper, credentials:'include'
   │  ├─ routes.ts                 # route path constants
   │  └─ telegram.ts               # Login Widget init helper
   ├─ components/
   │  ├─ GlassCard.tsx, Button.tsx, Spinner.tsx, FAQ.tsx, Logo.tsx, ProtectedRoute.tsx
   └─ pages/
      ├─ Landing.tsx
      ├─ Login.tsx
      ├─ Checkout.tsx
      ├─ Pay.tsx
      └─ Cabinet.tsx
```

### Deploy — `deploy/`
```
deploy/
├─ nginx.conf                      # TLS, /api + /sub proxy, SPA fallback
└─ trumpvpn.service                # systemd unit
```

---

## Conventions

- **Commit after every task.** Conventional Commits (`feat:`, `chore:`, `test:`, `docs:`).
- **Backend tests** use an in-memory SQLite fixture (override `DATABASE_URL`). Run from `backend/`.
- **Frontend** has no unit tests in this phase; verify by `npm run build` (tsc + vite) and manual smoke.
- The monorepo root is `D:\projects\vibecode\vpnwebsite`. Run backend commands in `backend/`, frontend in `frontend/`.
- All money is stored in **whole rubles** as `int` (consistent with the reference codebase).

---

## Task 1: Backend scaffolding

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/.env.example`
- Create: `backend/app/__init__.py` (empty)
- Create: `backend/app/config.py`
- Create: `backend/app/main.py`

- [ ] **Step 1: Write requirements.txt**

```
fastapi==0.115.0
uvicorn[standard]==0.30.6
sqlalchemy==2.0.35
pydantic==2.9.2
pydantic-settings==2.5.2
httpx==0.27.2
paramiko==3.4.1
PyJWT==2.9.0
python-dotenv==1.0.1
pytest==8.3.3
```

- [ ] **Step 2: Write .env.example**

```env
# Telegram
TG_BOT_TOKEN=123456:ABC-your-bot-token
TG_BOT_USERNAME=yourbotname
PUBLIC_BASE_URL=http://localhost:8000

# CryptoBot
CRYPTO_PAY_API_TOKEN=12345:AAA
CRYPTO_PAY_BASE_URL=https://pay.crypt.bot/api

# Security
JWT_SECRET=change-me-to-a-long-random-string
SESSION_COOKIE_NAME=trumpvpn_session

# Database
DATABASE_URL=sqlite:///./trumpvpn.db
```

- [ ] **Step 3: Write app/config.py**

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    tg_bot_token: str = ""
    tg_bot_username: str = ""
    public_base_url: str = "http://localhost:8000"

    crypto_pay_api_token: str = ""
    crypto_pay_base_url: str = "https://pay.crypt.bot/api"
    crypto_pay_invoice_expires_in: int = 86400
    crypto_pay_accepted_assets: str = "USDT,TON,BTC,ETH,LTC,BNB,TRX,USDC"

    jwt_secret: str = "change-me"
    session_cookie_name: str = "trumpvpn_session"
    session_ttl_seconds: int = 7 * 24 * 3600

    database_url: str = "sqlite:///./trumpvpn.db"

    @property
    def accepted_assets_list(self) -> list[str]:
        return [a.strip() for a in self.crypto_pay_accepted_assets.split(",") if a.strip()]


settings = Settings()
```

- [ ] **Step 4: Write app/main.py**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="TrumpVPN", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
```

- [ ] **Step 5: Install deps and smoke-run**

Run:
```bash
cd backend && python -m venv .venv && . .venv/Scripts/activate && pip install -r requirements.txt
```
Then verify import:
```bash
python -c "from app.main import app; print(app.title)"
```
Expected: `TrumpVPN`

- [ ] **Step 6: Commit**

```bash
git add backend/
git commit -m "feat(backend): scaffold FastAPI app with config and health"
```

---

## Task 2: Database layer + models

**Files:**
- Create: `backend/app/db/__init__.py` (empty)
- Create: `backend/app/db/base.py`
- Create: `backend/app/models.py`
- Create: `backend/app/plans.py`

- [ ] **Step 1: Write app/db/base.py**

```python
from collections.abc import Iterator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    pass


def _make_engine():
    connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
    engine = create_engine(settings.database_url, connect_args=connect_args, future=True)
    if settings.database_url.startswith("sqlite"):
        @event.listens_for(engine, "connect")
        def _enable_wal(dbapi_conn, _):  # noqa: ANN001
            try:
                cur = dbapi_conn.cursor()
                cur.execute("PRAGMA journal_mode=WAL")
                cur.execute("PRAGMA foreign_keys=ON")
                cur.close()
            except Exception:
                pass
    return engine


engine = _make_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from app import models  # noqa: F401  (register tables)
    Base.metadata.create_all(bind=engine)
```

- [ ] **Step 2: Write app/models.py**

```python
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
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
```

- [ ] **Step 3: Write app/plans.py**

```python
PLANS = [
    {"id": "p1m", "title": "1 месяц", "months": 1, "price_rub": 199, "discount_percent": 0},
    {"id": "p3m", "title": "3 месяца", "months": 3, "price_rub": 499, "discount_percent": 16},
    {"id": "p1y", "title": "1 год", "months": 12, "price_rub": 1490, "discount_percent": 38},
]

PLAN_BY_ID = {p["id"]: p for p in PLANS}
```

- [ ] **Step 4: Verify models create tables**

Run:
```bash
cd backend && . .venv/Scripts/activate && python -c "from app.db.base import init_db; init_db(); print('ok')"
```
Expected: `ok`

- [ ] **Step 5: Commit**

```bash
git add backend/app/db backend/app/models.py backend/app/plans.py
git commit -m "feat(backend): add db layer, models, plan catalog"
```

---

## Task 3: Test harness (conftest)

**Files:**
- Create: `backend/tests/__init__.py` (empty)
- Create: `backend/tests/conftest.py`

- [ ] **Step 1: Write conftest.py**

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
import app.models  # noqa: F401


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()
```

- [ ] **Step 2: Verify**

Run:
```bash
cd backend && . .venv/Scripts/activate && python -m pytest tests/ -q
```
Expected: `no tests ran` (collects OK, no errors)

- [ ] **Step 3: Commit**

```bash
git add backend/tests/
git commit -m "test(backend): add in-memory sqlite test fixture"
```

---

## Task 4: Protocols service (build URLs + subscription base64) — TDD

**Files:**
- Test: `backend/tests/test_protocols.py`
- Create: `backend/app/services/__init__.py` (empty)
- Create: `backend/app/services/protocols.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_protocols.py
from app.models import VpnServer
from app.services.protocols import build_vless_url, build_hysteria2_url, build_subscription_b64


def make_server(**kw):
    base = dict(
        name="DE", protocol="vless_reality", host="1.2.3.4", port=443,
        sni="www.cloudflare.com", public_key="PBK", short_id="ab12cd34",
        fingerprint="chrome", hy2_alpn="h3", hy2_insecure=False,
        ssh_host="1.2.3.4",
    )
    base.update(kw)
    return VpnServer(**base)


def test_build_vless_url_shape():
    url = build_vless_url(make_server(), "11111111-1111-1111-1111-111111111111", "DE")
    assert url.startswith("vless://11111111-1111-1111-1111-111111111111@1.2.3.4:443?")
    assert "security=reality" in url
    assert "pbk=PBK" in url
    assert "sid=ab12cd34" in url
    assert url.endswith("#DE")


def test_build_hysteria2_url_shape():
    url = build_hysteria2_url(make_server(protocol="hysteria2"), "s3cr3t", "DE")
    assert url.startswith("hy2://s3cr3t@1.2.3.4:443?")
    assert "sni=www.cloudflare.com" in url
    assert "alpn=h3" in url


def test_subscription_b64_roundtrip():
    import base64
    payload = build_subscription_b64(["vless://a@h:443#A", "hy2://b@h:443#B"])
    decoded = base64.b64decode(payload).decode("utf-8")
    assert decoded == "vless://a@h:443#A\nhy2://b@h:443#B"
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_protocols.py -q`
Expected: FAIL (module not found)

- [ ] **Step 3: Write app/services/protocols.py**

```python
import base64
from urllib.parse import quote

PROTOCOL_VLESS_REALITY = "vless_reality"
PROTOCOL_HYSTERIA2 = "hysteria2"


def server_protocol(server) -> str:
    value = str(getattr(server, "protocol", "") or "").strip().lower()
    return value if value in {PROTOCOL_VLESS_REALITY, PROTOCOL_HYSTERIA2} else PROTOCOL_VLESS_REALITY


def build_vless_url(server, client_uuid: str, label: str) -> str:
    params = (
        "encryption=none"
        "&security=reality"
        f"&sni={quote(server.sni, safe='')}"
        f"&fp={quote(server.fingerprint, safe='')}"
        f"&pbk={quote(server.public_key, safe='')}"
        f"&sid={quote(server.short_id, safe='')}"
        "&type=tcp"
        "&flow=xtls-rprx-vision"
    )
    return f"vless://{client_uuid}@{server.host}:{server.port}?{params}#{quote(label, safe='')}"


def build_hysteria2_url(server, password: str, label: str) -> str:
    params: list[str] = []
    sni = str(getattr(server, "sni", "") or "").strip()
    if sni:
        params.append(f"sni={quote(sni, safe='')}")
    alpn = str(getattr(server, "hy2_alpn", "h3") or "h3").strip()
    if alpn:
        params.append(f"alpn={quote(alpn, safe=',')}")
    if bool(getattr(server, "hy2_insecure", False)):
        params.append("insecure=1")
    obfs = str(getattr(server, "hy2_obfs", "") or "").strip()
    if obfs:
        params.append(f"obfs={quote(obfs, safe='')}")
        obfs_password = str(getattr(server, "hy2_obfs_password", "") or "").strip()
        if obfs_password:
            params.append(f"obfs-password={quote(obfs_password, safe='')}")
    query = f"?{'&'.join(params)}" if params else ""
    auth = quote(str(password or ""), safe="")
    return f"hy2://{auth}@{server.host}:{int(server.port)}{query}#{quote(label, safe='')}"


def build_client_url(server, client_secret: str, label: str) -> str:
    if server_protocol(server) == PROTOCOL_HYSTERIA2:
        return build_hysteria2_url(server, client_secret, label)
    return build_vless_url(server, client_secret, label)


def build_subscription_b64(urls: list[str]) -> str:
    payload = "\n".join(urls).encode("utf-8")
    return base64.b64encode(payload).decode("utf-8")
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/test_protocols.py -q`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/__init__.py backend/app/services/protocols.py backend/tests/test_protocols.py
git commit -m "feat(backend): protocol url builders and subscription base64"
```

---

## Task 5: Telegram auth verification — TDD

**Files:**
- Test: `backend/tests/test_telegram_auth.py`
- Create: `backend/app/services/telegram_auth.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_telegram_auth.py
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
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_telegram_auth.py -q`
Expected: FAIL (module not found)

- [ ] **Step 3: Write app/services/telegram_auth.py**

```python
import hashlib
import hmac
import time
from typing import Any


class TelegramAuthError(Exception):
    """Raised when a Telegram Login Widget payload is invalid."""


def verify_telegram_auth_payload(payload: dict[str, Any], bot_token: str = "") -> tuple[int, str | None]:
    """Verify a Telegram Login Widget callback payload.

    Ported from _verify_telegram_auth_payload (onefile_vpn.py). Raises TelegramAuthError on failure.
    Returns (telegram_id, username|None).
    """
    from app.config import settings
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
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/test_telegram_auth.py -q`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/telegram_auth.py backend/tests/test_telegram_auth.py
git commit -m "feat(backend): telegram login widget auth verification"
```

---

## Task 6: JWT session + cookie helpers + auth deps

**Files:**
- Create: `backend/app/security.py`
- Create: `backend/app/deps.py`

- [ ] **Step 1: Write app/security.py**

```python
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
```

- [ ] **Step 2: Write app/deps.py**

```python
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.config import settings
from app.db.base import get_db
from app.models import User
from app.security import decode_session_token


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get(settings.session_cookie_name) or ""
    telegram_id = decode_session_token(token) if token else None
    if not telegram_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if user.is_blocked:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account blocked")
    return user
```

- [ ] **Step 3: Smoke import**

Run:
```bash
cd backend && . .venv/Scripts/activate && python -c "from app.deps import get_current_user; from app.security import create_session_token, decode_session_token; t=create_session_token(123); print(decode_session_token(t))"
```
Expected: `123`

- [ ] **Step 4: Commit**

```bash
git add backend/app/security.py backend/app/deps.py
git commit -m "feat(backend): JWT session cookie and current-user dependency"
```

---

## Task 7: CryptoBot service

**Files:**
- Create: `backend/app/services/cryptobot.py`

- [ ] **Step 1: Write app/services/cryptobot.py**

```python
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
```

- [ ] **Step 2: Smoke import (no network call)**

Run:
```bash
cd backend && . .venv/Scripts/activate && python -c "from app.services.cryptobot import create_invoice, get_invoice; print('ok')"
```
Expected: `ok`

- [ ] **Step 3: Commit**

```bash
git add backend/app/services/cryptobot.py
git commit -m "feat(backend): cryptobot invoice client"
```

---

## Task 8: Promo service — TDD

**Files:**
- Test: `backend/tests/test_promo.py`
- Create: `backend/app/services/promo.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_promo.py
from datetime import datetime, timedelta, timezone

from app.models import PromoCode, User
from app.services.promo import apply_promo_percent


def _now():
    return datetime.now(timezone.utc)


def make_user(db_session, tid=100):
    u = User(telegram_id=tid)
    db_session.add(u)
    db_session.flush()
    return u


def test_valid_discount(db_session):
    p = PromoCode(code="WELCOME10", kind="discount_percent", value_int=10, enabled=True)
    db_session.add(p)
    db_session.flush()
    user = make_user(db_session)
    pct = apply_promo_percent(db_session, user, "welcome10", amount_rub=199)
    assert pct == 10
    assert user.pending_discount_promo_id == p.id


def test_expired_promo_rejected(db_session):
    p = PromoCode(code="OLD", kind="discount_percent", value_int=20, enabled=True,
                  ends_at=_now() - timedelta(days=1))
    db_session.add(p)
    db_session.flush()
    user = make_user(db_session)
    pct = apply_promo_percent(db_session, user, "OLD", amount_rub=199)
    assert pct == 0  # invalid -> no discount
```

> Note: `User.pending_discount_promo_id` is referenced — add it to the model if not present. **Update `app/models.py` `User` to include:**
> ```python
>     pending_discount_promo_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
> ```
> (Add this field in the User model before running tests.)

- [ ] **Step 2: Add pending_discount_promo_id to User model**

Edit `backend/app/models.py`, add inside the `User` class (after `balance_rub`):
```python
    pending_discount_promo_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
```

- [ ] **Step 3: Run to verify failure**

Run: `python -m pytest tests/test_promo.py -q`
Expected: FAIL (module not found)

- [ ] **Step 4: Write app/services/promo.py**

```python
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import PromoCode, PromoRedemption, User


class PromoError(Exception):
    pass


def _normalize(code: str) -> str:
    return (code or "").strip().upper()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def compute_payable(amount_rub: int, percent: int) -> int:
    pct = max(0, min(95, int(percent or 0)))
    return max(1, round(amount_rub * (100 - pct) / 100)) if amount_rub > 0 else 0


def _validation_error(db: Session, promo: PromoCode, user: User) -> str | None:
    if not promo.enabled:
        return "Promo code is disabled"
    now = _now()
    if promo.starts_at and now < promo.starts_at:
        return "Promo is not active yet"
    if promo.ends_at and now > promo.ends_at:
        return "Promo has expired"
    if promo.max_uses_per_user > 0:
        used = db.scalar(
            select(PromoRedemption)
            .where(PromoRedemption.promo_code_id == promo.id, PromoRedemption.user_id == user.id)
        )
        if used:
            return "Promo already used"
    if promo.max_uses_total > 0:
        total = db.scalar(
            select(PromoRedemption).where(PromoRedemption.promo_code_id == promo.id)
        )
        if total:
            return "Promo usage limit reached"
    return None


def apply_promo_percent(db: Session, user: User, code_raw: str, amount_rub: int) -> int:
    """Attach a discount promo to the user (pending). Returns percent 1..95, or 0 if invalid."""
    code = _normalize(code_raw)
    if len(code) < 2:
        return 0
    promo = db.scalar(select(PromoCode).where(PromoCode.code == code))
    if not promo or promo.kind != "discount_percent":
        return 0
    if _validation_error(db, promo, user):
        return 0
    percent = max(1, min(95, int(promo.value_int or 0)))
    user.pending_discount_promo_id = promo.id
    db.flush()
    return percent


def record_redemption(db: Session, user: User, payment_invoice_id: int) -> None:
    """Called after a successful payment to record the redemption for the applied promo."""
    if not user.pending_discount_promo_id:
        return
    promo = db.get(PromoCode, user.pending_discount_promo_id)
    if not promo:
        return
    db.add(PromoRedemption(
        promo_code_id=promo.id,
        user_id=user.id,
        payment_invoice_id=payment_invoice_id,
        kind=promo.kind,
        value_int=int(promo.value_int or 0),
    ))
    user.pending_discount_promo_id = None
    db.flush()
```

- [ ] **Step 5: Run to verify pass**

Run: `python -m pytest tests/test_promo.py -q`
Expected: PASS (2 passed)

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/promo.py backend/tests/test_promo.py backend/app/models.py
git commit -m "feat(backend): promo discount service with validation"
```

---

## Task 9: SSH provisioning service

**Files:**
- Create: `backend/app/services/provisioning.py`

- [ ] **Step 1: Write app/services/provisioning.py**

```python
import shlex
from datetime import datetime

import paramiko

from app.models import VpnServer


class ProvisioningError(Exception):
    pass


def _run_ssh(server: VpnServer, command: str, timeout: float = 20.0) -> str:
    if not server.ssh_key_path:
        raise ProvisioningError("Server SSH key not configured")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(
            hostname=server.ssh_host,
            port=server.ssh_port,
            username=server.ssh_user,
            key_filename=server.ssh_key_path or None,
            timeout=timeout,
            banner_timeout=timeout,
            auth_timeout=timeout,
            look_for_keys=False,
            allow_agent=False,
        )
        _stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
        exit_code = stdout.channel.recv_exit_status()
        out = stdout.read().decode("utf-8", errors="ignore").strip()
        err = stderr.read().decode("utf-8", errors="ignore").strip()
        if exit_code != 0:
            raise ProvisioningError(f"SSH command failed: {err or out or f'code {exit_code}'}")
        return out
    except ProvisioningError:
        raise
    except Exception as exc:
        raise ProvisioningError(str(exc)) from exc
    finally:
        client.close()


def _expiry_arg(expires_at: datetime | None) -> str:
    if not expires_at:
        return ""
    return f" --expiry {shlex.quote(expires_at.strftime('%Y-%m-%dT%H:%M:%SZ'))}"


def add_client(server: VpnServer, secret: str, email_tag: str, expires_at: datetime | None) -> None:
    """Provision one client on the server. secret=uuid(vless) or password(hy2)."""
    if (server.protocol or "").strip().lower() == "hysteria2":
        cmd = (
            f"sudo {shlex.quote(server.remote_add_script)} "
            f"--password {shlex.quote(secret)} "
            f"--name {shlex.quote(email_tag)}"
            f"{_expiry_arg(expires_at)}"
        )
    else:
        cmd = (
            f"sudo {shlex.quote(server.remote_add_script)} "
            f"--uuid {shlex.quote(secret)} "
            f"--email {shlex.quote(email_tag)}"
            f"{_expiry_arg(expires_at)}"
        )
    _run_ssh(server, cmd, timeout=20.0)


def remove_client(server: VpnServer, secret: str) -> None:
    flag = "--password" if (server.protocol or "").strip().lower() == "hysteria2" else "--uuid"
    cmd = (
        f"sudo {shlex.quote(server.remote_remove_script)} "
        f"{flag} {shlex.quote(secret)} || true"
    )
    try:
        _run_ssh(server, cmd, timeout=90.0)
    except ProvisioningError:
        # best-effort removal; idempotent
        pass
```

> **Dev note:** SSH calls are only exercised against real servers. In dev/tests these functions are mocked at the subscription-service layer (Task 10). The 4 real server configs (host/keys) are supplied by the user later via `deploy` seeding or admin (out of scope).

- [ ] **Step 2: Smoke import**

Run:
```bash
cd backend && . .venv/Scripts/activate && python -c "from app.services.provisioning import add_client, remove_client; print('ok')"
```
Expected: `ok`

- [ ] **Step 3: Commit**

```bash
git add backend/app/services/provisioning.py
git commit -m "feat(backend): ssh provisioning for vless/hysteria2 clients"
```

---

## Task 10: Subscription activation service — TDD

**Files:**
- Test: `backend/tests/test_subscription_service.py`
- Create: `backend/app/services/subscription.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_subscription_service.py
from datetime import timedelta
from unittest.mock import patch

from app.models import User, VpnServer
from app.services.subscription import activate_subscription, extend_subscription, build_subscription_url


def _servers(db_session):
    s1 = VpnServer(name="DE", protocol="vless_reality", host="1.1.1.1", port=443, sni="s", public_key="pk", short_id="sid", ssh_host="1.1.1.1", sort_order=0)
    s2 = VpnServer(name="NL", protocol="hysteria2", host="2.2.2.2", port=443, sni="s", ssh_host="2.2.2.2", sort_order=1)
    db_session.add_all([s1, s2])
    db_session.flush()
    return [s1, s2]


def test_activate_creates_one_config_per_server(db_session):
    user = User(telegram_id=1)
    db_session.add(user)
    db_session.flush()
    servers = _servers(db_session)
    with patch("app.services.subscription.add_client") as add_mock, \
         patch("app.services.subscription._get_enabled_servers", return_value=servers):
        activate_subscription(db_session, user, months=1)
    add_mock.assert_called()  # provisioned on both servers
    assert len(user.configs) == 2
    assert all(c.is_active for c in user.configs)
    assert user.subscription_token is not None
    # connection urls are correct protocol per server
    urls = sorted(c.connection_url.split("://")[0] for c in user.configs)
    assert urls == ["hy2", "vless"]


def test_extend_adds_days_from_now(db_session):
    from app.models import User
    from app.services.subscription import extend_subscription
    from app.db.base import Base  # noqa
    user = User(telegram_id=2)
    db_session.add(user)
    db_session.flush()
    extend_subscription(db_session, user, months=3)
    assert user.subscription_until is not None
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_subscription_service.py -q`
Expected: FAIL (module not found)

- [ ] **Step 3: Write app/services/subscription.py**

```python
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
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/test_subscription_service.py -q`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/subscription.py backend/tests/test_subscription_service.py
git commit -m "feat(backend): subscription activation across servers"
```

---

## Task 11: Schemas + auth API

**Files:**
- Create: `backend/app/schemas.py`
- Create: `backend/app/api/__init__.py` (empty)
- Create: `backend/app/api/auth.py`

- [ ] **Step 1: Write app/schemas.py**

```python
from typing import Any

from pydantic import BaseModel, Field


class TelegramLoginRequest(BaseModel):
    # accepts the full Login Widget callback fields
    id: int
    auth_date: int
    hash: str
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    photo_url: str | None = None

    model_config = {"extra": "allow"}  # widget may send extra fields


class UserOut(BaseModel):
    telegram_id: int
    username: str | None = None
    subscription_until: str | None = None
    balance_rub: int = 0

    model_config = {"from_attributes": True}

    @classmethod
    def from_user(cls, user: Any) -> "UserOut":
        return cls(
            telegram_id=user.telegram_id,
            username=user.username,
            subscription_until=user.subscription_until.isoformat() if user.subscription_until else None,
            balance_rub=int(user.balance_rub or 0),
        )


class CreatePaymentRequest(BaseModel):
    plan_id: str = Field(min_length=2, max_length=16)
    promo_code: str | None = Field(default=None, max_length=64)


class PaymentCreatedOut(BaseModel):
    invoice_id: int
    pay_url: str
    amount_rub: int
    payable_rub: int
    status: str


class PaymentStatusOut(BaseModel):
    invoice_id: int
    status: str
    paid: bool


class RedeemPromoRequest(BaseModel):
    code: str = Field(min_length=2, max_length=64)
```

- [ ] **Step 2: Write app/api/auth.py**

```python
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
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
```

- [ ] **Step 3: Smoke import**

Run:
```bash
cd backend && . .venv/Scripts/activate && python -c "from app.api.auth import router; print(len(router.routes))"
```
Expected: `3`

- [ ] **Step 4: Commit**

```bash
git add backend/app/schemas.py backend/app/api/__init__.py backend/app/api/auth.py
git commit -m "feat(backend): pydantic schemas and auth api"
```

---

## Task 12: Public + plans API

**Files:**
- Create: `backend/app/api/public.py`

- [ ] **Step 1: Write app/api/public.py**

```python
from fastapi import APIRouter

from app.plans import PLANS

router = APIRouter(tags=["public"])


@router.get("/api/public/config")
def public_config() -> dict:
    return {
        "features": [
            {"icon": "shield", "title": "0 логов", "text": "Мы не храним историю подключений."},
            {"icon": "bolt", "title": "1 Гбит/чел", "text": "Выделенный канал на пользователя."},
            {"icon": "key", "title": "Один ключ", "text": "Все 4 сервера в одной подписке."},
            {"icon": "lock", "title": "Reality + Hy2", "text": "Современные протоколы обхода блокировок."},
        ],
        "metrics": {"servers": 4, "speed": "1 Гбит", "uptime": "99.9%"},
        "faq": [
            {"q": "Как оплатить?", "a": "Криптовалютой (USDT/BTC/TON) через CryptoBot."},
            {"q": "На сколько устройств?", "a": "Без ограничений — один ключ на все ваши устройства."},
            {"q": "Какие приложения?", "a": "HAPP и Hiddify. Импорт подписки в один тап."},
        ],
    }


@router.get("/api/plans")
def plans() -> list[dict]:
    return PLANS
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/api/public.py
git commit -m "feat(backend): public config and plans endpoints"
```

---

## Task 13: Payments API

**Files:**
- Create: `backend/app/api/payments.py`

- [ ] **Step 1: Write app/api/payments.py**

```python
import hashlib
import time

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.deps import get_current_user
from app.models import PaymentInvoice, User
from app.plans import PLAN_BY_ID
from app.schemas import CreatePaymentRequest, PaymentCreatedOut, PaymentStatusOut
from app.services import cryptobot
from app.services.promo import apply_promo_percent, compute_payable, record_redemption
from app.services.subscription import activate_subscription

router = APIRouter(prefix="/api/payments", tags=["payments"])


def _new_invoice_id(db: Session) -> int:
    from sqlalchemy import func
    last = int(db.scalar(select(func.coalesce(func.max(PaymentInvoice.invoice_id), 0))) or 0)
    return max(last + 1, int(time.time()))


@router.post("/create")
def create_payment(payload: CreatePaymentRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    plan = PLAN_BY_ID.get(payload.plan_id)
    if not plan:
        raise HTTPException(status_code=400, detail="Unknown plan")

    amount_rub = int(plan["price_rub"])
    percent = 0
    if payload.promo_code:
        percent = apply_promo_percent(db, user, payload.promo_code, amount_rub)
    payable = compute_payable(amount_rub, percent)

    result = cryptobot.create_invoice(
        telegram_id=user.telegram_id,
        amount_rub=payable,
        description=f"TrumpVPN — {plan['title']} ({percent}% скидка)" if percent else f"TrumpVPN — {plan['title']}",
    )

    invoice_id = int(result["invoice_id"])
    invoice_hash = hashlib.sha256(f"{invoice_id}:{user.telegram_id}:{payable}".encode()).hexdigest()[:32]
    invoice = PaymentInvoice(
        invoice_id=invoice_id,
        invoice_hash=invoice_hash,
        user_id=user.id,
        amount_rub=amount_rub,
        payable_rub=payable,
        months=int(plan["months"]),
        kind="purchase",
        plan_id=plan["id"],
        promo_code_text=payload.promo_code.strip().upper() if payload.promo_code else None,
        promo_discount_percent=percent,
        pay_url=result["pay_url"],
        status="active",
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)

    return PaymentCreatedOut(
        invoice_id=invoice.invoice_id,
        pay_url=invoice.pay_url,
        amount_rub=invoice.amount_rub,
        payable_rub=invoice.payable_rub,
        status=invoice.status,
    ).model_dump()


@router.get("/status/{invoice_id}")
def payment_status(invoice_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    invoice = db.scalar(
        select(PaymentInvoice).where(
            PaymentInvoice.invoice_id == invoice_id,
            PaymentInvoice.user_id == user.id,
        )
    )
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # If still active, poll CryptoBot and settle on paid.
    if invoice.status == "active":
        try:
            remote = cryptobot.get_invoice(invoice.invoice_id)
            if str(remote.get("status", "")).lower() == "paid":
                _settle_paid(db, invoice, user)
        except Exception:
            pass

    return PaymentStatusOut(invoice_id=invoice.invoice_id, status=invoice.status, paid=invoice.status == "paid").model_dump()


@router.get("/history")
def payment_history(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[dict]:
    rows = db.scalars(
        select(PaymentInvoice)
        .where(PaymentInvoice.user_id == user.id)
        .order_by(PaymentInvoice.created_at.desc())
    ).all()
    return [
        {
            "invoice_id": r.invoice_id,
            "amount_rub": r.amount_rub,
            "payable_rub": r.payable_rub,
            "months": r.months,
            "plan_id": r.plan_id,
            "status": r.status,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "paid_at": r.paid_at.isoformat() if r.paid_at else None,
        }
        for r in rows
    ]


def _settle_paid(db: Session, invoice: PaymentInvoice, user: User) -> None:
    from app.models import utc_now
    invoice.status = "paid"
    invoice.paid_at = utc_now()
    db.flush()
    record_redemption(db, user, invoice.id)
    activate_subscription(db, user, months=invoice.months)
```

- [ ] **Step 2: Smoke import**

Run:
```bash
cd backend && . .venv/Scripts/activate && python -c "from app.api.payments import router; print(len(router.routes))"
```
Expected: `3`

- [ ] **Step 3: Commit**

```bash
git add backend/app/api/payments.py
git commit -m "feat(backend): payments create/status/history endpoints"
```

---

## Task 14: Cabinet API

**Files:**
- Create: `backend/app/api/cabinet.py`

- [ ] **Step 1: Write app/api/cabinet.py**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas import RedeemPromoRequest, UserOut
from app.services.promo import apply_promo_percent
from app.services.subscription import build_subscription_url, active_connection_urls

router = APIRouter(prefix="/api/cabinet", tags=["cabinet"])


@router.get("/me")
def cabinet_me(user: User = Depends(get_current_user)) -> dict:
    return UserOut.from_user(user).model_dump()


@router.get("/keys")
def cabinet_keys(user: User = Depends(get_current_user)) -> dict:
    if not user.subscription_token:
        return {"active": False, "subscription_url": None, "configs": [], "subscription_until": None}
    configs = [
        {"server": c.server.name, "protocol": c.server.protocol, "url": c.connection_url, "active": c.is_active}
        for c in sorted(user.configs, key=lambda x: x.server.sort_order)
    ]
    return {
        "active": user.subscription_until is not None,
        "subscription_url": build_subscription_url(user),
        "subscription_until": user.subscription_until.isoformat() if user.subscription_until else None,
        "configs": configs,
    }


@router.post("/redeem-promo")
def redeem_promo(payload: RedeemPromoRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    # Preview the discount that would apply on next purchase (no purchase yet).
    percent = apply_promo_percent(db, user, payload.code, amount_rub=199)
    if percent == 0:
        raise HTTPException(status_code=400, detail="Промокод недействителен")
    return {"status": "ok", "discount_percent": percent, "message": f"Скидка {percent}% применится к следующей покупке."}
```

- [ ] **Step 2: Smoke import**

Run:
```bash
cd backend && . .venv/Scripts/activate && python -c "from app.api.cabinet import router; print(len(router.routes))"
```
Expected: `3`

- [ ] **Step 3: Commit**

```bash
git add backend/app/api/cabinet.py
git commit -m "feat(backend): cabinet me/keys/redeem-promo endpoints"
```

---

## Task 15: Subscription endpoint (/sub) + wire router + startup

**Files:**
- Create: `backend/app/api/subscription.py`
- Create: `backend/app/api/router.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Write app/api/subscription.py**

```python
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.models import SubscriptionToken, User
from app.services.subscription import subscription_payload_b64

router = APIRouter(tags=["subscription"])


@router.get("/sub/{telegram_id}/{token}", response_class=PlainTextResponse)
def subscription(telegram_id: int, token: str, db: Session = Depends(get_db)) -> str:
    user = db.scalar(select(User).where(User.telegram_id == telegram_id))
    if not user or not user.subscription_token:
        raise HTTPException(status_code=404, detail="Not found")
    if user.subscription_token.token != token:
        raise HTTPException(status_code=404, detail="Not found")
    return subscription_payload_b64(user)


@router.get("/sub/{telegram_id}/{token}/preview", response_class=PlainTextResponse)
def subscription_preview(telegram_id: int, token: str, db: Session = Depends(get_db)) -> str:
    user = db.scalar(select(User).where(User.telegram_id == telegram_id))
    if not user or not user.subscription_token or user.subscription_token.token != token:
        raise HTTPException(status_code=404, detail="Not found")
    urls = [c.connection_url for c in user.configs if c.is_active]
    return "<html><body><pre>" + "\n".join(urls) + "</pre></body></html>"
```

- [ ] **Step 2: Write app/api/router.py**

```python
from fastapi import APIRouter

from app.api import auth, cabinet, payments, public, subscription

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(public.router)
api_router.include_router(payments.router)
api_router.include_router(cabinet.router)
api_router.include_router(subscription.router)
```

- [ ] **Step 3: Modify app/main.py — add router + startup init**

Replace the body of `app/main.py` with:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.db.base import init_db

app = FastAPI(title="TrumpVPN", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.on_event("startup")
def _startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
```

- [ ] **Step 4: Run full backend test suite + boot**

Run:
```bash
cd backend && . .venv/Scripts/activate && python -m pytest tests/ -q
```
Expected: all PASS (protocols, telegram_auth, promo, subscription_service)

Then boot once:
```bash
python -c "from app.main import app; from starlette.testclient import TestClient; c=TestClient(app); print(c.get('/health').json(), c.get('/api/plans').json()[0]['id'])"
```
Expected: `{'status': 'ok'} p1m`

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/subscription.py backend/app/api/router.py backend/app/main.py
git commit -m "feat(backend): subscription endpoint, router wiring, startup db init"
```

---

## Task 16: Backend dev seed (4 placeholder servers + a promo)

**Files:**
- Create: `backend/app/db/init_db.py`

- [ ] **Step 1: Write app/db/init_db.py**

```python
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
```

- [ ] **Step 2: Run seed**

Run:
```bash
cd backend && . .venv/Scripts/activate && python -c "from app.db.base import init_db; init_db(); from app.db.init_db import seed_dev; seed_dev(); print('seeded')"
```
Expected: `seeded`

- [ ] **Step 3: Commit**

```bash
git add backend/app/db/init_db.py
git commit -m "feat(backend): dev seed for 4 servers and welcome promo"
```

---

## Task 17: Frontend scaffolding

**Files:**
- Create: `frontend/package.json`, `frontend/vite.config.ts`, `frontend/tsconfig.json`, `frontend/index.html`, `frontend/src/main.tsx`

- [ ] **Step 1: Scaffold with Vite**

Run:
```bash
cd /d/projects/vibecode/vpnwebsite && npm create vite@latest frontend -- --template react-ts
cd frontend && npm install
npm install react-router-dom@6 qrcode
npm install -D @types/qrcode
```

- [ ] **Step 2: Write vite.config.ts (dev proxy)**

```ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": { target: "http://localhost:8000", changeOrigin: true },
      "/sub": { target: "http://localhost:8000", changeOrigin: true },
    },
  },
});
```

- [ ] **Step 3: Write index.html body title**

Edit `frontend/index.html`: set `<title>TrumpVPN — VPN, который просто работает</title>`.

- [ ] **Step 4: Verify build**

Run:
```bash
cd frontend && npm run build
```
Expected: build succeeds (dist/ produced)

- [ ] **Step 5: Commit**

```bash
cd /d/projects/vibecode/vpnwebsite
# make sure node_modules not committed (it's in root .gitignore already)
git add frontend/
git commit -m "feat(frontend): scaffold vite react-ts with api proxy"
```

---

## Task 18: Design system (frosted glass)

**Files:**
- Create: `frontend/src/styles.css`
- Create: `frontend/src/components/GlassCard.tsx`
- Create: `frontend/src/components/Button.tsx`
- Create: `frontend/src/components/Spinner.tsx`
- Create: `frontend/src/components/Logo.tsx`

- [ ] **Step 1: Write src/styles.css**

```css
:root {
  --bg: #08090d;
  --text: #fafafa;
  --muted: #a1a1aa;
  --dim: #71717a;
  --accent-1: #a5b4fc;
  --accent-2: #c4b5fd;
  --accent-3: #7dd3fc;
  --glass-bg: rgba(255, 255, 255, 0.06);
  --glass-border: rgba(255, 255, 255, 0.13);
  --glass-bg-hover: rgba(255, 255, 255, 0.10);
  --radius: 14px;
  --shadow: 0 20px 50px rgba(0, 0, 0, 0.45);
}

* { box-sizing: border-box; margin: 0; padding: 0; }

html, body, #root { height: 100%; }

body {
  font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  background: var(--bg);
  color: var(--text);
  -webkit-font-smoothing: antialiased;
  position: relative;
  overflow-x: hidden;
}

/* aurora background blobs */
body::before {
  content: "";
  position: fixed;
  inset: 0;
  z-index: 0;
  background:
    radial-gradient(circle at 12% 8%, rgba(139,155,255,0.40), transparent 38%),
    radial-gradient(circle at 88% 18%, rgba(167,139,250,0.32), transparent 40%),
    radial-gradient(circle at 50% 95%, rgba(56,189,248,0.22), transparent 45%);
  pointer-events: none;
}

#root { position: relative; z-index: 1; }

.glass {
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-radius: var(--radius);
}

.gradient-text {
  background: linear-gradient(90deg, var(--accent-1), var(--accent-2) 60%, var(--accent-3));
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

.container { width: 100%; max-width: 1080px; margin: 0 auto; padding: 0 24px; }

.muted { color: var(--muted); }
.dim { color: var(--dim); }

button { font-family: inherit; cursor: pointer; }
a { color: inherit; text-decoration: none; }
```

- [ ] **Step 2: Write components**

`src/components/GlassCard.tsx`:
```tsx
import type { ReactNode } from "react";

export function GlassCard({ children, className = "", style }: { children: ReactNode; className?: string; style?: React.CSSProperties }) {
  return <div className={`glass ${className}`} style={{ padding: 24, boxShadow: "var(--shadow)", ...style }}>{children}</div>;
}
```

`src/components/Button.tsx`:
```tsx
import type { ButtonHTMLAttributes, ReactNode } from "react";

type Variant = "primary" | "ghost" | "danger";
const styles: Record<Variant, React.CSSProperties> = {
  primary: { background: "rgba(255,255,255,0.12)", border: "1px solid rgba(255,255,255,0.28)", color: "#fff", backdropFilter: "blur(14px)" },
  ghost: { background: "transparent", border: "1px solid var(--glass-border)", color: "var(--muted)" },
  danger: { background: "rgba(239,68,68,0.15)", border: "1px solid rgba(239,68,68,0.4)", color: "#fca5a5" },
};

export function Button({ variant = "primary", children, style, ...rest }: { variant?: Variant; children: ReactNode } & ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      {...rest}
      style={{ padding: "11px 24px", borderRadius: 11, fontWeight: 600, fontSize: 14, transition: "all .15s ease", ...styles[variant], ...style }}
    >
      {children}
    </button>
  );
}
```

`src/components/Spinner.tsx`:
```tsx
export function Spinner() {
  return (
    <div style={{ width: 28, height: 28, border: "3px solid rgba(255,255,255,0.15)", borderTopColor: "#a5b4fc", borderRadius: "50%", animation: "spin 0.8s linear infinite", margin: "0 auto" }} />
  );
}
```
Add to `styles.css`:
```css
@keyframes spin { to { transform: rotate(360deg); } }
```

`src/components/Logo.tsx` (text placeholder — real logo supplied later):
```tsx
export function Logo() {
  return <span style={{ fontWeight: 700, fontSize: 17, letterSpacing: "-0.3px" }}>trump<span style={{ color: "#a5b4fc" }}>vpn</span></span>;
}
```

- [ ] **Step 3: Verify build**

Run: `cd frontend && npm run build`
Expected: success

- [ ] **Step 4: Commit**

```bash
git add frontend/src/styles.css frontend/src/components/
git commit -m "feat(frontend): frosted glass design system and primitives"
```

---

## Task 19: API client + auth + routes

**Files:**
- Create: `frontend/src/lib/routes.ts`
- Create: `frontend/src/lib/api.ts`
- Create: `frontend/src/lib/telegram.ts`
- Create: `frontend/src/components/ProtectedRoute.tsx`
- Create: `frontend/src/App.tsx`

- [ ] **Step 1: Write src/lib/routes.ts**

```ts
export const ROUTES = {
  landing: "/",
  login: "/login",
  checkout: (planId: string) => `/checkout/${planId}`,
  pay: (invoiceId: number | string) => `/pay/${invoiceId}`,
  cabinet: "/cabinet",
} as const;
```

- [ ] **Step 2: Write src/lib/api.ts**

```ts
export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, { credentials: "include", headers: { "Content-Type": "application/json" }, ...init });
  if (!res.ok) {
    let detail = res.statusText;
    try { detail = (await res.json()).detail ?? detail; } catch { /* noop */ }
    throw new ApiError(res.status, detail);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  get: <T,>(path: string) => request<T>(path),
  post: <T,>(path: string, body?: unknown) => request<T>(path, { method: "POST", body: body ? JSON.stringify(body) : undefined }),
};

export type Plan = { id: string; title: string; months: number; price_rub: number; discount_percent: number };
export type Me = { telegram_id: number; username: string | null; subscription_until: string | null; balance_rub: number };
export type PaymentCreated = { invoice_id: number; pay_url: string; amount_rub: number; payable_rub: number; status: string };
export type PaymentStatus = { invoice_id: number; status: string; paid: boolean };
export type KeyConfig = { server: string; protocol: string; url: string; active: boolean };
export type CabinetKeys = { active: boolean; subscription_url: string | null; subscription_until: string | null; configs: KeyConfig[] };
export type PaymentHistoryItem = { invoice_id: number; amount_rub: number; payable_rub: number; months: number; plan_id: string; status: string; created_at: string | null; paid_at: string | null };
```

- [ ] **Step 3: Write src/lib/telegram.ts**

```ts
// Loads Telegram Login Widget script and renders the button into a container.
export function loadTelegramWidget(containerId: string, botUsername: string, onAuth: (user: unknown) => void) {
  const existing = document.getElementById("tg-widget-script");
  if (!existing) {
    const s = document.createElement("script");
    s.id = "tg-widget-script";
    s.async = true;
    s.src = "https://telegram.org/js/telegram-widget.js?22";
    document.body.appendChild(s);
  }
  const el = document.getElementById(containerId);
  if (el) {
    el.setAttribute("data-telegram-login", botUsername);
    el.setAttribute("data-size", "large");
    el.setAttribute("data-radius", "10");
    el.setAttribute("data-onauth", "telegramLogin(user)");
    el.setAttribute("data-request-access", "write");
  }
  // global callback
  (window as any).telegramLogin = (user: unknown) => onAuth(user);
}
```

- [ ] **Step 4: Write src/components/ProtectedRoute.tsx**

```tsx
import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import { api, type Me } from "../lib/api";
import { ROUTES } from "../lib/routes";
import { Spinner } from "./Spinner";

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<"loading" | "ok" | "deny">("loading");
  useEffect(() => {
    api.get<Me>("/api/auth/me")
      .then(() => setState("ok"))
      .catch(() => setState("deny"));
  }, []);
  if (state === "loading") return <div style={{ paddingTop: 80, textAlign: "center" }}><Spinner /></div>;
  if (state === "deny") return <Navigate to={ROUTES.login} replace />;
  return <>{children}</>;
}
```

- [ ] **Step 5: Write src/App.tsx (routes shell)**

```tsx
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Landing } from "./pages/Landing";
import { Login } from "./pages/Login";
import { Checkout } from "./pages/Checkout";
import { Pay } from "./pages/Pay";
import { Cabinet } from "./pages/Cabinet";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { ROUTES } from "./lib/routes";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path={ROUTES.landing} element={<Landing />} />
        <Route path={ROUTES.login} element={<Login />} />
        <Route path="/checkout/:planId" element={<Checkout />} />
        <Route path="/pay/:invoiceId" element={<Pay />} />
        <Route path={ROUTES.cabinet} element={<ProtectedRoute><Cabinet /></ProtectedRoute>} />
        <Route path="*" element={<Navigate to={ROUTES.landing} replace />} />
      </Routes>
    </BrowserRouter>
  );
}
```

- [ ] **Step 6: Update src/main.tsx**

```tsx
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./styles.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

- [ ] **Step 7: Commit**

```bash
git add frontend/src/lib frontend/src/components/ProtectedRoute.tsx frontend/src/App.tsx frontend/src/main.tsx
git commit -m "feat(frontend): api client, routes, auth guard, telegram widget loader"
```

(Page components referenced by App.tsx are created in Tasks 20–24; create empty stubs first to keep the build green, or implement them in order — the next tasks fill them.)

---

## Task 20: Landing page

**Files:**
- Create: `frontend/src/components/FAQ.tsx`
- Create: `frontend/src/pages/Landing.tsx`

- [ ] **Step 1: Write src/components/FAQ.tsx**

```tsx
import { useState } from "react";

type Item = { q: string; a: string };
export function FAQ({ items }: { items: Item[] }) {
  const [open, setOpen] = useState<number | null>(0);
  return (
    <div style={{ display: "grid", gap: 10 }}>
      {items.map((it, i) => (
        <div key={i} className="glass" style={{ padding: "14px 18px", cursor: "pointer" }} onClick={() => setOpen(open === i ? null : i)}>
          <div style={{ display: "flex", justifyContent: "space-between", fontWeight: 600, fontSize: 14 }}>{it.q}<span style={{ color: "#a1a1aa" }}>{open === i ? "−" : "+"}</span></div>
          {open === i && <p className="muted" style={{ marginTop: 8, fontSize: 13, lineHeight: 1.5 }}>{it.a}</p>}
        </div>
      ))}
    </div>
  );
}
```

- [ ] **Step 2: Write src/pages/Landing.tsx** (hero, plans, key-flow, stack, faq — uses public config + plans endpoints)

```tsx
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, type Plan } from "../lib/api";
import { ROUTES } from "../lib/routes";
import { Button } from "../components/Button";
import { FAQ } from "../components/FAQ";
import { Logo } from "../components/Logo";

type PubConfig = { features: { icon: string; title: string; text: string }[]; metrics: Record<string, string>; faq: { q: string; a: string }[] };

export function Landing() {
  const [cfg, setCfg] = useState<PubConfig | null>(null);
  const [plans, setPlans] = useState<Plan[]>([]);
  useEffect(() => {
    api.get<PubConfig>("/api/public/config").then(setCfg);
    api.get<Plan[]>("/api/plans").then(setPlans);
  }, []);

  return (
    <div className="container" style={{ paddingBottom: 80 }}>
      <nav style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "22px 0" }}>
        <Logo />
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <a className="muted" style={{ fontSize: 14, padding: "6px 14px" }} href="#plans">Тарифы</a>
          <a className="muted" style={{ fontSize: 14, padding: "6px 14px" }} href="#how">Как это работает</a>
          <Link to={ROUTES.login}><Button variant="ghost">Войти</Button></Link>
        </div>
      </nav>

      <section style={{ textAlign: "center", padding: "40px 0 20px" }}>
        <div className="glass" style={{ display: "inline-flex", alignItems: "center", gap: 8, padding: "6px 14px", borderRadius: 999, fontSize: 12 }}>
          <span style={{ width: 7, height: 7, borderRadius: "50%", background: "#34d399", boxShadow: "0 0 8px #34d399" }} />
          <span className="muted">0 логов · Reality + Hysteria2</span>
        </div>
        <h1 style={{ fontSize: 44, fontWeight: 700, letterSpacing: "-1px", lineHeight: 1.1, margin: "16px 0 12px" }}>
          VPN, который <span className="gradient-text">просто работает</span>
        </h1>
        <p className="muted" style={{ fontSize: 16, maxWidth: 460, margin: "0 auto 22px", lineHeight: 1.6 }}>
          Подключение за 30 секунд. Платите криптой — ключ моментально. Импорт в HAPP и Hiddify в один тап.
        </p>
        <Link to={ROUTES.cabinet}><Button>Получить ключ →</Button></Link>
        <div style={{ display: "flex", gap: 26, justifyContent: "center", marginTop: 22, fontSize: 13 }}>
          <span className="dim"><b style={{ color: "#e4e4e7" }}>{cfg?.metrics.servers ?? 4}</b> сервера</span>
          <span className="dim"><b style={{ color: "#e4e4e7" }}>{cfg?.metrics.speed ?? "1 Гбит"}</b>/чел</span>
          <span className="dim"><b style={{ color: "#e4e4e7" }}>{cfg?.metrics.uptime ?? "99.9%"}</b> аптайм</span>
        </div>
      </section>

      <section id="plans" style={{ padding: "30px 0" }}>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 14 }}>
          {plans.map((p) => {
            const hot = p.discount_percent >= 30;
            return (
              <div key={p.id} className="glass" style={{ padding: 24, borderColor: hot ? "rgba(139,155,255,0.4)" : undefined, background: hot ? "rgba(139,155,255,0.10)" : undefined }}>
                {hot && <div style={{ fontSize: 11, color: "#a5b4fc", fontWeight: 700, marginBottom: 8 }}>ВЫГОДНО</div>}
                <div style={{ fontSize: 15, fontWeight: 600 }}>{p.title}</div>
                <div style={{ fontSize: 30, fontWeight: 700, margin: "10px 0" }}>{p.price_rub} ₽</div>
                <div className="dim" style={{ fontSize: 13, marginBottom: 16 }}>{p.discount_percent > 0 ? `скидка ${p.discount_percent}%` : "стандарт"}</div>
                <Link to={ROUTES.checkout(p.id)} style={{ display: "block" }}><Button style={{ width: "100%" }}>Выбрать</Button></Link>
              </div>
            );
          })}
        </div>
      </section>

      <section id="how" style={{ padding: "20px 0 40px" }}>
        <h2 style={{ fontSize: 22, fontWeight: 700, textAlign: "center", marginBottom: 6 }}>От оплаты до подключения</h2>
        <p className="dim" style={{ textAlign: "center", marginBottom: 22, fontSize: 14 }}>Как ключ попадает в ваше приложение</p>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 14 }}>
          {[
            { step: "01", t: "Оплата криптой", d: "USDT, BTC, TON через CryptoBot. Безопасно и анонимно." },
            { step: "02", t: "Получение ключа", d: "Мгновенная выдача ссылки-подписки в личном кабинете." },
            { step: "03", t: "Импорт в приложение", d: "Один тап — и 4 сервера доступны в HAPP / Hiddify." },
          ].map((s) => (
            <div key={s.step} className="glass" style={{ padding: 20, textAlign: "center" }}>
              <div style={{ fontSize: 11, color: "#a5b4fc", letterSpacing: 1, fontWeight: 700 }}>ШАГ {s.step}</div>
              <h4 style={{ margin: "10px 0 6px", fontSize: 15 }}>{s.t}</h4>
              <p className="muted" style={{ fontSize: 13, lineHeight: 1.5 }}>{s.d}</p>
            </div>
          ))}
        </div>
      </section>

      <section style={{ padding: "10px 0 40px" }}>
        <h2 style={{ fontSize: 22, fontWeight: 700, textAlign: "center", marginBottom: 20 }}>Частые вопросы</h2>
        {cfg && <FAQ items={cfg.faq} />}
      </section>
    </div>
  );
}
```

- [ ] **Step 3: Verify build**

Run: `cd frontend && npm run build`
Expected: success

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/FAQ.tsx frontend/src/pages/Landing.tsx
git commit -m "feat(frontend): landing page with hero, plans, flow, faq"
```

---

## Task 21: Login page (Telegram Login Widget)

**Files:**
- Create: `frontend/src/pages/Login.tsx`

- [ ] **Step 1: Write src/pages/Login.tsx**

```tsx
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, type Me } from "../lib/api";
import { loadTelegramWidget } from "../lib/telegram";
import { ROUTES } from "../lib/routes";
import { GlassCard } from "../components/GlassCard";
import { Spinner } from "../components/Spinner";
import { Logo } from "../components/Logo";

export function Login() {
  const nav = useNavigate();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const bot = (import.meta as any).env?.VITE_TG_BOT_USERNAME || "";
    if (bot) loadTelegramWidget("tg-login-container", bot, (user) => onTelegramUser(user as Record<string, unknown>));
  }, []);

  async function onTelegramUser(user: Record<string, unknown>) {
    setBusy(true);
    setError(null);
    try {
      await api.post("/api/auth/telegram", user);
      const me = await api.get<Me>("/api/auth/me");
      nav(me.subscription_until ? ROUTES.cabinet : ROUTES.landing, { replace: true });
    } catch (e: any) {
      setError(e?.message ?? "Ошибка авторизации");
      setBusy(false);
    }
  }

  return (
    <div className="container" style={{ display: "flex", justifyContent: "center", paddingTop: 80 }}>
      <GlassCard style={{ width: 380, textAlign: "center" }}>
        <Logo />
        <h1 style={{ fontSize: 24, margin: "16px 0 6px", fontWeight: 700 }}>Вход через Telegram</h1>
        <p className="muted" style={{ fontSize: 14, marginBottom: 24 }}>Авторизуйтесь через Telegram, чтобы купить и управлять подпиской.</p>
        {busy ? <Spinner /> : <div id="tg-login-container" style={{ display: "flex", justifyContent: "center", minHeight: 52 }} />}
        {error && <p style={{ color: "#fca5a5", fontSize: 13, marginTop: 16 }}>{error}</p>}
        {!busy && (
          <p className="dim" style={{ fontSize: 12, marginTop: 20 }}>
            Нет Telegram-бота? Установите <code>VITE_TG_BOT_USERNAME</code> в <code>frontend/.env</code> и создайте бот через @BotFather.
          </p>
        )}
      </GlassCard>
    </div>
  );
}
```

- [ ] **Step 2: Create frontend/.env.example**

```
VITE_TG_BOT_USERNAME=yourbotname
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/Login.tsx frontend/.env.example
git commit -m "feat(frontend): telegram login widget page"
```

---

## Task 22: Checkout page (plan + promo)

**Files:**
- Create: `frontend/src/pages/Checkout.tsx`

- [ ] **Step 1: Write src/pages/Checkout.tsx**

```tsx
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api, type Plan, type PaymentCreated } from "../lib/api";
import { ROUTES } from "../lib/routes";
import { GlassCard } from "../components/GlassCard";
import { Button } from "../components/Button";
import { Spinner } from "../components/Spinner";

export function Checkout() {
  const { planId } = useParams();
  const nav = useNavigate();
  const [plan, setPlan] = useState<Plan | null>(null);
  const [promo, setPromo] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.get<Plan[]>("/api/plans").then((all) => setPlan(all.find((p) => p.id === planId) ?? null));
  }, [planId]);

  async function pay() {
    if (!plan) return;
    setBusy(true);
    setError(null);
    try {
      const res = await api.post<PaymentCreated>("/api/payments/create", { plan_id: plan.id, promo_code: promo || undefined });
      nav(ROUTES.pay(res.invoice_id));
    } catch (e: any) {
      setError(e?.message ?? "Не удалось создать счёт");
      setBusy(false);
    }
  }

  if (!plan) return <div className="container" style={{ paddingTop: 80, textAlign: "center" }}><Spinner /></div>;

  return (
    <div className="container" style={{ display: "flex", justifyContent: "center", paddingTop: 60 }}>
      <GlassCard style={{ width: 420 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 4 }}>Оформление</h1>
        <p className="muted" style={{ fontSize: 14, marginBottom: 20 }}>Тариф: <b style={{ color: "#fafafa" }}>{plan.title}</b> — {plan.price_rub} ₽</p>

        <label className="dim" style={{ fontSize: 12 }}>Промокод</label>
        <input
          value={promo}
          onChange={(e) => setPromo(e.target.value.toUpperCase())}
          placeholder="WELCOME10"
          className="glass"
          style={{ width: "100%", padding: "11px 14px", marginTop: 6, marginBottom: 18, color: "#fff", fontSize: 14, outline: "none" }}
        />

        {error && <p style={{ color: "#fca5a5", fontSize: 13, marginBottom: 14 }}>{error}</p>}
        <Button style={{ width: "100%" }} disabled={busy} onClick={pay}>{busy ? "Создаём счёт..." : `Оплатить ${plan.price_rub} ₽`}</Button>
        <p className="dim" style={{ fontSize: 12, marginTop: 14, textAlign: "center" }}>Оплата криптой (USDT/BTC/TON) через CryptoBot.</p>
      </GlassCard>
    </div>
  );
}
```

- [ ] **Step 2: Verify build**

Run: `cd frontend && npm run build`
Expected: success

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/Checkout.tsx
git commit -m "feat(frontend): checkout page with promo field"
```

---

## Task 23: Pay page (polling)

**Files:**
- Create: `frontend/src/pages/Pay.tsx`

- [ ] **Step 1: Write src/pages/Pay.tsx**

```tsx
import { useEffect, useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import { api, type PaymentStatus } from "../lib/api";
import { ROUTES } from "../lib/routes";
import { GlassCard } from "../components/GlassCard";
import { Button } from "../components/Button";
import { Spinner } from "../components/Spinner";

export function Pay() {
  const { invoiceId } = useParams();
  const nav = useNavigate();
  const location = useLocation();
  const payUrl = (location.state as { pay_url?: string } | null)?.pay_url ?? "";
  const [status, setStatus] = useState<string>("active");

  useEffect(() => {
    if (!invoiceId) return;
    let stop = false;
    const poll = async () => {
      while (!stop) {
        try {
          const s = await api.get<PaymentStatus>(`/api/payments/status/${invoiceId}`);
          setStatus(s.status);
          if (s.paid) { nav(ROUTES.cabinet, { replace: true }); return; }
        } catch { /* keep polling */ }
        await new Promise((r) => setTimeout(r, 3000));
      }
    };
    poll();
    return () => { stop = true; };
  }, [invoiceId, nav]);

  function openPay() {
    if (payUrl) window.open(payUrl, "_blank", "noopener");
  }

  return (
    <div className="container" style={{ display: "flex", justifyContent: "center", paddingTop: 80 }}>
      <GlassCard style={{ width: 420, textAlign: "center" }}>
        <Spinner />
        <h1 style={{ fontSize: 22, fontWeight: 700, margin: "16px 0 6px" }}>Ожидаем оплату</h1>
        <p className="muted" style={{ fontSize: 14, marginBottom: 20 }}>Статус: {status === "paid" ? "оплачено" : "ожидание..."}</p>
        <p className="dim" style={{ fontSize: 13, marginBottom: 18 }}>Завершите платёж в окне CryptoBot. Мы проверим оплату автоматически.</p>
        {payUrl && <Button variant="ghost" onClick={openPay}>Открыть окно оплаты снова</Button>}
      </GlassCard>
    </div>
  );
}
```

> This page reads `pay_url` from router state (passed by the Checkout page after `/payments/create`). Update the Checkout page's `pay()` to pass it: `nav(ROUTES.pay(res.invoice_id), { state: { pay_url: res.pay_url } })`. This keeps the MVP correct without a new endpoint.

- [ ] **Step 2: Update Checkout pay() to pass pay_url**

In `frontend/src/pages/Checkout.tsx`, change the success branch of `pay()` from:
```tsx
nav(ROUTES.pay(res.invoice_id));
```
to:
```tsx
nav(ROUTES.pay(res.invoice_id), { state: { pay_url: res.pay_url } });
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/Pay.tsx
git commit -m "feat(frontend): payment polling page"
```

---

## Task 24: Cabinet page (subscription + keys + QR + history)

**Files:**
- Create: `frontend/src/pages/Cabinet.tsx`

- [ ] **Step 1: Write src/pages/Cabinet.tsx**

```tsx
import { useEffect, useState } from "react";
import QRCode from "qrcode";
import { Link } from "react-router-dom";
import { api, type CabinetKeys, type Me, type PaymentHistoryItem } from "../lib/api";
import { ROUTES } from "../lib/routes";
import { GlassCard } from "../components/GlassCard";
import { Button } from "../components/Button";
import { Logo } from "../components/Logo";

export function Cabinet() {
  const [me, setMe] = useState<Me | null>(null);
  const [keys, setKeys] = useState<CabinetKeys | null>(null);
  const [hist, setHist] = useState<PaymentHistoryItem[]>([]);
  const [qr, setQr] = useState<string>("");
  const [copied, setCopied] = useState(false);
  const [showConfigs, setShowConfigs] = useState(false);

  useEffect(() => {
    api.get<Me>("/api/auth/me").then(setMe);
    api.get<CabinetKeys>("/api/cabinet/keys").then(async (k) => {
      setKeys(k);
      if (k.subscription_url) setQr(await QRCode.toDataURL(k.subscription_url, { margin: 1, width: 220, color: { dark: "#0a0c10", light: "#ffffff" } }));
    });
    api.get<PaymentHistoryItem[]>("/api/payments/history").then(setHist);
  }, []);

  function copy() {
    if (!keys?.subscription_url) return;
    navigator.clipboard.writeText(keys.subscription_url);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  const active = me?.subscription_until && new Date(me.subscription_until) > new Date();

  return (
    <div className="container" style={{ paddingBottom: 80 }}>
      <nav style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "22px 0" }}>
        <Logo />
        <a href="/api/auth/logout" onClick={(e) => { e.preventDefault(); api.post("/api/auth/logout").then(() => (window.location.href = ROUTES.landing)); }}>
          <Button variant="ghost">Выйти</Button>
        </a>
      </nav>

      <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: 16, maxWidth: 620, margin: "0 auto" }}>
        <GlassCard>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
            <h2 style={{ fontSize: 18, fontWeight: 700 }}>Подписка</h2>
            <span style={{ fontSize: 12, padding: "4px 10px", borderRadius: 999, background: active ? "rgba(52,211,153,0.15)" : "rgba(113,113,122,0.15)", color: active ? "#34d399" : "#a1a1aa" }}>
              {active ? "Активна" : "Неактивна"}
            </span>
          </div>
          {active ? (
            <p className="muted" style={{ fontSize: 14 }}>Действует до <b style={{ color: "#fafafa" }}>{new Date(me!.subscription_until!).toLocaleDateString("ru-RU")}</b></p>
          ) : (
            <div>
              <p className="muted" style={{ fontSize: 14, marginBottom: 12 }}>У вас нет активной подписки.</p>
              <Link to={ROUTES.checkout("p1m")}><Button>Купить подписку</Button></Link>
            </div>
          )}
        </GlassCard>

        {active && keys?.subscription_url && (
          <GlassCard>
            <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 6 }}>Ваш ключ</h2>
            <p className="dim" style={{ fontSize: 13, marginBottom: 16 }}>Один ключ на все устройства. Вставьте эту ссылку в HAPP или Hiddify.</p>
            <div style={{ display: "flex", gap: 20, flexWrap: "wrap", alignItems: "center" }}>
              {qr && <img src={qr} alt="QR" style={{ borderRadius: 12, width: 180, height: 180 }} />}
              <div style={{ flex: 1, minWidth: 220 }}>
                <div className="glass" style={{ padding: 12, fontFamily: "ui-monospace, monospace", fontSize: 11, wordBreak: "break-all", color: "#86efac", marginBottom: 12 }}>
                  {keys.subscription_url}
                </div>
                <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                  <Button onClick={copy}>{copied ? "Скопировано!" : "Скопировать"}</Button>
                  <Button variant="ghost" onClick={() => setShowConfigs(!showConfigs)}>{showConfigs ? "Скрыть конфиги" : "Показать конфиги"}</Button>
                </div>
              </div>
            </div>
            {showConfigs && (
              <div style={{ marginTop: 16, display: "grid", gap: 8 }}>
                {keys.configs.map((c, i) => (
                  <div key={i} className="glass" style={{ padding: 10, fontSize: 11, fontFamily: "ui-monospace, monospace", color: "#a1a1aa", wordBreak: "break-all" }}>
                    <b style={{ color: "#c4b5fd" }}>{c.server}</b> · {c.protocol}<br />{c.url}
                  </div>
                ))}
              </div>
            )}
          </GlassCard>
        )}

        <GlassCard>
          <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 12 }}>История платежей</h2>
          {hist.length === 0 ? <p className="dim" style={{ fontSize: 13 }}>Платежей пока нет.</p> : (
            <div style={{ display: "grid", gap: 8 }}>
              {hist.map((p) => (
                <div key={p.invoice_id} style={{ display: "flex", justifyContent: "space-between", fontSize: 13, padding: "8px 0", borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
                  <span>{p.payable_rub} ₽ · {p.months} мес</span>
                  <span style={{ color: p.status === "paid" ? "#34d399" : "#a1a1aa" }}>{p.status === "paid" ? "Оплачено" : p.status}</span>
                </div>
              ))}
            </div>
          )}
        </GlassCard>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Verify build**

Run: `cd frontend && npm run build`
Expected: success

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/Cabinet.tsx
git commit -m "feat(frontend): cabinet with subscription, key+qr, configs, history"
```

---

## Task 25: Deploy artifacts (nginx + systemd)

**Files:**
- Create: `deploy/nginx.conf`
- Create: `deploy/trumpvpn.service`
- Create: `deploy/README.md`

- [ ] **Step 1: Write deploy/nginx.conf**

```nginx
server {
    listen 80;
    server_name trumpvpn.example.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name trumpvpn.example.com;

    ssl_certificate     /etc/letsencrypt/live/trumpvpn.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/trumpvpn.example.com/privkey.pem;

    root /opt/trumpvpn/frontend/dist;
    index index.html;

    # API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Subscription endpoint (public, token-protected)
    location /sub/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
    }

    # SPA fallback
    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

- [ ] **Step 2: Write deploy/trumpvpn.service**

```ini
[Unit]
Description=TrumpVPN Backend (FastAPI)
After=network.target

[Service]
Type=simple
User=trumpvpn
WorkingDirectory=/opt/trumpvpn/backend
EnvironmentFile=/opt/trumpvpn/backend/.env
ExecStart=/opt/trumpvpn/backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

- [ ] **Step 3: Write deploy/README.md**

```markdown
# TrumpVPN Deploy

1. Provision server, create user `trumpvpn`.
2. Clone repo to `/opt/trumpvpn`.
3. Backend: `python -m venv backend/.venv && backend/.venv/bin/pip install -r backend/requirements.txt`.
4. Copy `backend/.env.example` to `backend/.env`, fill `TG_BOT_TOKEN`, `CRYPTO_PAY_API_TOKEN`, `JWT_SECRET`, `PUBLIC_BASE_URL`.
5. Seed servers/promo: `backend/.venv/bin/python -c "from app.db.base import init_db; init_db(); from app.db.init_db import seed_dev; seed_dev()"`.
6. Frontend: `cd frontend && npm ci && npm run build`.
7. Install nginx config: `cp deploy/nginx.conf /etc/nginx/sites-available/trumpvpn && ln -s ... && nginx -t && systemctl reload nginx`.
8. Install systemd unit: `cp deploy/trumpvpn.service /etc/systemd/system/ && systemctl daemon-reload && systemctl enable --now trumpvpn`.
9. SSL: `certbot --nginx -d trumpvpn.example.com`.
```

- [ ] **Step 4: Commit**

```bash
git add deploy/
git commit -m "chore: nginx and systemd deploy configs"
```

---

## Task 26: End-to-end smoke + documentation

**Files:**
- Create: `README.md` (root)

- [ ] **Step 1: Full backend test run**

Run:
```bash
cd backend && . .venv/Scripts/activate && python -m pytest tests/ -q
```
Expected: all PASS

- [ ] **Step 2: Frontend build**

Run:
```bash
cd frontend && npm run build
```
Expected: success

- [ ] **Step 3: Manual E2E smoke (both dev servers)**

Terminal 1: `cd backend && . .venv/Scripts/activate && uvicorn app.main:app --reload --port 8000`
Terminal 2: `cd frontend && npm run dev`
Browser: `http://localhost:5173`
Verify: landing loads + plans render; `/login` shows (widget needs a real bot username); `/cabinet` redirects to login when not authed.

- [ ] **Step 4: Write root README.md**

```markdown
# TrumpVPN

VPN service web app — landing, Telegram auth, CryptoBot payments, instant key delivery across 4 servers.

## Stack
- **Backend:** FastAPI, SQLAlchemy 2.0, SQLite (WAL), PyJWT, httpx, paramiko
- **Frontend:** React 18, Vite, TypeScript, react-router-dom, qrcode
- **Deploy:** nginx + systemd

## Structure
- `backend/` — FastAPI JSON-API + services (protocols, telegram-auth, cryptobot, provisioning, subscription)
- `frontend/` — React SPA (landing, login, checkout, pay, cabinet)
- `deploy/` — nginx + systemd configs
- `docs/superpowers/specs/` — design spec

## Dev quickstart
```bash
# backend
cd backend && python -m venv .venv && . .venv/Scripts/activate
pip install -r requirements.txt
cp .env.example .env   # fill TG_BOT_TOKEN, CRYPTO_PAY_API_TOKEN, JWT_SECRET
uvicorn app.main:app --reload --port 8000

# frontend
cd frontend && npm install
echo "VITE_TG_BOT_USERNAME=yourbot" > .env
npm run dev   # http://localhost:5173
```

See `docs/superpowers/specs/2026-06-25-trumpvpn-core-design.md` for the full design.
```

- [ ] **Step 5: Commit**

```bash
git add README.md
git commit -m "docs: root README with stack and quickstart"
```

---

## Done criteria

- [ ] Backend test suite green (protocols, telegram_auth, promo, subscription_service)
- [ ] `frontend npm run build` succeeds
- [ ] Landing renders with 3 plans + FAQ from API
- [ ] Telegram login → JWT cookie → `/api/auth/me` returns user
- [ ] Checkout creates a CryptoBot invoice; Pay page polls status
- [ ] On `status=paid`: 4 client configs created, subscription_token minted, `subscription_until` set
- [ ] `/sub/{telegram_id}/{token}` returns base64 of all active configs
- [ ] Cabinet shows subscription status, subscription URL + QR, configs, payment history
- [ ] Deploy artifacts present (nginx + systemd)
```
