import { GlassCard } from "./components/GlassCard";
import { Button } from "./components/Button";
import { Logo } from "./components/Logo";

function App() {
  return (
    <div className="container" style={{ display: "flex", justifyContent: "center", paddingTop: 80 }}>
      <GlassCard style={{ width: 380, textAlign: "center" }}>
        <Logo />
        <h1 style={{ fontSize: 24, margin: "16px 0 6px", fontWeight: 700 }}>
          TrumpVPN <span className="gradient-text">design system</span>
        </h1>
        <p className="muted" style={{ fontSize: 14, marginBottom: 20 }}>Frosted glass scaffold ready. Routes land in the next task.</p>
        <Button>Primary</Button>{" "}
        <Button variant="ghost">Ghost</Button>
      </GlassCard>
    </div>
  );
}

export default App;
