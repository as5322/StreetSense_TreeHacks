import type React from "react";
import { Flame, Shield, X } from "lucide-react";

type Props = {
  heatmapOn: boolean;
  onToggleHeatmap: () => void;
  safeOn: boolean;
  onToggleSafe: () => void;
  onClear?: () => void;
};

export default function TopPills({ heatmapOn, onToggleHeatmap, safeOn, onToggleSafe, onClear }: Props) {
  return (
    <div style={wrap}>
      <button onClick={onToggleHeatmap} style={pill(heatmapOn, "blue")}>
        <Flame size={16} />
        Heatmap
      </button>
      <button onClick={onToggleSafe} style={pill(safeOn, "green")}>
        <Shield size={16} />
        Nearby Safe
      </button>
      {onClear && (
        <button onClick={onClear} style={pill(false, "neutral")}>
          <X size={16} />
          Clear
        </button>
      )}
    </div>
  );
}

const wrap: React.CSSProperties = {
  position: "absolute",
  top: 14,
  left: "50%",
  transform: "translateX(-50%)",
  display: "flex",
  gap: 10,
  padding: 8,
  borderRadius: 16,
  background: "rgba(15, 23, 42, 0.55)",
  border: "1px solid rgba(255,255,255,0.12)",
  backdropFilter: "blur(10px)",
  zIndex: 20,
};

const pill = (active: boolean, tone: "blue" | "green" | "neutral"): React.CSSProperties => {
  const base = {
    display: "inline-flex",
    alignItems: "center",
    gap: 8,
    padding: "10px 12px",
    borderRadius: 14,
    border: "1px solid rgba(255,255,255,0.12)",
    cursor: "pointer",
    fontWeight: 800,
    fontSize: 13,
    color: "white",
    background: "rgba(255,255,255,0.10)",
  } as React.CSSProperties;

  if (!active) return base;

  const bg =
    tone === "blue" ? "rgba(59,130,246,0.85)" :
    tone === "green" ? "rgba(34,197,94,0.85)" :
    "rgba(148,163,184,0.7)";

  return {
    ...base,
    background: bg,
    border: "1px solid rgba(255,255,255,0.18)",
    boxShadow: "0 12px 30px rgba(0,0,0,0.25)",
  };
};
