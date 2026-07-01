import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, type Me } from "../lib/api";
import { ROUTES } from "../lib/routes";
import { Button } from "./Button";

/**
 * Shows the right-hand nav auth affordance:
 * - logged in  -> "@username" linking to the cabinet
 * - logged out -> "Войти" button linking to /login
 *
 * Checks /api/auth/me on mount. Silent on failure (just shows Войти).
 */
export function NavUser() {
  const [me, setMe] = useState<Me | null>(null);
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    api
      .get<Me>("/api/auth/me")
      .then((user) => setMe(user))
      .catch(() => setMe(null))
      .finally(() => setChecked(true));
  }, []);

  if (!checked) return null; // avoid flicker; renders nothing until resolved
  if (!me) return <Link to={ROUTES.login}><Button variant="ghost">Войти</Button></Link>;

  return (
    <Link to={ROUTES.cabinet} className="nav-link" style={{ display: "inline-flex", alignItems: "center", gap: 8, padding: "6px 14px", fontSize: 14, borderRadius: 8 }}>
      <span style={{ width: 8, height: 8, borderRadius: "50%", background: "#34d399", boxShadow: "0 0 6px #34d399" }} />
      <span style={{ color: "var(--text)", fontWeight: 600 }}>@{me.username ?? me.telegram_id}</span>
    </Link>
  );
}
