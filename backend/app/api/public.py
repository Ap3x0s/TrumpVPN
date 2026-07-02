from fastapi import APIRouter

from app.plans import PLANS

router = APIRouter(tags=["public"])

# Supported apps — shown as a marquee/strip on the landing.
SUPPORTED_APPS = [
    "YouTube", "Telegram", "Instagram", "X", "WhatsApp",
    "Claude", "Twitch", "Spotify", "TikTok", "Discord", "ChatGPT",
]

# Devices the VPN works on — "для любого устройства" section.
SUPPORTED_DEVICES = [
    {"icon": "phone", "title": "Android", "text": "HAPP, Hiddify, v2rayNG"},
    {"icon": "apple", "title": "iOS / iPad", "text": "HAPP, Hiddify, Streisand"},
    {"icon": "laptop", "title": "Windows", "text": "Hiddify, Nekoray, v2rayN"},
    {"icon": "monitor", "title": "macOS", "text": "HAPP, Hiddify, FoXray"},
    {"icon": "router", "title": "Роутер", "text": "OpenWrt, Keenetic (VLESS)"},
    {"icon": "tv", "title": "Smart TV", "text": "Android TV через HAPP"},
]


@router.get("/api/public/config")
def public_config() -> dict:
    return {
        "features": [
            {"icon": "shield", "title": "0 логов", "text": "Мы не храним историю подключений и ваши данные."},
            {"icon": "bolt", "title": "1 Гбит/чел", "text": "Выделенный канал на каждого пользователя."},
            {"icon": "key", "title": "Один ключ", "text": "Все серверы в одной подписке — ставьте куда угодно."},
            {"icon": "lock", "title": "VLESS Reality", "text": "Современный протокол обхода любых блокировок."},
            {"icon": "globe", "title": "4 страны", "text": "Нидерланды, Польша, Финляндия, Германия."},
            {"icon": "rocket", "title": "Мгновенно", "text": "Оплата криптой — ключ выдаётся сразу."},
        ],
        "metrics": {"servers": 4, "speed": "1 Гбит", "uptime": "99.9%"},
        "countries": [
            {"code": "NL", "name": "Нидерланды"},
            {"code": "PL", "name": "Польша"},
            {"code": "FI", "name": "Финляндия"},
            {"code": "DE", "name": "Германия"},
        ],
        "apps": SUPPORTED_APPS,
        "devices": SUPPORTED_DEVICES,
        "faq": [
            {
                "q": "Как оплатить подписку?",
                "a": "Криптовалютой (USDT, BTC, TON) через CryptoBot. Оплата анонимна, ключ выдаётся автоматически сразу после подтверждения платежа.",
            },
            {
                "q": "На сколько устройств хватает подписки?",
                "a": "Без ограничений. Один ключ устанавливается на любое число устройств — телефон, ноутбук, планшет, Smart TV и даже роутер.",
            },
            {
                "q": "Какие приложения поддерживаются?",
                "a": "HAPP и Hiddify на всех платформах, а также v2rayNG, Nekoray, Streisand и другие клиенты с поддержкой VLESS-подписок.",
            },
            {
                "q": "Что такое VLESS Reality?",
                "a": "Это современный протокол, который маскирует VPN-трафик под обычное HTTPS-соединение. Его невозможно отличить от обычного сайта, поэтому блокировки его не видят.",
            },
            {
                "q": "Будет ли VPN работать в моей стране?",
                "a": "Да. Reality-протокол разработан специально для обхода систем DPI и глубокого анализа трафика. Он стабильно работает даже там, где обычные VPN заблокированы.",
            },
            {
                "q": "Что если не понравится?",
                "a": "Напишите в поддержку через бота — поможем настроить. Если что-то не сработает, подберём оптимальный сервер под вашего провайдера.",
            },
        ],
    }


@router.get("/api/plans")
def plans() -> list[dict]:
    return PLANS
