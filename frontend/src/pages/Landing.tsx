import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, type Plan } from "../lib/api";
import { ROUTES } from "../lib/routes";
import { Button } from "../components/Button";
import { FAQ } from "../components/FAQ";
import { Logo } from "../components/Logo";
import { NavUser } from "../components/NavUser";

type PubConfig = { features: { icon: string; title: string; text: string }[]; metrics: Record<string, string>; faq: { q: string; a: string }[] };

export function Landing() {
  const [cfg, setCfg] = useState<PubConfig | null>(null);
  const [plans, setPlans] = useState<Plan[]>([]);
  useEffect(() => {
    api.get<PubConfig>("/api/public/config").then(setCfg);
    api.get<Plan[]>("/api/plans").then(setPlans);
  }, []);

  const scrollTo = (id: string) => {
    const el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  return (
    <div className="container" style={{ paddingBottom: 80 }}>
      <nav style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "22px 0" }}>
        <Logo />
        <div style={{ display: "flex", gap: 4, alignItems: "center" }}>
          <button type="button" className="muted nav-link" style={{ fontSize: 14, padding: "6px 14px", background: "transparent", border: "none" }} onClick={() => scrollTo("plans")}>Тарифы</button>
          <button type="button" className="muted nav-link" style={{ fontSize: 14, padding: "6px 14px", background: "transparent", border: "none" }} onClick={() => scrollTo("how")}>Как это работает</button>
          <NavUser />
        </div>
      </nav>

      <section style={{ textAlign: "center", padding: "40px 0 20px" }}>
        <div className="glass" style={{ display: "inline-flex", alignItems: "center", gap: 8, padding: "6px 14px", borderRadius: 999, fontSize: 12 }}>
          <span style={{ width: 7, height: 7, borderRadius: "50%", background: "#34d399", boxShadow: "0 0 8px #34d399" }} />
          <span className="muted">0 логов · Reality + Hysteria2</span>
        </div>
        <h1 style={{ fontSize: 44, fontWeight: 700, letterSpacing: "-1px", lineHeight: 1.1, margin: "16px 0 12px" }}>
          VPN, который <span className="gradient-text">просто работает</span>
        </h1>
        <p className="muted" style={{ fontSize: 16, maxWidth: 460, margin: "0 auto 22px", lineHeight: 1.6 }}>
          Подключение за 30 секунд. Платите криптой — ключ моментально. Импорт в HAPP и Hiddify в один тап.
        </p>
        <Link to={ROUTES.cabinet}><Button>Получить ключ →</Button></Link>
        <div style={{ display: "flex", gap: 26, justifyContent: "center", marginTop: 22, fontSize: 13 }}>
          <span className="dim"><b style={{ color: "#e4e4e7" }}>{cfg?.metrics.servers ?? 4}</b> сервера</span>
          <span className="dim"><b style={{ color: "#e4e4e7" }}>{cfg?.metrics.speed ?? "1 Гбит"}</b>/чел</span>
          <span className="dim"><b style={{ color: "#e4e4e7" }}>{cfg?.metrics.uptime ?? "99.9%"}</b> аптайм</span>
        </div>
      </section>

      <section id="plans" style={{ padding: "30px 0" }}>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 14 }}>
          {plans.map((p) => {
            const hot = p.discount_percent >= 30;
            return (
              <div key={p.id} className="glass interactive" style={{ padding: 24, borderColor: hot ? "rgba(139,155,255,0.4)" : undefined, background: hot ? "rgba(139,155,255,0.10)" : undefined }}>
                {hot && <div style={{ fontSize: 11, color: "#a5b4fc", fontWeight: 700, marginBottom: 8 }}>ВЫГОДНО</div>}
                <div style={{ fontSize: 15, fontWeight: 600 }}>{p.title}</div>
                <div style={{ fontSize: 30, fontWeight: 700, margin: "10px 0" }}>{p.price_rub} ₽</div>
                <div className="dim" style={{ fontSize: 13, marginBottom: 16 }}>{p.discount_percent > 0 ? `скидка ${p.discount_percent}%` : "стандарт"}</div>
                <Link to={ROUTES.checkout(p.id)} style={{ display: "block" }}><Button style={{ width: "100%" }}>Выбрать</Button></Link>
              </div>
            );
          })}
        </div>
      </section>

      <section id="how" style={{ padding: "20px 0 40px" }}>
        <h2 style={{ fontSize: 22, fontWeight: 700, textAlign: "center", marginBottom: 6 }}>От оплаты до подключения</h2>
        <p className="dim" style={{ textAlign: "center", marginBottom: 22, fontSize: 14 }}>Как ключ попадает в ваше приложение</p>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 14 }}>
          {[
            { step: "01", t: "Оплата криптой", d: "USDT, BTC, TON через CryptoBot. Безопасно и анонимно." },
            { step: "02", t: "Получение ключа", d: "Мгновенная выдача ссылки-подписки в личном кабинете." },
            { step: "03", t: "Импорт в приложение", d: "Один тап — и 4 сервера доступны в HAPP / Hiddify." },
          ].map((s) => (
            <div key={s.step} className="glass" style={{ padding: 20, textAlign: "center" }}>
              <div style={{ fontSize: 11, color: "#a5b4fc", letterSpacing: 1, fontWeight: 700 }}>ШАГ {s.step}</div>
              <h4 style={{ margin: "10px 0 6px", fontSize: 15 }}>{s.t}</h4>
              <p className="muted" style={{ fontSize: 13, lineHeight: 1.5 }}>{s.d}</p>
            </div>
          ))}
        </div>
      </section>

      <section style={{ padding: "10px 0 40px" }}>
        <h2 style={{ fontSize: 22, fontWeight: 700, textAlign: "center", marginBottom: 20 }}>Частые вопросы</h2>
        {cfg && <FAQ items={cfg.faq} />}
      </section>
    </div>
  );
}
