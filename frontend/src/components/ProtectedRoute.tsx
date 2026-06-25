import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import { api, type Me } from "../lib/api";
import { ROUTES } from "../lib/routes";
import { Spinner } from "./Spinner";

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<"loading" | "ok" | "deny">("loading");
  useEffect(() => {
    api.get<Me>("/api/auth/me")
      .then(() => setState("ok"))
      .catch(() => setState("deny"));
  }, []);
  if (state === "loading") return <div style={{ paddingTop: 80, textAlign: "center" }}><Spinner /></div>;
  if (state === "deny") return <Navigate to={ROUTES.login} replace />;
  return <>{children}</>;
}
