import type React from "react";

export const page: React.CSSProperties = {
  minHeight: "100vh",
  background: "#0b1220",
  color: "#e8eefc",
};

export const container: React.CSSProperties = {
  maxWidth: 980,
  margin: "0 auto",
  padding: "28px 18px 40px",
};

export const topBar: React.CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  gap: 12,
  marginBottom: 18,
};

export const titleWrap: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: 4,
};

export const title: React.CSSProperties = {
  fontSize: 26,
  fontWeight: 800,
  letterSpacing: "-0.02em",
  margin: 0,
};

export const subtitle: React.CSSProperties = {
  margin: 0,
  opacity: 0.8,
  fontSize: 13,
};

export const pill: React.CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  gap: 8,
  padding: "8px 12px",
  borderRadius: 999,
  background: "rgba(255,255,255,0.08)",
  border: "1px solid rgba(255,255,255,0.10)",
  fontSize: 13,
  color: "#e8eefc",
  textDecoration: "none",
};

export const tabs: React.CSSProperties = {
  display: "flex",
  gap: 10,
  padding: 6,
  borderRadius: 14,
  background: "rgba(255,255,255,0.06)",
  border: "1px solid rgba(255,255,255,0.10)",
  width: "fit-content",
  marginBottom: 18,
};

export const tab = (active: boolean): React.CSSProperties => ({
  padding: "10px 14px",
  borderRadius: 12,
  textDecoration: "none",
  color: active ? "#0b1220" : "#e8eefc",
  background: active ? "#e8eefc" : "transparent",
  fontWeight: 700,
  fontSize: 13,
  border: active ? "1px solid rgba(0,0,0,0.12)" : "1px solid transparent",
});

export const grid: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "1.3fr 0.7fr",
  gap: 18,
};

export const card: React.CSSProperties = {
  background: "rgba(255,255,255,0.06)",
  border: "1px solid rgba(255,255,255,0.10)",
  borderRadius: 18,
  padding: 16,
  boxShadow: "0 20px 50px rgba(0,0,0,0.35)",
};

export const cardTitle: React.CSSProperties = {
  margin: "0 0 10px",
  fontSize: 14,
  fontWeight: 800,
  opacity: 0.9,
};

export const composer: React.CSSProperties = {
  display: "flex",
  gap: 12,
  alignItems: "flex-start",
};

export const avatar: React.CSSProperties = {
  width: 38,
  height: 38,
  borderRadius: 999,
  background: "linear-gradient(135deg, #7c3aed, #22c55e)",
  flex: "0 0 auto",
};

export const textarea: React.CSSProperties = {
  width: "100%",
  minHeight: 78,
  resize: "vertical",
  padding: 12,
  borderRadius: 14,
  border: "1px solid rgba(255,255,255,0.14)",
  background: "rgba(0,0,0,0.25)",
  color: "#e8eefc",
  outline: "none",
  fontSize: 14,
  lineHeight: 1.4,
};

export const button: React.CSSProperties = {
  padding: "10px 14px",
  borderRadius: 12,
  border: "1px solid rgba(255,255,255,0.14)",
  background: "#e8eefc",
  color: "#0b1220",
  fontWeight: 800,
  cursor: "pointer",
  whiteSpace: "nowrap",
};

export const ghostButton: React.CSSProperties = {
  padding: "10px 14px",
  borderRadius: 12,
  border: "1px solid rgba(255,255,255,0.14)",
  background: "rgba(255,255,255,0.06)",
  color: "#e8eefc",
  fontWeight: 800,
  cursor: "pointer",
  whiteSpace: "nowrap",
};

export const postRow: React.CSSProperties = {
  display: "flex",
  gap: 12,
  padding: "12px 10px",
  borderRadius: 16,
  border: "1px solid rgba(255,255,255,0.10)",
  background: "rgba(0,0,0,0.18)",
};

export const postMeta: React.CSSProperties = {
  display: "flex",
  gap: 10,
  alignItems: "center",
  opacity: 0.75,
  fontSize: 12,
  marginTop: 6,
};

export const badge = (tone: "low" | "mod" | "high"): React.CSSProperties => {
  const map = {
    low: "rgba(34,197,94,0.18)",
    mod: "rgba(234,179,8,0.18)",
    high: "rgba(239,68,68,0.18)",
  } as const;

  return {
    padding: "6px 10px",
    borderRadius: 999,
    fontSize: 12,
    fontWeight: 800,
    background: map[tone],
    border: "1px solid rgba(255,255,255,0.10)",
    width: "fit-content",
  };
};
