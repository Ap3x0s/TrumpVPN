import type { ReactNode } from "react";

export function GlassCard({ children, className = "", style }: { children: ReactNode; className?: string; style?: React.CSSProperties }) {
  return <div className={`glass ${className}`} style={{ padding: 24, boxShadow: "var(--shadow)", ...style }}>{children}</div>;
}
