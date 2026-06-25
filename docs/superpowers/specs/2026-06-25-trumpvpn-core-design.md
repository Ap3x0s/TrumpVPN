# TrumpVPN — Design Spec: Core Path (Landing → Payment → Key Delivery)

**Дата:** 2026-06-25
**Статус:** Approved (pending user review)
**Фаза:** 1 — MVP core path + промокоды
**Референс-репозиторий:** `matrass3/trumpvpn` (изучен; ценная доменная логика переносится, остальное переписывается)

---

## 1. Контекст и цели

Построить **полноценный веб-сайт VPN-сервиса** TrumpVPN, заменяющий текущую Telegram-only реализацию. Полный стек: от захода пользователя на лендинг → просмотра информации → авторизации → оплаты → выдачи ключа → личного кабинета с просмотром подписки/ключей.

Это **первая фаза (MVP)** более крупной платформы. Рефералка, триал-бонусы, форточка (fortune/giveaway), админ-панель — в последующих фазах.

### Зафиксированные продуктовые решения

| Решение | Выбор |
|---|---|
| Авторизация | **Только Telegram** (Login Widget, проверка hash-подписи на бэке) |
| Платежи | **CryptoBot (Crypto Pay API)** — USDT/BTC/TON, оплата в крипте |
| Платформа | **Отдельный сайт на домене** (обычная вкладка браузера) |
| Фронтенд-стек | **React 18 + Vite + TypeScript** |
| Архитектура | **Подход A** — модульный монолит: backend (FastAPI JSON-API) + frontend (React SPA), monorepo |
| Визуальный стиль | **Clean Modern SaaS + Frosted Glassmorphism**, aurora-фон (индиго→голубой) |
| Тарифы | **3-ступенчатые**: 1 мес (199₽) / 3 мес (499₽, −16%) / 1 год (1490₽, −38%) |
| Устройства | **Без лимита** — один ключ ставится на любое число устройств |
| Модель ключа | **Подписочная**: одна подписка → конфиг на каждый из 4 серверов → единый sub-URL |
| Сервера | **4 сервера** (конфиги предоставит пользователь позже), 1 Гбит/чел |
| База данных | **SQLite + WAL** |
| Скоп фазы 1 | Ядро пути + **промокоды** на скидку |

### Отложено на следующие фазы
- Реферальная программа (бонусы за приглашения)
- Триал/приветственный бонус новым юзерам
- Форточка (fortune wheel), розыгрыши (giveaways)
- Админ-панель (HTML-шаблоны старой админки не переносим)
- Webhook от CryptoBot (стартуем с поллинга, заложим место под webhook)

---

## 2. Модель данных (SQLite)

7 основных таблиц. Лучшая практика перенесена из старого `onefile_vpn.py`.

### users
| Поле | Тип | Описание |
|---|---|---|
| id | int PK | |
| telegram_id | int, unique, index | ключевой идентификатор |
| username | str? | из Telegram |
| subscription_until | datetime? | NULL = нет активной подписки |
| balance_rub | int, default 0 | внутренний баланс, в рублях |
| created_at / updated_at | datetime | |

### vpn_servers (4 записи)
| Поле | Тип | Описание |
|---|---|---|
| id | int PK | |
| name | str, unique | отображаемое ("Германия") |
| protocol | str | `vless_reality` \| `hysteria2`, index |
| host / port / sni | str/int/str | соединение |
| public_key / short_id / fingerprint | str | VLESS-Reality параметры |
| hy2_obfs / hy2_obfs_password / hy2_alpn / hy2_insecure | | Hysteria2 параметры |
| ssh_host / ssh_port / ssh_user / ssh_key_path | | SSH-доступ для провижнинга |
| remote_add_script / remote_remove_script | str | пути к скриптам на сервере |
| enabled | bool, default true | |

### client_configs
По строке на **сервер × пользователь**. Это реализует подписочную модель.
| Поле | Тип | Описание |
|---|---|---|
| id | int PK | |
| user_id | FK users | index |
| server_id | FK vpn_servers | index |
| client_uuid | str(36), unique, index | для VLESS |
| client_secret | str | пароль для Hysteria2 |
| connection_url | text | итоговая vless:// или hy2:// ссылка |
| is_active | bool, default true, index | |
| created_at / revoked_at | datetime? | |

> **Ключевое отличие от старого:** создаётся по конфигу на каждый сервер (4 строки на юзера при активации), а не одно устройство = один конфиг.

### subscription_tokens
Выделена в отдельную таблицу для гибкости (ротация токена без трогания юзера).
| Поле | Тип | Описание |
|---|---|---|
| id | int PK | |
| user_id | FK users | unique (один активный токен на юзера) |
| token | str, unique | `secrets.token_urlsafe(32)` |
| created_at | datetime | |

### payment_invoices
| Поле | Тип | Описание |
|---|---|---|
| id | int PK | |
| invoice_id | int, unique, index | ID из CryptoBot |
| invoice_hash | str, unique, index | |
| user_id | FK users | index |
| amount_rub / payable_rub / months / kind | | `kind`: topup \| purchase |
| promo_code_text / promo_discount_percent | | применённый промокод |
| pay_url | text | от CryptoBot |
| status | str, index | active \| paid \| expired \| cancelled |
| idempotency_key | str? index | |
| created_at / paid_at | datetime? | |

### promo_codes / promo_redemptions
Переносятся как есть из старого проекта. `kind` (discount), `value_int`, `max_uses_total/per_user`, `starts_at/ends_at`, `enabled`.

**Семантика промокода (уточнено по старому коду):** промокод задаёт **процент скидки** (`value_int` = 1–95). При создании счёта: `payable_rub = max(1, round(amount_rub * (100 - percent) / 100))`. `kind = "topup_discount_percent"`. Один промокод привязывается к счёту (`promo_code_text` + `promo_discount_percent`), redeem-запись создаётся после успешной оплаты.

---

## 3. Backend API (FastAPI)

Чистое JSON-API. Авторизация: после TG-логина выдаётся **JWT в httpOnly cookie** (SameSite=Lax, защита от XSS-кражи). Фронт шлёт запросы с `credentials: 'include'`.

### Эндпоинты

```
АВТОРИЗАЦИЯ
POST /api/auth/telegram              приём Login Widget payload → проверка hash → JWT cookie
GET  /api/auth/me                    текущий пользователь (по JWT)
POST /api/auth/logout                очистка cookie

ПУБЛИЧНОЕ (без авторизации)
GET  /api/public/config              данные для лендинга (фичи, метрики)
GET  /api/plans                      3 тарифа: [{id, title, months, price_rub, discount_percent}]

ОПЛАТА (требует авторизации)
POST /api/payments/create            body: {plan_id, promo_code?} → {invoice_id, pay_url}
GET  /api/payments/status/{id}       статус счёта (фронт поллит каждые 3с)
GET  /api/payments/history           история платежей юзера

КАБИНЕТ (требует авторизации)
GET  /api/cabinet/me                 состояние подписки
GET  /api/cabinet/keys               все конфиги + sub-URL + QR-данные
POST /api/cabinet/keys/regenerate    перевыпуск ключей (ротация uuid/secret)
POST /api/cabinet/redeem-promo       применить промокод отдельно от покупки

ПОДПИСКА (публичный, по токену)
GET  /sub/{telegram_id}/{token}      base64 всех активных конфигов юзера
GET  /sub/{telegram_id}/{token}?preview   HTML-превью для браузера
```

### Поток оплаты (ключевая логика)

```
1. Фронт: юзер выбрал тариф → POST /payments/create {plan_id, promo?}
2. Бэк: создаёт PaymentInvoice, вызывает CryptoBot createInvoice API
        → получает pay_url, сохраняет, возвращает {pay_url, invoice_id}
3. Фронт: редирект/новая вкладка на pay_url
4. Фронт: параллельно поллит GET /payments/status/{invoice_id} каждые 3с
5. Бэк: при проверке дёргает CryptoBot getInvoices → если paid:
        → активирует подписку (subscription_until += months)
        → создаёт 4 client_configs (по серверу) + subscription_token
        → провижнит юзера на серверах по SSH (add_vless/add_hy2)
        → invoice.status = paid, paid_at = now
6. Фронт: видит status=paid → редирект на /cabinet → показывает ключи
```

**Webhook от CryptoBot:** стартуем с поллинга (домен не обязателен). В коде закладываем место под webhook-эндпоинт — включим, когда будет домен с HTTPS.

### Перенос из старого `onefile_vpn.py` (без изменения логики)
- `build_vless_url()`, `build_hysteria2_url()`, `build_client_url()` — генерация ссылок
- `/sub/...` base64-сборка подписки
- `add_vless_client()`, `add_hysteria2_client()`, `remove_*_client()` — SSH-провижнинг (paramiko)
- Проверка подписи Telegram (`data_check_string` + HMAC-SHA256)
- Интеграция CryptoBot (createInvoice/getInvoices)

---

## 4. Фронтенд (React + Vite + TS)

SPA, react-router-dom.

### Страницы

```
/                  Лендинг (hero, тарифы, поток ключа, стек, FAQ-аккордеон)
/login             Telegram Login Widget (редирект сюда если не авторизован)
/checkout/:planId  оформление: тариф + поле промокода → "Оплатить"
/pay/:invoiceId    ожидание оплаты (поллинг, ссылка на pay_url в новой вкладке)
/cabinet           ЛИЧНЫЙ КАБИНЕТ (защищён):
                   · статус подписки + до какого числа (прогресс-бар)
                   · блок "Ваш ключ": sub-URL + QR + "Скопировать" / "Импорт в HAPP/Hiddify"
                   · список 4 конфигов (по серверу) с раскрытием ссылок
                   · история платежей
                   · "Продлить" / "Купить" если нет подписки
```

### Дизайн-система (Frosted Glass)
- **Палитра:** фон `#08090d`, aurora-блобы (индиго `#a5b4fc`, фиолет `#c4b5fd`, голубой `#7dd3fc`), текст `#fafafa` / `#a1a1aa`
- **Стеклянные компоненты:** `.glass-card`, `.glass-input`, `.glass-button` — `backdrop-filter: blur()`, полупрозрачная заливка `rgba(255,255,255,0.06)`, тонкая граница `rgba(255,255,255,0.13)`
- **Кнопки:** primary (белая/градиент), ghost (стекло), ховер — лёгкое свечение
- **QR-код:** библиотека `qrcode`, генерация на клиенте из sub-URL
- **Telegram Login Widget:** `telegram.org/js/telegram-widget.js`, стилизуем под сайт

### Технологии
- React 18, react-router-dom 6, TypeScript 5, Vite 5
- HTTP-клиент: обёртка над fetch с `credentials: 'include'`
- QR: `qrcode` пакет
- Иконки: кастомные (создаются отдельно после сайта)

---

## 5. Поток выдачи ключа (детально)

Сердце системы — доступ к 4 серверам через одну ссылку.

### Активация после оплаты
```
1. payment.status → paid
2. Для КАЖДОГО из 4 серверов:
   · VLESS-Reality: генерируем UUID → build_vless_url() → ClientConfig
   · Hysteria2:     генерируем пароль → build_hysteria2_url() → ClientConfig
   · По SSH: add_vless_client / add_hysteria2_client на сервере
3. Генерируем subscription_token (один на юзера) → subscription_tokens
4. sub-URL = https://domain/sub/{telegram_id}/{token}
```

### Что видит пользователь в кабинете
- Большой блок с **sub-URL + QR** ("ключ на все устройства")
- Кнопки: "Скопировать ссылку", "Открыть в HAPP" (deep-link/инструкция), "Открыть в Hiddify", "Показать отдельные конфиги"
- Импорт = вставить sub-URL в приложение → подтягиваются все 4 сервера, юзер переключается между ними в приложении

### Что отдаёт /sub/{telegram_id}/{token}
- `base64( "vless://...\nvless://...\nhy2://...\nvless://..." )`
- Все активные конфиги юзера через `\n`, закодированные в base64
- HAPP/Hiddify парсят как multi-config подписку

### Продление
Тот же тариф продлевает `subscription_until += months`, ключи остаются те же (без перегенерации — юзер не переподключает устройства). Если подписка истекла и ключи отозваны на серверах — при продлении перевыпускаем/переподключаем.

---

## 6. Безопасность

- **TG-подпись:** проверка на бэке по `data_check_string` + HMAC-SHA256 с bot_token
- **Сессия:** JWT в httpOnly cookie, SameSite=Lax (защита от XSS-кражи)
- **subscription_token:** криптослучайный (`secrets.token_urlsafe(32)`), неугадываемый
- **CryptoBot:** сверка по `invoice_id` + `invoice_hash`, idempotency_key против дублей
- **Rate-limit:** на `/api/auth/telegram` и `/api/payments/create` (защита от спама/bruteforce промокодов)
- **Секреты:** `.env`, никогда в коде. JWT-секрет, CryptoBot token, TG bot_token
- **Авторизация кабинета:** проверка `subscription_until` на бэке при каждом запросе

---

## 7. Деплой

```
nginx (443, TLS) → /api/*  проксирует на FastAPI (127.0.0.1:8000)
                 → /sub/*  проксирует на FastAPI
                 → остальное = собранный React (frontend/dist)
FastAPI          systemd-сервис, uvicorn, SQLite WAL
```

Структура monorepo:
```
vpnwebsite/
├─ backend/   (Python, FastAPI)
├─ frontend/  (React, Vite, TS)
├─ deploy/    (nginx.conf, trumpvpn.service, install scripts)
├─ docs/      (design specs)
└─ .env.example
```

### Перенос из старого проекта
Переносим: протоколы (`build_*_url`, SSH-провижнинг), модели БД, TG-auth, CryptoBot. Переупаковываем в модульную структуру. HTML-шаблоны админки — не переносим.

---

## 8. Границы фазы 1 (MVP)

**Входит:**
- Лендинг с frosted-glass дизайном
- TG-авторизация (Login Widget)
- 3 тарифа, оплата через CryptoBot (поллинг статуса)
- **Промокоды** на скидку при покупке
- Активация подписки → 4 конфига → единый sub-URL
- Личный кабинет: статус подписки, sub-URL + QR, список конфигов, история платежей
- SSH-провижнинг на 4 сервера
- Деплой через nginx + systemd

**Не входит (следующие фазы):**
- Реферальная программа
- Триал / приветственный бонус
- Форточка (fortune), розыгрыши (giveaways)
- Админ-панель
- CryptoBot webhook
