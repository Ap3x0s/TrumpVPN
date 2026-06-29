# TrumpVPN

VPN service web app — landing, Telegram auth, CryptoBot payments, instant key delivery across 4 servers.

## Stack
- **Backend:** FastAPI, SQLAlchemy 2.0, SQLite (WAL), PyJWT, httpx, paramiko
- **Frontend:** React 18, Vite, TypeScript, react-router-dom, qrcode
- **Deploy:** nginx + systemd

## Structure
- `backend/` — FastAPI JSON-API + services (protocols, telegram-auth, cryptobot, provisioning, subscription)
- `frontend/` — React SPA (landing, login, checkout, pay, cabinet)
- `bot/` — aiogram login bot (magic-link login via `/start` → deep-link button)
- `deploy/` — nginx + systemd configs

## Dev quickstart

Three processes run side by side in dev. Use the same venv for backend + bot.

```bash
# backend
cd backend && python -m venv .venv && . .venv/Scripts/activate    # Windows Git Bash
pip install -r requirements.txt
cp .env.example .env   # fill TG_BOT_TOKEN, CRYPTO_PAY_API_TOKEN, JWT_SECRET, LOGIN_BOT_TOKEN
uvicorn app.main:app --reload --port 8000

# frontend
cd frontend && npm install
echo "VITE_TG_BOT_USERNAME=yourbot" > .env
npm run dev   # http://localhost:5173

# bot (separate terminal, same venv active)
cd bot && cp .env.example .env   # BOT_TOKEN, BOT_AUTH_TOKEN (== backend LOGIN_BOT_TOKEN), SITE_URL
python -m bot
```

For local testing with Telegram Login Widget / magic-link, expose the frontend
through a tunnel (`cloudflared tunnel --url http://localhost:5173`) and put the
tunnel URL as `SITE_URL` in `bot/.env`.

## Tests

```bash
cd backend && . .venv/Scripts/activate && python -m pytest tests/ -q
```

See `docs/superpowers/specs/2026-06-25-trumpvpn-core-design.md` for the full design.
