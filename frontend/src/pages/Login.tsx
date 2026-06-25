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
    const bot = (import.meta as unknown as { env?: { VITE_TG_BOT_USERNAME?: string } }).env?.VITE_TG_BOT_USERNAME || "";
    if (bot) loadTelegramWidget("tg-login-container", bot, (user) => onTelegramUser(user as Record<string, unknown>));
  }, []);

  async function onTelegramUser(user: Record<string, unknown>) {
    setBusy(true);
    setError(null);
    try {
      await api.post("/api/auth/telegram", user);
      const me = await api.get<Me>("/api/auth/me");
      nav(me.subscription_until ? ROUTES.cabinet : ROUTES.landing, { replace: true });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка авторизации");
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
