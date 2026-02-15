import { useEffect, useMemo, useState } from "react";
import { ShieldCheck, Clock, ArrowRight, Star } from "lucide-react";
import { useNavigate } from "react-router-dom";

type Props = {
  name: string;
  lat: number;
  lng: number;
};

type Hotspot = {
  name: string;
  risk: number; // 0..1
  distance_m: number;
};

type SummaryData = {
  lat: number;
  lng: number;
  radius: number;

  risk_score: number; // 0..100
  risk_label: "Low" | "Moderate" | "High";

  nearby_posts: number;
  last_updated: number; // unix seconds

  hotspots: Hotspot[];
  recommendation: string;

  // New: per-category truth vector (category -> 0..1)
  truth: Record<string, number>;

  // New: where the summary came from
  source?: "location" | "radius_aggregate";
};

// Keep these consistent with RoutePanel + MapHeader alignment
const LEFT_PANEL_LEFT = 20;

export default function SummaryPanel({ name, lat, lng }: Props) {
  const navigate = useNavigate();
  const [data, setData] = useState<SummaryData | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    if (!Number.isFinite(lat) || !Number.isFinite(lng)) return;

    let cancelled = false;

    async function fetchSummary() {
      try {
        setErr(null);

        const url = `http://127.0.0.1:8000/location-summary?lat=${encodeURIComponent(
          String(lat)
        )}&lng=${encodeURIComponent(String(lng))}&radius=500`;

        const res = await fetch(url, { method: "GET" });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);

        const json = (await res.json()) as SummaryData;
        if (!cancelled) setData(json);
      } catch (e: any) {
        if (!cancelled) setErr(e?.message ?? "Failed to load");
      }
    }

    fetchSummary();
    return () => {
      cancelled = true;
    };
  }, [lat, lng]);

  const tone = useMemo(() => {
    if (!data) return "low";
    if (data.risk_label === "High") return "high";
    if (data.risk_label === "Moderate") return "mod";
    return "low";
  }, [data]);

  const labelText = useMemo(() => {
    if (!data) return "";
    return data.risk_label;
  }, [data]);

  const updatedText = useMemo(() => {
    if (!data) return "";
    const delta = Math.max(1, Math.floor(Date.now() / 1000 - data.last_updated));
    if (delta < 60) return `${delta}s ago`;
    const m = Math.floor(delta / 60);
    if (m < 60) return `${m}m ago`;
    const h = Math.floor(m / 60);
    return `${h}h ago`;
  }, [data]);

  const sourceText = useMemo(() => {
    if (!data?.source) return null;
    return data.source === "location" ? "Exact location" : `Avg within ${data.radius}m`;
  }, [data]);

  if (!data && !err) return null;

  return (
      <div className="summary-panel" style={panel}>
      <div style={header}>
        <div style={logo(tone)}>
          <ShieldCheck size={18} />
        </div>
        <div>
          <div style={title}>Safety Summary</div>
          <div style={sub}>{name}</div>
        </div>
      </div>

      {err ? (
        <div style={card}>
          <div style={{ fontWeight: 900, marginBottom: 6 }}>Couldn’t load summary</div>
          <div style={{ opacity: 0.8, fontSize: 13 }}>{err}</div>
        </div>
      ) : (
        <>
          {/* Risk */}
          <div style={card}>
            <div style={rowBetween}>
              <div style={{ fontWeight: 900 }}>Overall</div>
              <div style={badge(tone)}>{labelText}</div>
            </div>

            <div style={bigScoreWrap}>
              <div style={bigScore}>{Math.round(data!.risk_score)}</div>
              <div style={{ opacity: 0.75, fontSize: 12 }}>risk score</div>
            </div>

            <div style={progressWrap}>
              <div style={progressFill(tone, data!.risk_score)} />
            </div>

            <div style={{ marginTop: 10, opacity: 0.85, fontSize: 13, lineHeight: 1.4 }}>
              {data!.recommendation}
            </div>
          </div>

          {/* Stats */}
          <div style={twoCol}>
            <div style={card}>
              <div style={{ fontWeight: 900, marginBottom: 8 }}>Nearby activity</div>
              <div style={statLine}>
                <span style={statLabel}>Reports</span>
                <span style={statValue}>{data!.nearby_posts}</span>
              </div>
              <div style={statLine}>
                <span style={statLabel}>Radius</span>
                <span style={statValue}>{data!.radius}m</span>
              </div>
              <div style={footer}>
                <Clock size={14} />
                Updated {updatedText}
              </div>
              {sourceText && <div style={sourceNote}>{sourceText}</div>}
            </div>

            <div style={card}>
              <div style={{ fontWeight: 900, marginBottom: 8 }}>Community</div>
              <div style={statLine}>
                <span style={statLabel}>Rating</span>
                <span style={statValue}>
                  <Star size={14} style={{ marginRight: 6, opacity: 0.9 }} />
                  {randomDemoRating(tone)}
                </span>
              </div>
            </div>
          </div>

          {/* Hotspots */}
          <div style={card}>
            <div style={{ fontWeight: 900, marginBottom: 10 }}>Hotspots</div>

            {data!.hotspots?.length ? (
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {data!.hotspots.slice(0, 3).map((h, idx) => (
                  <div key={`${h.name}-${idx}`} style={hotspotRow}>
                    <div style={{ fontWeight: 800 }}>{h.name}</div>
                    <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
                      <span style={{ opacity: 0.75, fontSize: 12 }}>{h.distance_m}m</span>
                      <span style={miniBadge(h.risk)}>{Math.round(h.risk * 100)}%</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ opacity: 0.8, fontSize: 13 }}>No hotspots yet.</div>
            )}
          </div>

          {/* Category breakdown (truth vector) */}
          <div style={card}>
            <div style={rowBetween}>
              <div style={{ fontWeight: 900 }}>Category breakdown</div>
              {sourceText && <div style={{ opacity: 0.7, fontSize: 12 }}>{sourceText}</div>}
            </div>

            {data!.truth && Object.keys(data!.truth).length ? (
              <div style={{ display: "flex", flexDirection: "column", gap: 10, marginTop: 12 }}>
                {topTruth(data!.truth, 6).map(([cat, v]) => (
                  <div key={cat}>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                      <div style={{ fontSize: 13, fontWeight: 800, opacity: 0.95 }}>
                        {prettyCategory(cat)}
                      </div>
                      <div style={{ fontSize: 12, fontWeight: 900, opacity: 0.85 }}>
                        {Math.round(v * 100)}%
                      </div>
                    </div>
                    <div style={miniBarWrap}>
                      <div style={miniBarFill(v)} />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ opacity: 0.8, fontSize: 13, marginTop: 8 }}>
                No category data yet.
              </div>
            )}
          </div>

          {/* CTA */}
          <button
            style={cta}
            onClick={() =>
              navigate(`/location/${encodeURIComponent(name)}?lat=${lat}&lng=${lng}`, {
                state: { name, coordinates: { lat, lng } },
              })
            }
          >
            See Live Incidents
            <ArrowRight size={16} />
          </button>
        </>
      )}
    </div>
  );
}

/* ------------------- helpers ------------------- */

function randomDemoRating(tone: "low" | "mod" | "high") {
  // purely cosmetic for now
  if (tone === "low") return "4.6/5";
  if (tone === "mod") return "3.8/5";
  return "2.9/5";
}

function prettyCategory(key: string) {
  return key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function topTruth(truth: Record<string, number>, n = 6) {
  return Object.entries(truth)
    .sort((a, b) => (b[1] ?? 0) - (a[1] ?? 0))
    .slice(0, n);
}

/* ------------------- styling ------------------- */

const panel: React.CSSProperties = {
  position: "absolute",
  top: 480,                 // keep this
  left: LEFT_PANEL_LEFT,
  width: 415,

  maxHeight: "calc(100vh - 520px)",  // 👈 key line
  overflowY: "auto",                 // enable vertical scroll
  overflowX: "hidden",

  zIndex: 20,
  display: "flex",
  flexDirection: "column",
  gap: 12,
  padding: 16,
  borderRadius: 18,
  background: "rgba(15, 23, 42, 0.55)",
  border: "1px solid rgba(255,255,255,0.12)",
  backdropFilter: "blur(12px)",
  boxShadow: "0 18px 45px rgba(0,0,0,0.35)",
  color: "white",
};



const header: React.CSSProperties = {
  display: "flex",
  gap: 12,
  alignItems: "center",
};

const logo = (tone: "low" | "mod" | "high"): React.CSSProperties => ({
  width: 36,
  height: 36,
  borderRadius: 12,
  display: "grid",
  placeItems: "center",
  background:
    tone === "low"
      ? "rgba(34,197,94,0.22)"
      : tone === "mod"
      ? "rgba(234,179,8,0.22)"
      : "rgba(239,68,68,0.22)",
  border: "1px solid rgba(255,255,255,0.14)",
});

const title: React.CSSProperties = {
  fontWeight: 900,
  fontSize: 16,
  letterSpacing: "-0.02em",
};

const sub: React.CSSProperties = {
  fontSize: 12,
  opacity: 0.78,
  marginTop: 2,
};

const card: React.CSSProperties = {
  padding: 14,
  borderRadius: 16,
  background: "rgba(255,255,255,0.08)",
  border: "1px solid rgba(255,255,255,0.12)",
};

const rowBetween: React.CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  gap: 10,
};

const badge = (tone: "low" | "mod" | "high"): React.CSSProperties => ({
  padding: "6px 10px",
  borderRadius: 999,
  fontSize: 12,
  fontWeight: 900,
  background:
    tone === "low"
      ? "rgba(34,197,94,0.22)"
      : tone === "mod"
      ? "rgba(234,179,8,0.22)"
      : "rgba(239,68,68,0.22)",
  border: "1px solid rgba(255,255,255,0.14)",
});

const bigScoreWrap: React.CSSProperties = {
  display: "flex",
  alignItems: "baseline",
  gap: 10,
  margin: "10px 0 8px",
};

const bigScore: React.CSSProperties = {
  fontSize: 34,
  fontWeight: 950 as any,
  letterSpacing: "-0.03em",
};

const progressWrap: React.CSSProperties = {
  height: 10,
  borderRadius: 999,
  background: "rgba(255,255,255,0.12)",
  overflow: "hidden",
};

const progressFill = (tone: "low" | "mod" | "high", value: number): React.CSSProperties => ({
  height: "100%",
  width: `${Math.max(2, Math.min(100, value))}%`,
  background:
    tone === "low"
      ? "rgba(34,197,94,0.95)"
      : tone === "mod"
      ? "rgba(234,179,8,0.95)"
      : "rgba(239,68,68,0.95)",
});

const twoCol: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "1fr 1fr",
  gap: 12,
};

const statLine: React.CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  marginBottom: 8,
  fontSize: 13,
};

const statLabel: React.CSSProperties = {
  opacity: 0.8,
};

const statValue: React.CSSProperties = {
  fontWeight: 900,
  display: "inline-flex",
  alignItems: "center",
};

const footer: React.CSSProperties = {
  marginTop: 6,
  display: "flex",
  alignItems: "center",
  gap: 6,
  fontSize: 12,
  opacity: 0.75,
};

const sourceNote: React.CSSProperties = {
  marginTop: 8,
  fontSize: 12,
  opacity: 0.7,
};

const hotspotRow: React.CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  padding: "10px 10px",
  borderRadius: 14,
  background: "rgba(0,0,0,0.18)",
  border: "1px solid rgba(255,255,255,0.10)",
};

const miniBadge = (risk01: number): React.CSSProperties => {
  const tone = risk01 < 0.35 ? "low" : risk01 < 0.7 ? "mod" : "high";
  return {
    padding: "6px 10px",
    borderRadius: 999,
    fontSize: 12,
    fontWeight: 900,
    background:
      tone === "low"
        ? "rgba(34,197,94,0.22)"
        : tone === "mod"
        ? "rgba(234,179,8,0.22)"
        : "rgba(239,68,68,0.22)",
    border: "1px solid rgba(255,255,255,0.14)",
  };
};

const miniBarWrap: React.CSSProperties = {
  height: 8,
  borderRadius: 999,
  background: "rgba(255,255,255,0.10)",
  overflow: "hidden",
};

const miniBarFill = (v01: number): React.CSSProperties => ({
  height: "100%",
  width: `${Math.max(2, Math.min(100, v01 * 100))}%`,
  background: "rgba(255,255,255,0.85)",
});

const cta: React.CSSProperties = {
  width: "100%",
  height: 46,
  borderRadius: 14,
  border: "1px solid rgba(59,130,246,0.35)",
  background: "rgba(59,130,246,0.95)",
  color: "white",
  fontWeight: 900,
  fontSize: 14,
  cursor: "pointer",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  gap: 8,
  boxShadow: "0 12px 28px rgba(59,130,246,0.35)",
};
