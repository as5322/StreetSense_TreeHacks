export type Post = {
  id: number;
  content: string;
  severity: number;
  distance: number;
  timestamp: number;
};

export function computeRisk(posts: Post[]) {
  if (posts.length === 0) return "Low";

  const totalSeverity = posts.reduce((sum, p) => sum + p.severity, 0);
  if (totalSeverity > 5) return "High";
  if (totalSeverity > 2) return "Moderate";
  return "Low";
}

export function riskTone(risk: string): "low" | "mod" | "high" {
  if (risk === "High") return "high";
  if (risk === "Moderate") return "mod";
  return "low";
}

export function timeAgo(ts: number) {
  const ms = Date.now() - ts;
  const s = Math.max(1, Math.floor(ms / 1000));
  if (s < 60) return `${s}s`;
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}m`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h`;
  const d = Math.floor(h / 24);
  return `${d}d`;
}
