import { useEffect, useState } from "react";
import QRCode from "qrcode";
import { Link } from "react-router-dom";
import { api, type CabinetKeys, type Me, type PaymentHistoryItem, type Plan } from "../lib/api";
import { ROUTES } from "../lib/routes";
import { GlassCard } from "../components/GlassCard";
import { Button } from "../components/Button";
import { Logo } from "../components/Logo";

export function Cabinet() {
  const [me, setMe] = useState<Me | null>(null);
  const [keys, setKeys] = useState<CabinetKeys | null>(null);
  const [hist, setHist] = useState<PaymentHistoryItem[]>([]);
  const [plans, setPlans] = useState<Plan[]>([]);
  const [qr, setQr] = useState<string>("");
  const [copied, setCopied] = useState(false);
  const [showConfigs, setShowConfigs] = useState(false);

  useEffect(() => {
    api.get<Me>("/api/auth/me").then(setMe);
    api.get<CabinetKeys>("/api/cabinet/keys").then(async (k) => {
      setKeys(k);
      if (k.subscription_url) setQr(await QRCode.toDataURL(k.subscription_url, { margin: 1, width: 220, color: { dark: "#0a0c10", light: "#ffffff" } }));
    });
    api.get<PaymentHistoryItem[]>("/api/payments/history").then(setHist);
    api.get<Plan[]>("/api/plans").then(setPlans);
  }, []);

  function copy() {
    if (!keys?.subscription_url) return;
    navigator.clipboard.writeText(keys.subscription_url);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  function logout() {
    api.post("/api/auth/logout").then(() => (window.location.href = ROUTES.landing));
  }

  const active = !!me?.subscription_until && new Date(me.subscription_until) > new Date();

  return (
    <div className="container" style={{ paddingBottom: 80 }}>
      {/* NAV: clickable logo -> home, plus home + logout */}
      <nav style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "22px 0" }}>
        <Link to={ROUTES.landing} style={{ display: "flex", alignItems: "center" }}><Logo /></Link>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <Link to={ROUTES.landing}><Button variant="ghost">На главную</Button></Link>
          <Button variant="ghost" onClick={logout}>Выйти</Button>
        </div>
      </nav>

      <h1 style={{ fontSize: 28, fontWeight: 700, letterSpacing: "-0.5px", marginBottom: 18 }}>
        Личный кабинет
      </h1>

      <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: 16, maxWidth: 680, margin: "0 auto" }}>
        {/* ACCOUNT INFO */}
        <GlassCard>
          <h2 style={{ fontSize: 16, fontWeight: 700, marginBottom: 12, color: "var(--muted)" }}>Аккаунт</h2>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 12 }}>
            <div>
              <div className="dim" style={{ fontSize: 11, marginBottom: 2 }}>Telegram ID</div>
              <div style={{ fontSize: 14, fontFamily: "ui-monospace, monospace" }}>{me?.telegram_id ?? "—"}</div>
            </div>
            <div>
              <div className="dim" style={{ fontSize: 11, marginBottom: 2 }}>Имя пользователя</div>
              <div style={{ fontSize: 14 }}>@{me?.username ?? "—"}</div>
            </div>
            <div>
              <div className="dim" style={{ fontSize: 11, marginBottom: 2 }}>Баланс</div>
              <div style={{ fontSize: 14 }}>{me?.balance_rub ?? 0} ₽</div>
            </div>
          </div>
        </GlassCard>

        {/* SUBSCRIPTION STATUS */}
        <GlassCard>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
            <h2 style={{ fontSize: 18, fontWeight: 700 }}>Подписка</h2>
            <span style={{ fontSize: 12, padding: "4px 10px", borderRadius: 999, background: active ? "rgba(52,211,153,0.15)" : "rgba(113,113,122,0.15)", color: active ? "#34d399" : "#a1a1aa" }}>
              {active ? "● Активна" : "Неактивна"}
            </span>
          </div>
          {active && me ? (
            <>
              <p className="muted" style={{ fontSize: 14, marginBottom: 4 }}>
                Действует до <b style={{ color: "#fafafa" }}>{new Date(me.subscription_until!).toLocaleDateString("ru-RU")}</b>
              </p>
              <Link to={ROUTES.checkout("p1m")}><Button variant="ghost" style={{ marginTop: 10 }}>Продлить</Button></Link>
            </>
          ) : (
            <p className="muted" style={{ fontSize: 14 }}>У вас нет активной подписки. Выберите тариф ниже 👇</p>
          )}
        </GlassCard>

        {/* KEY + QR (only with active subscription) */}
        {active && keys?.subscription_url && (
          <GlassCard>
            <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 6 }}>Ваш ключ</h2>
            <p className="dim" style={{ fontSize: 13, marginBottom: 16 }}>Один ключ на все устройства. Вставьте эту ссылку в HAPP или Hiddify.</p>
            <div style={{ display: "flex", gap: 20, flexWrap: "wrap", alignItems: "center" }}>
              {qr && <img src={qr} alt="QR" style={{ borderRadius: 12, width: 180, height: 180 }} />}
              <div style={{ flex: 1, minWidth: 220 }}>
                <div className="glass" style={{ padding: 12, fontFamily: "ui-monospace, monospace", fontSize: 11, wordBreak: "break-all", color: "#86efac", marginBottom: 12 }}>
                  {keys.subscription_url}
                </div>
                <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                  <Button onClick={copy}>{copied ? "Скопировано!" : "Скопировать"}</Button>
                  <Button variant="ghost" onClick={() => setShowConfigs(!showConfigs)}>{showConfigs ? "Скрыть конфиги" : "Показать конфиги"}</Button>
                </div>
              </div>
            </div>
            {showConfigs && (
              <div style={{ marginTop: 16, display: "grid", gap: 8 }}>
                {keys.configs.map((c, i) => (
                  <div key={i} className="glass" style={{ padding: 10, fontSize: 11, fontFamily: "ui-monospace, monospace", color: "#a1a1aa", wordBreak: "break-all" }}>
                    <b style={{ color: "#c4b5fd" }}>{c.server}</b> · {c.protocol}<br />{c.url}
                  </div>
                ))}
              </div>
            )}
          </GlassCard>
        )}

        {/* PLANS — shown to users without subscription (conversion) */}
        {!active && (
          <GlassCard>
            <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 4 }}>Выбрать тариф</h2>
            <p className="dim" style={{ fontSize: 13, marginBottom: 18 }}>Оплата криптой. Ключ выдаётся мгновенно после оплаты.</p>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: 12 }}>
              {plans.map((p) => {
                const hot = p.discount_percent >= 30;
                return (
                  <div key={p.id} className="glass interactive" style={{ padding: 18, borderColor: hot ? "rgba(139,155,255,0.4)" : undefined, background: hot ? "rgba(139,155,255,0.10)" : undefined }}>
                    {hot && <div style={{ fontSize: 10, color: "#a5b4fc", fontWeight: 700, marginBottom: 6 }}>ВЫГОДНО</div>}
                    <div style={{ fontSize: 14, fontWeight: 600 }}>{p.title}</div>
                    <div style={{ fontSize: 24, fontWeight: 700, margin: "8px 0" }}>{p.price_rub} ₽</div>
                    <Link to={ROUTES.checkout(p.id)} style={{ display: "block" }}><Button style={{ width: "100%", padding: "8px 16px" }}>Выбрать</Button></Link>
                  </div>
                );
              })}
            </div>
          </GlassCard>
        )}

        {/* PAYMENT HISTORY */}
        <GlassCard>
          <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 12 }}>История платежей</h2>
          {hist.length === 0 ? <p className="dim" style={{ fontSize: 13 }}>Платежей пока нет.</p> : (
            <div style={{ display: "grid", gap: 8 }}>
              {hist.map((p) => (
                <div key={p.invoice_id} style={{ display: "flex", justifyContent: "space-between", fontSize: 13, padding: "8px 0", borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
                  <span>{p.payable_rub} ₽ · {p.months} мес</span>
                  <span style={{ color: p.status === "paid" ? "#34d399" : "#a1a1aa" }}>{p.status === "paid" ? "Оплачено" : p.status}</span>
                </div>
              ))}
            </div>
          )}
        </GlassCard>
      </div>
    </div>
  );
}
