from fastapi import APIRouter
from pydantic import BaseModel
from static_analysis_pipeline.criticality_analysis_agent  import CriticalityAgent
from db.db_writer import DBWriter
import math

router = APIRouter()
agent = CriticalityAgent()
db = DBWriter()

class CreatePostRequest(BaseModel):
    lat: float
    lng: float
    content: str
    severity: float = 1.0

def haversine(lat1, lng1, lat2, lng2):
    R = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)

    a = math.sin(dphi/2)**2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2

    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


@router.post("/post")
def create_post(data: CreatePostRequest):
    out = agent.assess(data.content)

    db.insert_post(
        lat=data.lat,
        long=data.lng,
        severity=out.final_severity,
        category=out.category,
        content=data.content,   # ← unchanged
        human=True,
    )

    return {"status": "created"}


@router.get("/feed")
def get_feed(lat: float, lng: float, radius: float = 500):
    posts = db.get_feed(lat=lat, lng=lng, radius=radius)

    nearby = []

    for post in posts:
        distance = haversine(lat, lng, post["lat"], post["lng"])

        if distance <= radius:
            nearby.append({
                "id": post["id"],
                "content": post["content"],
                "severity": post["severity"],
                "distance": distance,
                "timestamp": post["timestamp"],
                "lat": post["lat"],
                "lng": post["lng"],
            })

    nearby.sort(key=lambda x: x["timestamp"], reverse=True)

    return nearby
