import { useState, useEffect, useRef } from "react";
import {
  ShieldCheck,
  MapPin,
  Flag,
  SlidersHorizontal,
  Navigation,
  Crosshair,
} from "lucide-react";

type Suggestion = {
  name: string;
  coordinates: number[];
};

type Props = {
  onRouteFetched: (route: [number, number][]) => void;
};

export default function RoutePanel({ onRouteFetched }: Props) {
  const fromRef = useRef<HTMLDivElement | null>(null);
  const toRef = useRef<HTMLDivElement | null>(null);

  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");

  const [fromSuggestions, setFromSuggestions] = useState<Suggestion[]>([]);
  const [toSuggestions, setToSuggestions] = useState<Suggestion[]>([]);

  const [selectedFrom, setSelectedFrom] = useState<number[] | null>(null);
  const [selectedTo, setSelectedTo] = useState<number[] | null>(null);

  // UI only (not sent anywhere)
  const [prioritize, setPrioritize] = useState<"safety" | "speed">("safety");

  const token = import.meta.env.VITE_MAPBOX_TOKEN;

  async function fetchSuggestions(query: string, setter: (s: Suggestion[]) => void) {
    if (query.length < 3) {
      setter([]);
      return;
    }

    const response = await fetch(
      `https://api.mapbox.com/geocoding/v5/mapbox.places/${encodeURIComponent(
        query
      )}.json?access_token=${token}&limit=5&proximity=-0.1276,51.5074`
    );

    const data = await response.json();

    const suggestions: Suggestion[] = (data.features || []).map((feature: any) => ({
      name: feature.place_name,
      coordinates: feature.center,
    }));

    setter(suggestions);
  }

  useEffect(() => {
    fetchSuggestions(from, setFromSuggestions);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [from]);

  useEffect(() => {
    fetchSuggestions(to, setToSuggestions);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [to]);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      const t = event.target as Node;
      if (fromRef.current && !fromRef.current.contains(t)) setFromSuggestions([]);
      if (toRef.current && !toRef.current.contains(t)) setToSuggestions([]);
    }

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  async function handleSubmit() {
    if (!selectedFrom || !selectedTo) return;

    const lambdaVal = prioritize === "speed" ? 0 : 0.5;

    const response = await fetch("http://127.0.0.1:8000/route", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        start: selectedFrom,
        end: selectedTo,
        lambda_val: lambdaVal,
      }),
    });

    const data = await response.json();
    onRouteFetched(data.coordinates);
  }

  const canSubmit = Boolean(selectedFrom && selectedTo);

  return (
    <div style={panel}>
      <div style={header}>
        <div style={logo}>
          <ShieldCheck size={18} />
        </div>
        <div>
          <div style={title}>Plan Safe Route</div>
          <div style={sub}>Get the safest path, based on live reports.</div>
        </div>
      </div>

      {/* Start */}
      <div ref={fromRef} style={fieldWrap}>
        <div style={field}>
          <MapPin size={16} style={{ opacity: 0.9 }} />
          <input
            className="route-input"
            placeholder="Start location"
            value={from}
            onChange={(e) => {
              setFrom(e.target.value);
              setSelectedFrom(null);
            }}
            style={input}
          />
          <button
            type="button"
            title="Use my location"
            style={iconBtn}
            onClick={() => {
              // optional: hook geolocation later
            }}
          >
            <Crosshair size={16} />
          </button>
        </div>

        {fromSuggestions.length > 0 && (
          <div style={dropdown}>
            {fromSuggestions.map((s, i) => (
              <div
                key={`${s.name}-${i}`}
                style={item}
                onClick={() => {
                  setFrom(s.name);
                  setSelectedFrom(s.coordinates);
                  setFromSuggestions([]);
                }}
              >
                {s.name}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Destination */}
      <div ref={toRef} style={fieldWrap}>
        <div style={field}>
          <Flag size={16} style={{ opacity: 0.9 }} />
          <input
            placeholder="Destination"
            value={to}
            className="route-input"
            onChange={(e) => {
              setTo(e.target.value);
              setSelectedTo(null);
            }}
            style={input}
          />
          {/* spacer to align with the start's icon button */}
          <div style={{ width: 36 }} />
        </div>

        {toSuggestions.length > 0 && (
          <div style={dropdown}>
            {toSuggestions.map((s, i) => (
              <div
                key={`${s.name}-${i}`}
                style={item}
                onClick={() => {
                  setTo(s.name);
                  setSelectedTo(s.coordinates);
                  setToSuggestions([]);
                }}
              >
                {s.name}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Prioritize */}
      <div style={row}>
        <div style={rowLabel}>
          <SlidersHorizontal size={16} />
          Prioritize
        </div>

        <select
          value={prioritize}
          onChange={(e) => setPrioritize(e.target.value as "safety" | "speed")}
          style={select}
        >
          <option value="safety">Overall safety</option>
          <option value="speed">Speed</option>
        </select>
      </div>

      {/* CTA */}
      <button onClick={handleSubmit} disabled={!canSubmit} style={!canSubmit ? ctaDisabled : cta}>
        <Navigation size={18} />
        Find safe route
      </button>
    </div>
  );
}

/* ---------- Styling ---------- */

const panel: React.CSSProperties = {
  position: "absolute",
  top: 40,
  left: 25,
  width: 400,
  padding: 20,
  borderRadius: 18,
  zIndex: 20,
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
  marginBottom: 14,
};

const logo: React.CSSProperties = {
  width: 36,
  height: 36,
  borderRadius: 12,
  display: "grid",
  placeItems: "center",
  background: "rgba(34,197,94,0.25)",
  border: "1px solid rgba(34,197,94,0.35)",
};

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

const fieldWrap: React.CSSProperties = {
  position: "relative",
  marginBottom: 10,
};

const field: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: 10,
  padding: "12px 12px",
  borderRadius: 14,
  background: "rgba(255,255,255,0.10)",
  border: "1px solid rgba(255,255,255,0.12)",
};

const input: React.CSSProperties = {
  width: "100%",
  border: "none",
  outline: "none",
  background: "transparent",
  fontSize: 14,
  color: "white",
};

const iconBtn: React.CSSProperties = {
  width: 36,
  height: 30,
  borderRadius: 10,
  border: "1px solid rgba(255,255,255,0.14)",
  background: "rgba(255,255,255,0.08)",
  color: "white",
  cursor: "pointer",
  display: "grid",
  placeItems: "center",
};

const dropdown: React.CSSProperties = {
  position: "absolute",
  top: 54,
  width: "100%",
  background: "rgba(15,23,42,0.96)",
  border: "1px solid rgba(255,255,255,0.12)",
  borderRadius: 14,
  boxShadow: "0 20px 40px rgba(0,0,0,0.35)",
  overflow: "hidden",
  maxHeight: 220,
  overflowY: "auto",
  zIndex: 30,
};

const item: React.CSSProperties = {
  padding: "10px 12px",
  cursor: "pointer",
  borderBottom: "1px solid rgba(255,255,255,0.08)",
  fontSize: 13,
  lineHeight: 1.3,
};

const row: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
  gap: 10,
  marginTop: 6,
  marginBottom: 12,
};

const rowLabel: React.CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  gap: 8,
  fontSize: 13,
  fontWeight: 800,
  opacity: 0.9,
};

const select: React.CSSProperties = {
  flex: 1,
  height: 38,
  borderRadius: 12,
  background: "rgba(255,255,255,0.10)",
  color: "white",
  border: "1px solid rgba(255,255,255,0.14)",
  padding: "0 10px",
  outline: "none",
};

const cta: React.CSSProperties = {
  width: "100%",
  height: 48,
  borderRadius: 14,
  border: "1px solid rgba(34,197,94,0.35)",
  background: "rgba(34,197,94,0.92)",
  color: "#07121f",
  fontWeight: 900,
  fontSize: 14,
  cursor: "pointer",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  gap: 10,
  boxShadow: "0 18px 35px rgba(34,197,94,0.25)",
};

const ctaDisabled: React.CSSProperties = {
  ...cta,
  background: "rgba(148,163,184,0.25)",
  border: "1px solid rgba(255,255,255,0.12)",
  color: "rgba(255,255,255,0.7)",
  cursor: "not-allowed",
  boxShadow: "none",
};
