import { Flame, Shield, RotateCcw  } from "lucide-react";

type Props = {
  showHeatmap: boolean;
  toggleHeatmap: () => void;
  onShowNearbySafe: () => void;
  onResetRoute: () => void;
};

export default function MapHeader({
  showHeatmap,
  toggleHeatmap,
  onShowNearbySafe,
  onResetRoute
}: Props) {
  return (
    <div style={wrap}>
      <button
        onClick={toggleHeatmap}
        style={pill(showHeatmap, "heat")}
      >
        <Flame size={16} />
        {showHeatmap ? "Heatmap On" : "Heatmap"}
      </button>

      <button
        onClick={onShowNearbySafe}
        style={pill(false, "safe")}
      >
        <Shield size={16} />
        Nearby Safe
      </button>

      <button
        onClick={onResetRoute}
        style={pill(false, "reset")}
      >
        <RotateCcw size={16} />
        Reset Route
      </button>


    </div>
  );
}

/* ---------------- STYLES ---------------- */


const wrap: React.CSSProperties = {
  position: "absolute",
  top: 40,
  left: 2000,
  transform: "translateX(-100%)",
  display: "flex",
  gap: 12,
  padding: 8,
  borderRadius: 16,
  backdropFilter: "blur(12px)",
  background: "rgba(15, 23, 42, 0.55)",
  border: "1px solid rgba(255,255,255,0.12)",
  boxShadow: "0 18px 40px rgba(0,0,0,0.35)",
  zIndex: 20,
};

const pill = (
  active: boolean,
  tone: "heat" | "safe" | "reset"
): React.CSSProperties => {
  const base: React.CSSProperties = {
    display: "inline-flex",
    alignItems: "center",
    gap: 8,
    padding: "10px 14px",
    borderRadius: 14,
    fontWeight: 800,
    fontSize: 13,
    cursor: "pointer",
    border: "1px solid rgba(255,255,255,0.12)",
    background: "rgba(255,255,255,0.08)",
    color: "white",
    transition: "all 0.2s ease",
    whiteSpace: "nowrap",
  };

  if (!active && tone !== "reset") return base;

  if (tone === "heat") {
    return {
      ...base,
      background: "rgba(239,68,68,0.85)",
      border: "1px solid rgba(239,68,68,0.9)",
      boxShadow: "0 12px 30px rgba(239,68,68,0.25)",
    };
  }

  if (tone === "safe" && active) {
    return {
      ...base,
      background: "rgba(34,197,94,0.85)",
      border: "1px solid rgba(34,197,94,0.9)",
      boxShadow: "0 12px 30px rgba(34,197,94,0.25)",
    };
  }

  if (tone === "reset") {
    return {
      ...base,
      background: "rgba(59,130,246,0.85)",
      border: "1px solid rgba(59,130,246,0.9)",
      boxShadow: "0 12px 30px rgba(59,130,246,0.25)",
    };
  }

  return base
};
