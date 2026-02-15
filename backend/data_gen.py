"""
seed_truth.py

Generates a smooth, spatially-consistent "truth" vector over a bounding box
using random anchors + Gaussian distance weighting, then upserts into DB.

Run:
  python seed_truth.py

Tweak:
  - BOUNDS for your city
  - GRID_STEP_M for density
  - N_ANCHORS and SIGMA_M for smoothness
"""

from __future__ import annotations

import json
import math
import random
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
from db.db_writer import DBWriter

# -------------------------
# Config (London-ish bounds)
# -------------------------
BOUNDS = {
    "min_lat": 51.20,
    "max_lat": 51.75,
    "min_lng": -0.65,
    "max_lng": 0.45,
}

db = DBWriter()


CATEGORIES = [
    "crime",
    "public_safety",
    "transport",
    "infrastructure",
    "policy",
    "protest",
    "weather",
    "other",
]

SEED = 1337

# Grid resolution (smaller = more points = more DB rows)
GRID_STEP_M = 250  # 250m grid is already a lot

# Number of random anchors (more = more texture)
N_ANCHORS = 60

# Smoothness radius (bigger = smoother neighborhoods)
SIGMA_M = 900  # try 700..1500

# Overall "riskiness" baseline
BASE_RISK = 0.15
RISK_VARIANCE = 0.65  # how strong anchors can get

# If you want a few *very* strong dangerous pockets
N_SUPER_HOTSPOTS = 6


# -------------------------
# Geo helpers
# -------------------------
def haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6371000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def meters_to_deg_lat(m: float) -> float:
    return m / 111_320.0


def meters_to_deg_lng(m: float, at_lat: float) -> float:
    return m / (111_320.0 * math.cos(math.radians(at_lat)))


def clamp01(x: float) -> float:
    return 0.0 if x < 0 else 1.0 if x > 1 else x


# -------------------------
# Smooth field model
# -------------------------
@dataclass
class Anchor:
    lat: float
    lng: float
    vec: Dict[str, float]  # category -> 0..1
    strength: float        # 0..1 overall scaling


def random_category_vec(rng: random.Random, strength: float) -> Dict[str, float]:
    """
    Create a category vector with some structure:
    - pick 1-2 dominant categories
    - spread some residual to others
    """
    vec = {c: 0.0 for c in CATEGORIES}

    # Choose dominant categories
    dom = rng.sample(CATEGORIES, k=2 if rng.random() < 0.55 else 1)
    for c in dom:
        vec[c] = clamp01(BASE_RISK + strength * (0.6 + 0.4 * rng.random()))

    # Add mild correlated noise to others
    for c in CATEGORIES:
        if c in dom:
            continue
        vec[c] = clamp01(BASE_RISK * (0.3 + 0.7 * rng.random()) + strength * (0.05 * rng.random()))

    return vec


def gaussian_weight(d_m: float, sigma_m: float) -> float:
    # exp(-d^2 / (2 sigma^2))
    return math.exp(-(d_m * d_m) / (2.0 * sigma_m * sigma_m))


def blend_truth(lat: float, lng: float, anchors: List[Anchor], sigma_m: float) -> Dict[str, float]:
    # Weighted average of anchor vectors
    wsum = 0.0
    out = {c: 0.0 for c in CATEGORIES}

    for a in anchors:
        d = haversine_m(lat, lng, a.lat, a.lng)
        w = gaussian_weight(d, sigma_m) * (0.35 + 0.65 * a.strength)
        if w < 1e-6:
            continue
        wsum += w
        for c in CATEGORIES:
            out[c] += w * a.vec[c]

    if wsum <= 1e-9:
        return out

    for c in CATEGORIES:
        out[c] = clamp01(out[c] / wsum)

    return out


# -------------------------
# DB hook (EDIT THIS)
# -------------------------
import sqlite3
from pathlib import Path
import time

def upsert_truth(lat: float, lng: float, truth: Dict[str, float]) -> None:
    # IMPORTANT: your DB uses column name "long" not "lng"
    conn = sqlite3.connect(db.path)
    cur = conn.cursor()

    # Ensure row exists
    cur.execute("INSERT OR IGNORE INTO truth (lat, long) VALUES (?, ?)", (lat, lng))

    # Update all category columns
    cols = ", ".join([f"{c} = ?" for c in CATEGORIES] + ["updated_at = CURRENT_TIMESTAMP"])
    values = [float(truth[c]) for c in CATEGORIES] + [lat, lng]

    cur.execute(
        f"""
        UPDATE truth
        SET {cols}
        WHERE lat = ? AND long = ?
        """,
        values,
    )

    conn.commit()
    conn.close()



# -------------------------
# Main seeding logic
# -------------------------
def generate_anchors(rng: random.Random) -> List[Anchor]:
    anchors: List[Anchor] = []
    for i in range(N_ANCHORS):
        lat = rng.uniform(BOUNDS["min_lat"], BOUNDS["max_lat"])
        lng = rng.uniform(BOUNDS["min_lng"], BOUNDS["max_lng"])

        strength = clamp01(rng.random() * RISK_VARIANCE)
        vec = random_category_vec(rng, strength)

        anchors.append(Anchor(lat=lat, lng=lng, vec=vec, strength=strength))

    # Add a few strong hotspots
    for _ in range(N_SUPER_HOTSPOTS):
        lat = rng.uniform(BOUNDS["min_lat"], BOUNDS["max_lat"])
        lng = rng.uniform(BOUNDS["min_lng"], BOUNDS["max_lng"])
        strength = clamp01(0.85 + 0.15 * rng.random())
        vec = random_category_vec(rng, strength)
        anchors.append(Anchor(lat=lat, lng=lng, vec=vec, strength=strength))

    return anchors


def grid_points() -> List[Tuple[float, float]]:
    pts: List[Tuple[float, float]] = []
    lat = BOUNDS["min_lat"]
    while lat <= BOUNDS["max_lat"]:
        dlat = meters_to_deg_lat(GRID_STEP_M)
        dlng = meters_to_deg_lng(GRID_STEP_M, at_lat=lat)

        lng = BOUNDS["min_lng"]
        while lng <= BOUNDS["max_lng"]:
            pts.append((lat, lng))
            lng += dlng

        lat += dlat

    return pts


def main():
    rng = random.Random(SEED)

    anchors = generate_anchors(rng)
    pts = grid_points()

    print(f"Seeding {len(pts)} grid points with {len(anchors)} anchors...")
    print(f"Bounds: {BOUNDS}, step={GRID_STEP_M}m, sigma={SIGMA_M}m")

    # If you want to bulk insert, collect and batch here
    # For now we just compute and call upsert_truth
    every = max(1, len(pts) // 20)

    for i, (lat, lng) in enumerate(pts):
        truth = blend_truth(lat, lng, anchors, SIGMA_M)

        # Optional: add tiny local noise so it doesn't look too "perfect"
        # (still consistent because it's small)
        for c in CATEGORIES:
            truth[c] = clamp01(truth[c] + rng.uniform(-0.02, 0.02))

        # Upsert into your truth table
        upsert_truth(lat, lng, truth)

        if i % every == 0:
            top_cat = max(truth.items(), key=lambda kv: kv[1])[0]
            print(f"[{i}/{len(pts)}] lat={lat:.5f}, lng={lng:.5f}, top={top_cat}")

    print("Done.")


if __name__ == "__main__":
    main()
