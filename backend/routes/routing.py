from fastapi import APIRouter
from pydantic import BaseModel
import osmnx as ox
import networkx as nx
import os
from db.db_writer import DBWriter
import math
import sqlite3

router = APIRouter()
db = DBWriter()

if os.path.exists("london_walk.graphml"):
    print("Loading cached London graph...")
    G = ox.load_graphml("london_walk.graphml")
else:
    print("Downloading London road network...")
    G = ox.graph_from_place("London, UK", network_type="walk")
    ox.save_graphml(G, "london_walk.graphml")

print("loaded")


SEARCH_RADIUS_M = 150  # tune (100–250m)
MAX_CANDIDATES = 50

def haversine_m(lat1, lon1, lat2, lon2):
    R = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2 * R * math.asin(math.sqrt(a))

def clamp01(v: float) -> float:
    return 0.0 if v < 0 else 1.0 if v > 1 else v

CATEGORIES = [
    "crime","public_safety","transport","infrastructure",
    "policy","protest","weather","other"
]

def row_to_risk01(row) -> float:
    # DB already 0..1
    vals = [float(row[c]) for c in CATEGORIES]
    return clamp01(max(vals) if vals else 0.0)

def risk_at_point(lat: float, lng: float) -> float:
    """
    Nearest-neighbour risk within SEARCH_RADIUS_M; else 0.
    Uses a quick bbox filter, then haversine refine.
    """
    # rough deg window
    pad_deg = SEARCH_RADIUS_M / 111_000.0
    w, e = lng - pad_deg, lng + pad_deg
    s, n = lat - pad_deg, lat + pad_deg

    conn = sqlite3.connect(db.path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(
        f"""
        SELECT lat, long, {", ".join(CATEGORIES)}
        FROM truth
        WHERE long BETWEEN ? AND ?
          AND lat BETWEEN ? AND ?
        LIMIT ?
        """,
        (w, e, s, n, MAX_CANDIDATES),
    )
    rows = cur.fetchall()
    conn.close()

    best = None
    best_d = 1e18
    for r in rows:
        d = haversine_m(lat, lng, float(r["lat"]), float(r["long"]))
        if d < best_d:
            best_d = d
            best = r

    if best is None or best_d > SEARCH_RADIUS_M:
        return 0.0

    # Optional: decay with distance so it’s smoother
    base = row_to_risk01(best)
    decay = math.exp(-(best_d / (SEARCH_RADIUS_M * 0.6))**2)  # gaussian-ish
    return clamp01(base * decay)


def compute_length_scale(G):
    # median edge length across a sample (fast)
    lengths = []
    count = 0
    for _, _, d in G.edges(data=True):
        if "length" in d:
            lengths.append(float(d["length"]))
            count += 1
        if count >= 50_000:
            break
    lengths.sort()
    if not lengths:
        return 50.0
    return lengths[len(lengths)//2]  # median


LENGTH_SCALE = compute_length_scale(G)  # median meters per edge

class RouteRequest(BaseModel):
    start: list  # [lng, lat]
    end: list    # [lng, lat]
    lambda_val: float = 0.5  # 0.5 = 50/50

@router.post("/route")
def compute_route(request: RouteRequest):
    start_lng, start_lat = request.start
    end_lng, end_lat = request.end

    start_node = ox.nearest_nodes(G, start_lng, start_lat)
    end_node = ox.nearest_nodes(G, end_lng, end_lat)

    lam = max(0.0, min(1.0, float(request.lambda_val)))  # clamp 0..1

    def weight(u, v, d):
        length_m = float(d.get("length", 1.0))

        # edge midpoint
        x1, y1 = G.nodes[u]["x"], G.nodes[u]["y"]  # lng, lat
        x2, y2 = G.nodes[v]["x"], G.nodes[v]["y"]
        mid_lng = (x1 + x2) * 0.5
        mid_lat = (y1 + y2) * 0.5

        risk01 = risk_at_point(mid_lat, mid_lng)  # 0..1

        # normalize length to ~O(1)
        length_norm = length_m / max(LENGTH_SCALE, 1e-6)

        # Combine: (1-lam) distance + lam risk
        return (1.0 - lam) * length_norm + lam * risk01

    route_nodes = nx.astar_path(G, start_node, end_node, weight=weight)

    route_coords = [(G.nodes[n]["x"], G.nodes[n]["y"]) for n in route_nodes]
    return {"coordinates": route_coords, "lambda_val": lam}
