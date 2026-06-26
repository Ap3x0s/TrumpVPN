import { useEffect, useState } from "react";
import QRCode from "qrcode";
import { Link } from "react-router-dom";
import { api, type CabinetKeys, type Me, type PaymentHistoryItem } from "../lib/api";
import { ROUTES } from "../lib/routes";
import { GlassCard } from "../components/GlassCard";
import { Button } from "../components/Button";
import { Logo } from "../components/Logo";

export function Cabinet() {
  const [me, setMe] = useState<Me | null>(null);
  const [keys, setKeys] = useState<CabinetKeys | null>(null);
  const [hist, setHist] = useState<PaymentHistoryItem[]>([]);
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
  }, []);

  function copy() {
    if (!keys?.subscription_url) return;
    navigator.clipboard.writeText(keys.subscription_url);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  const active = !!me?.subscription_until && new Date(me.subscription_until) > new Date();

  return (
    <div className="container" style={{ paddingBottom: 80 }}>
      <nav style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "22px 0" }}>
        <Logo />
        <a href="/api/auth/logout" onClick={(e) => { e.preventDefault(); api.post("/api/auth/logout").then(() => (window.location.href = ROUTES.landing)); }}>
          <Button variant="ghost">Выйти</Button>
        </a>
      </nav>

      <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: 16, maxWidth: 620, margin: "0 auto" }}>
        <GlassCard>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
            <h2 style={{ fontSize: 18, fontWeight: 700 }}>Подписка</h2>
            <span style={{ fontSize: 12, padding: "4px 10px", borderRadius: 999, background: active ? "rgba(52,211,153,0.15)" : "rgba(113,113,122,0.15)", color: active ? "#34d399" : "#a1a1aa" }}>
              {active ? "Активна" : "Неактивна"}
            </span>
          </div>
          {active && me ? (
            <p className="muted" style={{ fontSize: 14 }}>Действует до <b style={{ color: "#fafafa" }}>{new Date(me.subscription_until!).toLocaleDateString("ru-RU")}</b></p>
          ) : (
            <div>
              <p className="muted" style={{ fontSize: 14, marginBottom: 12 }}>У вас нет активной подписки.</p>
              <Link to={ROUTES.checkout("p1m")}><Button>Купить подписку</Button></Link>
            </div>
          )}
        </GlassCard>

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
