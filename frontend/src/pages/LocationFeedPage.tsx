import { Link, useLocation, useParams } from "react-router-dom";
import { useEffect, useMemo, useState } from "react";
import type { Post } from "../lib/locationFeed";
import { computeRisk, riskTone, timeAgo } from "../lib/locationFeed";

export default function LocationFeedPage() {
  const { id } = useParams();
  const location = useLocation();
  const data = location.state as any;

  const [posts, setPosts] = useState<Post[]>([]);
  const [newPost, setNewPost] = useState("");
  const [loading, setLoading] = useState(false);

  const lat = data?.coordinates?.lat;
  const lng = data?.coordinates?.lng;

  const placeName = data?.name || id || "Location";
  const risk = useMemo(() => computeRisk(posts), [posts]);
  const tone = riskTone(risk);

  async function refreshFeed() {
    if (!lat || !lng) return;
    const res = await fetch(
      `http://127.0.0.1:8000/feed?lat=${lat}&lng=${lng}&radius=500`
    );
    const json = await res.json();
    setPosts(json);
  }

  useEffect(() => {
    if (!lat || !lng) return;
    refreshFeed();
    const t = setInterval(refreshFeed, 15000);
    return () => clearInterval(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lat, lng]);

  async function handleCreatePost() {
    if (!newPost.trim() || !lat || !lng) return;
    setLoading(true);
    try {
      await fetch("http://127.0.0.1:8000/post", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          lat,
          lng,
          content: newPost.trim(),
          severity: 1.0,
        }),
      });
      setNewPost("");
      await refreshFeed();
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={ui.page}>
      {/* Top panel like the map overlays */}
      <div style={ui.topWrap}>
        <div style={ui.topBar}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <Link to="/" style={ui.pill}>
              ← Map
            </Link>
            <div style={ui.titleCol}>
              <div style={ui.titleRow}>
                <div style={ui.title}>{placeName}</div>
                <span style={ui.riskChip(tone)}>Risk {risk}</span>
              </div>
              <div style={ui.sub}>
                {posts.length} nearby reports • radius 500m
              </div>
            </div>
          </div>

          <div style={{ display: "flex", gap: 10 }}>
            <Link to="." state={data} style={ui.tab(true)}>
              Feed
            </Link>
            <Link to={`/location/${id}/summary`} state={data} style={ui.tab(false)}>
              Summary
            </Link>
          </div>
        </div>
      </div>

      {/* Scroll area */}
      <div style={ui.scroll}>
        <div style={ui.content}>
          {posts.length === 0 ? (
            <div style={ui.emptyCard}>
              <div style={ui.emptyTitle}>Nothing nearby</div>
              <div style={ui.emptyBody}>
                No incidents reported within 500m. You can post an update below.
              </div>
            </div>
          ) : (
            <div style={ui.list}>
              {posts.map((post) => (
                <div key={post.id} style={ui.postCard}>
                  <div style={{ display: "flex", gap: 12 }}>
                    <div style={ui.avatar} />
                    <div style={{ flex: 1 }}>
                      <div style={ui.postContent}>{post.content}</div>
                      <div style={ui.meta}>
                        <span>{Math.round(post.distance)}m away</span>
                        <span style={ui.dot}>•</span>
                        <span>severity {post.severity.toFixed(1)}</span>
                        <span style={ui.dot}>•</span>
                        <span>{post.timestamp ? timeAgo(post.timestamp) : "now"}</span>
                      </div>
                      <div style={ui.barOuter}>
                        <div
                          style={{
                            ...ui.barInner,
                            width: `${Math.min(100, Math.max(8, post.severity * 20))}%`,
                          }}
                        />
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* spacer so last item isn't hidden */}
          <div style={{ height: 120 }} />
        </div>
      </div>

      {/* Bottom composer styled like the map panels */}
      <div style={ui.composerDock}>
        <div style={ui.composer}>
          <div style={ui.avatar} />
          <div style={{ flex: 1 }}>
            <textarea
              placeholder="What’s happening right now?"
              value={newPost}
              onChange={(e) => setNewPost(e.target.value)}
              style={ui.textarea}
              rows={2}
            />
            <div style={ui.composerRow}>
              <div style={ui.hint}>Be specific. Avoid personal info.</div>
              <button
                onClick={handleCreatePost}
                style={{
                  ...ui.primaryBtn,
                  opacity: loading ? 0.75 : 1,
                  cursor: loading ? "not-allowed" : "pointer",
                }}
                disabled={loading}
              >
                {loading ? "Posting…" : "Post"}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

const ui: Record<string, any> = {
  page: {
    height: "100vh",
    background: "#eef2f7", // slightly darker than before
    color: "#0f172a",
    display: "flex",
    flexDirection: "column",
  },

  topWrap: {
    padding: 22,
    paddingBottom: 16,
  },

  topBar: {
    maxWidth: 1100,
    margin: "0 auto",
    borderRadius: 22,
    padding: "20px 22px",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 16,
    background: "rgba(255,255,255,0.85)",
    border: "1px solid rgba(15,23,42,0.08)",
    boxShadow: "0 20px 50px rgba(15,23,42,0.10)",
    backdropFilter: "blur(12px)",
  },

  titleCol: { display: "flex", flexDirection: "column" },

  titleRow: { display: "flex", alignItems: "center", gap: 14 },

  title: {
    fontSize: 22, // BIGGER
    fontWeight: 900,
    letterSpacing: -0.4,
  },

  sub: {
    marginTop: 6,
    fontSize: 14,
    color: "rgba(15,23,42,0.70)",
  },

  pill: {
    textDecoration: "none",
    fontSize: 14,
    fontWeight: 800,
    padding: "10px 14px",
    borderRadius: 14,
    color: "#0f172a",
    background: "rgba(255,255,255,0.95)",
    border: "1px solid rgba(15,23,42,0.08)",
    boxShadow: "0 12px 25px rgba(15,23,42,0.08)",
  },

  tab: (active: boolean) => ({
    textDecoration: "none",
    fontSize: 14,
    fontWeight: 800,
    padding: "10px 16px",
    borderRadius: 14,
    color: active ? "#0f172a" : "rgba(15,23,42,0.65)",
    background: active ? "rgba(59,130,246,0.18)" : "rgba(255,255,255,0.65)",
    border: "1px solid rgba(15,23,42,0.08)",
  }),

  riskChip: (tone: string) => ({
    fontSize: 13,
    fontWeight: 900,
    padding: "8px 14px",
    borderRadius: 999,
    border: "1px solid rgba(15,23,42,0.08)",
    background:
      tone === "bad"
        ? "rgba(239,68,68,0.18)"
        : tone === "warn"
        ? "rgba(245,158,11,0.22)"
        : "rgba(34,197,94,0.18)",
  }),

  scroll: { flex: 1, overflowY: "auto" },

  content: {
    maxWidth: 1100,
    margin: "0 auto",
    padding: "0 22px 22px",
  },

  list: {
    display: "flex",
    flexDirection: "column",
    gap: 18, // more spacing between posts
  },

  postCard: {
    borderRadius: 22,
    padding: 20, // bigger padding
    background: "rgba(255,255,255,0.88)",
    border: "1px solid rgba(15,23,42,0.08)",
    boxShadow: "0 20px 45px rgba(15,23,42,0.08)",
  },

  avatar: {
    width: 44,  // bigger avatar
    height: 44,
    borderRadius: 999,
    background: "linear-gradient(145deg, #60a5fa, #2563eb)",
    boxShadow: "0 12px 30px rgba(37,99,235,0.25)",
    flexShrink: 0,
  },

  postContent: {
    fontSize: 16,  // bigger content
    fontWeight: 900,
    lineHeight: "22px",
  },

  meta: {
    marginTop: 10,
    fontSize: 13,
    color: "rgba(15,23,42,0.65)",
    display: "flex",
    alignItems: "center",
    gap: 10,
    flexWrap: "wrap",
  },

  dot: { opacity: 0.5 },

  barOuter: {
    marginTop: 14,
    height: 8,
    borderRadius: 999,
    background: "rgba(15,23,42,0.10)",
    overflow: "hidden",
  },

  barInner: {
    height: "100%",
    borderRadius: 999,
    background: "rgba(59,130,246,0.65)",
  },

  emptyCard: {
    marginTop: 18,
    borderRadius: 22,
    padding: 24,
    background: "rgba(255,255,255,0.88)",
    border: "1px solid rgba(15,23,42,0.08)",
    boxShadow: "0 20px 45px rgba(15,23,42,0.08)",
  },

  emptyTitle: {
    fontSize: 16,
    fontWeight: 900,
  },

  emptyBody: {
    marginTop: 8,
    fontSize: 14,
    color: "rgba(15,23,42,0.70)",
  },

  composerDock: {
    position: "fixed",
    left: 0,
    right: 0,
    bottom: 0,
    padding: 18,
    background: "rgba(238,242,247,0.92)",
    borderTop: "1px solid rgba(15,23,42,0.08)",
    backdropFilter: "blur(12px)",
  },

  composer: {
    maxWidth: 1100,
    margin: "0 auto",
    borderRadius: 22,
    padding: 18,
    display: "flex",
    gap: 16,
    alignItems: "flex-start",
    background: "rgba(255,255,255,0.88)",
    border: "1px solid rgba(15,23,42,0.08)",
    boxShadow: "0 20px 45px rgba(15,23,42,0.10)",
  },

  textarea: {
    width: "90%",
    resize: "none",
    borderRadius: 16,
    border: "1px solid rgba(15,23,42,0.10)",
    background: "white",
    color: "#0f172a",
    padding: "14px 16px",
    outline: "none",
    fontSize: 15,
    lineHeight: "22px",
  },

  composerRow: {
    marginTop: 14,
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
  },

  hint: {
    fontSize: 13,
    color: "rgba(15,23,42,0.60)",
  },

  primaryBtn: {
    borderRadius: 14,
    padding: "12px 18px",
    border: "1px solid rgba(37,99,235,0.35)",
    background: "#2563eb",
    color: "white",
    fontWeight: 900,
    fontSize: 14,
    boxShadow: "0 14px 30px rgba(37,99,235,0.25)",
  },
};
