# TrumpVPN Deploy

1. Provision server, create user `trumpvpn`.
2. Clone repo to `/opt/trumpvpn`.
3. Backend: `python -m venv backend/.venv && backend/.venv/bin/pip install -r backend/requirements.txt`.
4. Copy `backend/.env.example` to `backend/.env`, fill `TG_BOT_TOKEN`, `CRYPTO_PAY_API_TOKEN`, `JWT_SECRET`, `PUBLIC_BASE_URL`.
5. Seed servers/promo: `backend/.venv/bin/python -c "from app.db.base import init_db; init_db(); from app.db.init_db import seed_dev; seed_dev()"`.
6. Frontend: `cd frontend && npm ci && npm run build`.
7. Install nginx config: `cp deploy/nginx.conf /etc/nginx/sites-available/trumpvpn && ln -s /etc/nginx/sites-available/trumpvpn /etc/nginx/sites-enabled/ && nginx -t && systemctl reload nginx`.
8. Install systemd unit: `cp deploy/trumpvpn.service /etc/systemd/system/ && systemctl daemon-reload && systemctl enable --now trumpvpn`.
9. SSL: `certbot --nginx -d trumpvpn.example.com`.
