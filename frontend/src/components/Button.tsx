import type { ButtonHTMLAttributes, ReactNode } from "react";

type Variant = "primary" | "ghost" | "danger";

const base: React.CSSProperties = {
  padding: "11px 24px",
  borderRadius: 11,
  fontWeight: 600,
  fontSize: 14,
  transition: "transform .12s ease, box-shadow .18s ease, background .18s ease, border-color .18s ease, opacity .15s ease",
  position: "relative" as const,
  cursor: "pointer",
};

const variants: Record<Variant, React.CSSProperties> = {
  primary: {
    background: "linear-gradient(180deg, rgba(255,255,255,0.16), rgba(255,255,255,0.10))",
    border: "1px solid rgba(255,255,255,0.28)",
    color: "#fff",
    backdropFilter: "blur(14px)",
  },
  ghost: {
    background: "transparent",
    border: "1px solid var(--glass-border)",
    color: "var(--muted)",
  },
  danger: {
    background: "rgba(239,68,68,0.15)",
    border: "1px solid rgba(239,68,68,0.4)",
    color: "#fca5a5",
  },
};

const hoverBg: Record<Variant, string> = {
  primary: "linear-gradient(180deg, rgba(255,255,255,0.24), rgba(165,180,252,0.18))",
  ghost: "rgba(255,255,255,0.07)",
  danger: "rgba(239,68,68,0.25)",
};

export function Button({
  variant = "primary",
  children,
  style,
  onMouseEnter,
  onMouseLeave,
  onMouseDown,
  disabled,
  ...rest
}: { variant?: Variant; children: ReactNode } & ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      {...rest}
      disabled={disabled}
      onMouseEnter={(e) => {
        if (!disabled) e.currentTarget.style.background = hoverBg[variant];
        onMouseEnter?.(e);
      }}
      onMouseLeave={(e) => {
        if (!disabled) {
          e.currentTarget.style.background = (variants[variant].background as string) ?? "";
          e.currentTarget.style.transform = "";
          e.currentTarget.style.boxShadow = "";
        }
        onMouseLeave?.(e);
      }}
      onMouseDown={(e) => {
        if (!disabled) e.currentTarget.style.transform = "translateY(1px) scale(0.985)";
        onMouseDown?.(e);
      }}
      style={{
        ...base,
        ...variants[variant],
        opacity: disabled ? 0.5 : 1,
        cursor: disabled ? "not-allowed" : "pointer",
        boxShadow: disabled ? "none" : "0 6px 20px rgba(139,155,255,0.10)",
        ...style,
      }}
    >
      {children}
    </button>
  );
}
