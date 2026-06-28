"""TrumpVPN login bot.

A small aiogram bot whose only job is magic-link login:
  user -> /start (or /login) -> bot asks backend for a one-time token
       -> bot sends an inline button linking to the website
       -> website exchanges the token for a session.

Run separately from the backend:
    python -m bot   (reads BOT_TOKEN, BOT_AUTH_TOKEN, BACKEND_URL, SITE_URL from env)
"""
import os

import httpx
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Load .env from the bot/ directory if python-dotenv is available.
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
except Exception:
    pass

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000").rstrip("/")
SITE_URL = os.environ.get("SITE_URL", "http://localhost:5173").rstrip("/")
BOT_AUTH_TOKEN = os.environ.get("BOT_AUTH_TOKEN", "")

bot = Bot(BOT_TOKEN)
dp = Dispatcher()


async def _issue_token(telegram_id: int, username: str | None) -> str | None:
    """Ask the backend to mint a one-time login token. Returns token or None."""
    params: dict[str, str] = {"telegram_id": str(telegram_id)}
    if username:
        params["username"] = username
    headers = {"X-Bot-Token": BOT_AUTH_TOKEN}
    try:
        r = await httpx.AsyncClient().get(
            f"{BACKEND_URL}/api/auth/issue-token",
            params=params,
            headers=headers,
            timeout=10.0,
        )
    except Exception:
        return None
    if r.status_code != 200:
        return None
    data = r.json()
    return data.get("token")


def _login_button(token: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="🔐 Открыть личный кабинет", url=f"{SITE_URL}/login?token={token}"))
    return kb.as_markup()


@dp.message(Command("start", "login"))
async def start(message: Message) -> None:
    if not BOT_AUTH_TOKEN:
        await message.answer("⚠️ Бот не настроен (BOT_AUTH_TOKEN отсутствует). Обратитесь к администратору.")
        return
    user = message.from_user
    token = await _issue_token(user.id, user.username)
    if not token:
        await message.answer("⚠️ Не удалось создать ссылку для входа. Попробуйте позже.")
        return
    await message.answer(
        "👋 Привет! Нажмите кнопку ниже, чтобы открыть личный кабинет TrumpVPN.\n\n"
        "Ссылка одноразовая и действует 10 минут.",
        reply_markup=_login_button(token),
    )


@dp.message(F.text)
async def fallback(message: Message) -> None:
    await message.answer("Напишите /login, чтобы войти в личный кабинет TrumpVPN.")


async def main() -> None:
    if not BOT_TOKEN:
        raise SystemExit("BOT_TOKEN env var is required")
    print(f"[bot] polling started | backend={BACKEND_URL} site={SITE_URL}")
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
