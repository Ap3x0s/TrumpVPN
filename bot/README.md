# TrumpVPN Login Bot

A small aiogram bot that issues **magic-link login** tokens for the TrumpVPN website.

## How it works

```
user -> @trumpvpn1bot -> /start (or /login)
  bot -> backend POST /api/auth/issue-token  (X-Bot-Token shared secret)
       <- { token }
  bot -> sends inline button linking to {SITE_URL}/login?token=xxx
user -> clicks button
  website -> POST /api/auth/exchange { token }
           <- sets JWT session cookie, redirects to /cabinet
```

The token is **one-time use**, valid **10 minutes**, bound to the `telegram_id`.

## Prerequisites

- Python 3.11+ with the backend venv active (aiogram is in `backend/requirements.txt`)
- Backend running on `BACKEND_URL`
- The website reachable at `SITE_URL` (tunnel URL in dev, real domain in prod)

## Setup

1. Copy `.env.example` to `.env` and fill in:
   ```
   BOT_TOKEN=<from @BotFather, same bot as the website's Login Widget>
   BOT_AUTH_TOKEN=<MUST match backend's LOGIN_BOT_TOKEN>
   BACKEND_URL=http://localhost:8000
   SITE_URL=<your tunnel or domain>
   ```
2. Generate the shared secret on the backend and paste the **same value** into both `backend/.env` (`LOGIN_BOT_TOKEN`) and `bot/.env` (`BOT_AUTH_TOKEN`).

## Run

Run the bot as a **separate process** from the backend:

```bash
# from the repo root, with the backend venv active
python -m bot
```

You should see `[bot] polling started | backend=... site=...`.

In dev you run **three processes**:
1. `cd backend && uvicorn app.main:app --reload --port 8000`
2. `cd frontend && npm run dev`
3. `python -m bot` (from repo root)

## Bot commands

- `/start` — greet + login button
- `/login` — login button (alias)
- any other text — hint to use `/login`
