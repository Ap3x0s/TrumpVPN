import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api, type Plan, type PaymentCreated } from "../lib/api";
import { ROUTES } from "../lib/routes";
import { GlassCard } from "../components/GlassCard";
import { Button } from "../components/Button";
import { Spinner } from "../components/Spinner";

export function Checkout() {
  const { planId } = useParams();
  const nav = useNavigate();
  const [plan, setPlan] = useState<Plan | null>(null);
  const [promo, setPromo] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.get<Plan[]>("/api/plans").then((all) => setPlan(all.find((p) => p.id === planId) ?? null));
  }, [planId]);

  async function pay() {
    if (!plan) return;
    setBusy(true);
    setError(null);
    try {
      const res = await api.post<PaymentCreated>("/api/payments/create", { plan_id: plan.id, promo_code: promo || undefined });
      nav(ROUTES.pay(res.invoice_id), { state: { pay_url: res.pay_url } });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось создать счёт");
      setBusy(false);
    }
  }

  if (!plan) return <div className="container" style={{ paddingTop: 80, textAlign: "center" }}><Spinner /></div>;

  return (
    <div className="container" style={{ display: "flex", justifyContent: "center", paddingTop: 60 }}>
      <GlassCard style={{ width: 420 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 4 }}>Оформление</h1>
        <p className="muted" style={{ fontSize: 14, marginBottom: 20 }}>Тариф: <b style={{ color: "#fafafa" }}>{plan.title}</b> — {plan.price_rub} ₽</p>

        <label className="dim" style={{ fontSize: 12 }}>Промокод</label>
        <input
          value={promo}
          onChange={(e) => setPromo(e.target.value.toUpperCase())}
          placeholder="WELCOME10"
          className="glass"
          style={{ width: "100%", padding: "11px 14px", marginTop: 6, marginBottom: 18, color: "#fff", fontSize: 14, outline: "none" }}
        />

        {error && <p style={{ color: "#fca5a5", fontSize: 13, marginBottom: 14 }}>{error}</p>}
        <Button style={{ width: "100%" }} disabled={busy} onClick={pay}>{busy ? "Создаём счёт..." : `Оплатить ${plan.price_rub} ₽`}</Button>
        <p className="dim" style={{ fontSize: 12, marginTop: 14, textAlign: "center" }}>Оплата криптой (USDT/BTC/TON) через CryptoBot.</p>
      </GlassCard>
    </div>
  );
}
