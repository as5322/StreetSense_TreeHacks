from fastapi import APIRouter
from typing import Dict, List
import math
import time
from db.db_writer import DBWriter


router = APIRouter()
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

def haversine(lat1, lng1, lat2, lng2):
    R = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)

    a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def label_from_score(score_0_100: float) -> str:
    if score_0_100 >= 70: return "High"
    if score_0_100 >= 35: return "Moderate"
    return "Low"

@router.get("/location-summary")
def location_summary(lat: float, lng: float, radius: float = 500):
    posts = db.get_feed(lat=lat, lng=lng, radius=radius)  # should return dicts

    # filter precisely by haversine (in case DB radius is coarse)
    in_radius = []
    for p in posts:
        plat = p.get("lat")
        plng = p.get("lng", p.get("long"))
        if plat is None or plng is None:
            continue
        d = haversine(lat, lng, plat, plng)
        if d <= radius:
            in_radius.append((p, d))

    nearby_posts = len(in_radius)

    # compute per-category averages
    sums: Dict[str, float] = {c: 0.0 for c in CATEGORIES}
    counts: Dict[str, int] = {c: 0 for c in CATEGORIES}

    for p, _d in in_radius:
        cat = p.get("category", "other")
        sev = float(p.get("severity", 0.0))
        if cat not in sums:
            cat = "other"
        sums[cat] += sev
        counts[cat] += 1

    truth = {}
    for c in CATEGORIES:
        truth[c] = (sums[c] / counts[c]) if counts[c] else 0.0

    # overall risk: simplest working definition
    overall_risk01 = max(truth.values()) if truth else 0.0
    risk_score = round(overall_risk01 * 100)

    # recommendation (simple rules)
    if risk_score >= 70:
        recommendation = "High risk nearby. Consider an alternative route, stay in well-lit areas, and travel with others if possible."
    elif risk_score >= 35:
        recommendation = "Moderate risk nearby. Stay alert and avoid quiet streets if you can."
    else:
        recommendation = "No major issues reported nearby."

    # hotspots: top 3 categories as “hotspots” (or replace with actual nearby places later)
    hotspots = []
    for cat, v in sorted(truth.items(), key=lambda kv: kv[1], reverse=True)[:3]:
        hotspots.append({
            "name": cat.replace("_", " ").title(),
            "risk": v,
            "distance_m": int(radius * 0.6),  # placeholder until you compute real hotspot centroids
        })

    return {
        "lat": lat,
        "lng": lng,
        "radius": radius,
        "risk_score": risk_score,
        "risk_label": label_from_score(risk_score),
        "nearby_posts": nearby_posts,
        "last_updated": int(time.time()),
        "hotspots": hotspots,
        "recommendation": recommendation,
        "truth": truth,  
        "source": "location",
    }
