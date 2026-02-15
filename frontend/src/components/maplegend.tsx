import { Info } from "lucide-react";
import type React from "react";

export default function MapLegend() {
  return (
    <div style={legend}>
      <div style={header}>
        <Info size={16} />
        <span>Safety Legend</span>
      </div>

      <div style={itemsRow}>
        <LegendItem color="#22c55e" label="Safe" />
        <LegendItem color="#eab308" label="Moderate" />
        <LegendItem color="#f97316" label="Caution" />
        <LegendItem color="#ef4444" label="Avoid" />
      </div>
    </div>
  );
}

function LegendItem({ color, label }: { color: string; label: string }) {
  return (
    <div style={item}>
      <div
        style={{
          ...pill,
          background: color,
          boxShadow: `0 0 14px ${color}55`,
        }}
      />
      <span style={labelStyle}>{label}</span>
    </div>
  );
}

/* -------- styles -------- */
const legend: React.CSSProperties = {
  position: "absolute",
  bottom: 22,
  left: 1700,
  padding: "16px 18px",
  borderRadius: 18,
  background: "rgba(15, 23, 42, 0.65)",
  border: "1px solid rgba(255,255,255,0.14)",
  backdropFilter: "blur(14px)",
  boxShadow: "0 20px 45px rgba(0,0,0,0.4)",
  color: "white",
  zIndex: 25,
  display: "flex",
  flexDirection: "column",
  gap: 14,
  minWidth: 360,
};

const header: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: 8,
  fontWeight: 900,
  fontSize: 14,
  opacity: 0.85,
};

const itemsRow: React.CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  gap: 16,
};

const item: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: 8,
};

const pill: React.CSSProperties = {
  width: 20,
  height: 20,
  borderRadius: 999,
};

const labelStyle: React.CSSProperties = {
  fontSize: 13,
  fontWeight: 700,
};
