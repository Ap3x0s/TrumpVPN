import { useEffect, useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import { api, type PaymentStatus } from "../lib/api";
import { ROUTES } from "../lib/routes";
import { GlassCard } from "../components/GlassCard";
import { Button } from "../components/Button";
import { Spinner } from "../components/Spinner";

export function Pay() {
  const { invoiceId } = useParams();
  const nav = useNavigate();
  const location = useLocation();
  const payUrl = (location.state as { pay_url?: string } | null)?.pay_url ?? "";
  const [status, setStatus] = useState<string>("active");

  useEffect(() => {
    if (!invoiceId) return;
    let stop = false;
    const poll = async () => {
      while (!stop) {
        try {
          const s = await api.get<PaymentStatus>(`/api/payments/status/${invoiceId}`);
          setStatus(s.status);
          if (s.paid) { nav(ROUTES.cabinet, { replace: true }); return; }
        } catch { /* keep polling */ }
        await new Promise((r) => setTimeout(r, 3000));
      }
    };
    poll();
    return () => { stop = true; };
  }, [invoiceId, nav]);

  function openPay() {
    if (payUrl) window.open(payUrl, "_blank", "noopener");
  }

  return (
    <div className="container" style={{ display: "flex", justifyContent: "center", paddingTop: 80 }}>
      <GlassCard style={{ width: 420, textAlign: "center" }}>
        <Spinner />
        <h1 style={{ fontSize: 22, fontWeight: 700, margin: "16px 0 6px" }}>Ожидаем оплату</h1>
        <p className="muted" style={{ fontSize: 14, marginBottom: 20 }}>Статус: {status === "paid" ? "оплачено" : "ожидание..."}</p>
        <p className="dim" style={{ fontSize: 13, marginBottom: 18 }}>Завершите платёж в окне CryptoBot. Мы проверим оплату автоматически.</p>
        {payUrl && <Button variant="ghost" onClick={openPay}>Открыть окно оплаты снова</Button>}
      </GlassCard>
    </div>
  );
}
