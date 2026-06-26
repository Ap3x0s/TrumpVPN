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
