import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { api, type Me } from "../lib/api";
import { loadTelegramWidget } from "../lib/telegram";
import { ROUTES } from "../lib/routes";
import { GlassCard } from "../components/GlassCard";
import { Spinner } from "../components/Spinner";
import { Logo } from "../components/Logo";
import { Button } from "../components/Button";

type View = "loading" | "form" | "error";

export function Login() {
  const nav = useNavigate();
  const [params] = useSearchParams();
  const [view, setView] = useState<View>("loading");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 1) If the URL has a magic-link token (from the bot's button), exchange it.
  useEffect(() => {
    const token = params.get("token");
    if (!token) {
      setView("form");
      return;
    }
    setBusy(true);
    api
      .post<Me>("/api/auth/exchange", { token })
      .then((me) => nav(me.subscription_until ? ROUTES.cabinet : ROUTES.cabinet, { replace: true }))
      .catch((e) => {
        setError(e instanceof Error ? e.message : "Ссылка входа недействительна или истекла.");
        setBusy(false);
        setView("error");
      });
  }, [params, nav]);

  // 2) If no token, mount the Telegram Login Widget as a fallback.
  useEffect(() => {
    if (view !== "form") return;
    const bot = (import.meta as unknown as { env?: { VITE_TG_BOT_USERNAME?: string } }).env?.VITE_TG_BOT_USERNAME || "";
    if (bot) loadTelegramWidget("tg-login-container", bot, (user) => onTelegramUser(user as Record<string, unknown>));
  }, [view]);

  async function onTelegramUser(user: Record<string, unknown>) {
    setBusy(true);
    setError(null);
    try {
      await api.post("/api/auth/telegram", user);
      const me = await api.get<Me>("/api/auth/me");
      nav(me.subscription_until ? ROUTES.cabinet : ROUTES.cabinet, { replace: true });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка авторизации");
      setBusy(false);
    }
  }

  function retry() {
    setError(null);
    setView("form");
  }

  // Loading state (magic-link exchange in progress)
  if (view === "loading" || busy) {
    return (
      <div className="container" style={{ display: "flex", justifyContent: "center", paddingTop: 80 }}>
        <GlassCard style={{ width: 380, textAlign: "center" }}>
          <Spinner />
          <p className="muted" style={{ fontSize: 14, marginTop: 16 }}>Выполняем вход…</p>
        </GlassCard>
      </div>
    );
  }

  // Error state (bad/expired token)
  if (view === "error") {
    return (
      <div className="container" style={{ display: "flex", justifyContent: "center", paddingTop: 80 }}>
        <GlassCard style={{ width: 380, textAlign: "center" }}>
          <Logo />
          <h1 style={{ fontSize: 22, margin: "16px 0 6px", fontWeight: 700 }}>Ссылка истекла</h1>
          {error && <p style={{ color: "#fca5a5", fontSize: 13, marginBottom: 16 }}>{error}</p>}
          <p className="muted" style={{ fontSize: 14, marginBottom: 18 }}>
            Откройте <b>@trumpvpn1bot</b> в Telegram и нажмите «Открыть личный кабинет», чтобы получить новую ссылку.
          </p>
          <Button variant="ghost" onClick={retry}>Назад</Button>
        </GlassCard>
      </div>
    );
  }

  // Form state — bot login is primary, widget is fallback
  return (
    <div className="container" style={{ display: "flex", justifyContent: "center", paddingTop: 80 }}>
      <GlassCard style={{ width: 380, textAlign: "center" }}>
        <Logo />
        <h1 style={{ fontSize: 24, margin: "16px 0 6px", fontWeight: 700 }}>Вход через Telegram</h1>
        <p className="muted" style={{ fontSize: 14, marginBottom: 16 }}>
          Авторизуйтесь через Telegram, чтобы купить и управлять подпиской.
        </p>

        {/* Primary: login via bot */}
        <div className="glass" style={{ padding: 16, marginBottom: 16, textAlign: "left" }}>
          <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 6 }}>💡 Проще всего:</div>
          <ol style={{ fontSize: 13, color: "var(--muted)", paddingLeft: 18, lineHeight: 1.6 }}>
            <li>Откройте <a href="https://t.me/trumpvpn1bot" target="_blank" rel="noopener" style={{ color: "var(--accent-1)" }}>@trumpvpn1bot</a> в Telegram</li>
            <li>Напишите <code>/login</code></li>
            <li>Нажмите кнопку «Открыть личный кабинет»</li>
          </ol>
        </div>

        {/* Fallback: Telegram Login Widget */}
        <div className="dim" style={{ fontSize: 12, marginBottom: 8 }}>Или войдите здесь:</div>
        <div id="tg-login-container" style={{ display: "flex", justifyContent: "center", minHeight: 52 }} />

        {error && <p style={{ color: "#fca5a5", fontSize: 13, marginTop: 16 }}>{error}</p>}
      </GlassCard>
    </div>
  );
}
