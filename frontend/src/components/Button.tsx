import type { ButtonHTMLAttributes, ReactNode } from "react";

type Variant = "primary" | "ghost" | "danger";
const styles: Record<Variant, React.CSSProperties> = {
  primary: { background: "rgba(255,255,255,0.12)", border: "1px solid rgba(255,255,255,0.28)", color: "#fff", backdropFilter: "blur(14px)" },
  ghost: { background: "transparent", border: "1px solid var(--glass-border)", color: "var(--muted)" },
  danger: { background: "rgba(239,68,68,0.15)", border: "1px solid rgba(239,68,68,0.4)", color: "#fca5a5" },
};

export function Button({ variant = "primary", children, style, ...rest }: { variant?: Variant; children: ReactNode } & ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      {...rest}
      style={{ padding: "11px 24px", borderRadius: 11, fontWeight: 600, fontSize: 14, transition: "all .15s ease", ...styles[variant], ...style }}
    >
      {children}
    </button>
  );
}
