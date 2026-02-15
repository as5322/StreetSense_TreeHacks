import { useParams, useLocation, Link } from "react-router-dom";
import { useEffect, useState } from "react";

type Post = {
  id: number;
  content: string;
  severity: number;
  distance: number;
  timestamp: number;
};

export default function LocationPage() {
  const { id } = useParams();
  const location = useLocation();
  const data = location.state as any;

  const [posts, setPosts] = useState<Post[]>([]);
  const [newPost, setNewPost] = useState("");

  const lat = data?.coordinates?.lat;
  const lng = data?.coordinates?.lng;

  useEffect(() => {
    if (!lat || !lng) return;

    fetch(
      `http://127.0.0.1:8000/feed?lat=${lat}&lng=${lng}&radius=500`
    )
      .then(res => res.json())
      .then(data => setPosts(data));
  }, [lat, lng]);

  async function handleCreatePost() {
    if (!newPost || !lat || !lng) return;

    await fetch("http://127.0.0.1:8000/post", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        lat,
        lng,
        content: newPost,
        severity: 1.0,
      }),
    });

    setNewPost("");

    // Refresh feed
    const response = await fetch(
      `http://127.0.0.1:8000/feed?lat=${lat}&lng=${lng}&radius=500`
    );
    const data = await response.json();
    setPosts(data);
  }

  return (
    <div style={{ padding: "40px" }}>
      <Link to="/">← Back to Map</Link>

      <h1>{data?.name || id}</h1>

      <div style={{ display: "flex", gap: "40px", marginTop: "30px" }}>
        
        {/* Live Feed */}
        <div style={{ flex: 1 }}>
          <h2>Live Feed</h2>

          <div style={cardStyle}>
            <textarea
              placeholder="Report something..."
              value={newPost}
              onChange={(e) => setNewPost(e.target.value)}
              style={{ width: "100%", marginBottom: "10px" }}
            />
            <button onClick={handleCreatePost}>
              Post
            </button>
          </div>

          {posts.length === 0 && (
            <div style={cardStyle}>
              No incidents nearby.
            </div>
          )}

          {posts.map(post => (
            <div key={post.id} style={cardStyle}>
              <div>{post.content}</div>
              <small>
                {Math.round(post.distance)}m away
              </small>
            </div>
          ))}
        </div>

        {/* Summary */}
        <div style={{ flex: 1 }}>
          <h2>Summary</h2>
          <div style={cardStyle}>
            Risk Level: {computeRisk(posts)}
          </div>
          <div style={cardStyle}>
            Nearby Posts: {posts.length}
          </div>
        </div>

      </div>
    </div>
  );
}

function computeRisk(posts: Post[]) {
  if (posts.length === 0) return "Low";

  const totalSeverity = posts.reduce(
    (sum, p) => sum + p.severity,
    0
  );

  if (totalSeverity > 5) return "High";
  if (totalSeverity > 2) return "Moderate";
  return "Low";
}

const cardStyle: React.CSSProperties = {
  background: "#f5f5f5",
  padding: "20px",
  borderRadius: "12px",
  marginBottom: "15px",
};
