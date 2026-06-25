import { useState } from "react";

type Item = { q: string; a: string };
export function FAQ({ items }: { items: Item[] }) {
  const [open, setOpen] = useState<number | null>(0);
  return (
    <div style={{ display: "grid", gap: 10 }}>
      {items.map((it, i) => (
        <div key={i} className="glass" style={{ padding: "14px 18px", cursor: "pointer" }} onClick={() => setOpen(open === i ? null : i)}>
          <div style={{ display: "flex", justifyContent: "space-between", fontWeight: 600, fontSize: 14 }}>{it.q}<span style={{ color: "#a1a1aa" }}>{open === i ? "−" : "+"}</span></div>
          {open === i && <p className="muted" style={{ marginTop: 8, fontSize: 13, lineHeight: 1.5 }}>{it.a}</p>}
        </div>
      ))}
    </div>
  );
}
