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
- `docs/superpowers/plans/` — implementation plan

## Dev quickstart

```bash
# backend
cd backend && python -m venv .venv && . .venv/Scripts/activate    # Windows Git Bash
pip install -r requirements.txt
cp .env.example .env   # fill TG_BOT_TOKEN, CRYPTO_PAY_API_TOKEN, JWT_SECRET
uvicorn app.main:app --reload --port 8000

# frontend
cd frontend && npm install
echo "VITE_TG_BOT_USERNAME=yourbot" > .env
npm run dev   # http://localhost:5173
```

## Tests

```bash
cd backend && . .venv/Scripts/activate && python -m pytest tests/ -q
```

See `docs/superpowers/specs/2026-06-25-trumpvpn-core-design.md` for the full design.
