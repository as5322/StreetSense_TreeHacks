import sqlite3
import math
from uuid import uuid4
from pathlib import Path
from typing import Dict, Any, List, Optional

CATEGORIES = [
    "crime", "public_safety", "transport", "infrastructure",
    "policy", "protest", "weather", "other"
]

DEFAULT_DB_PATH = Path(__file__).resolve().parents[1] / "app.db"

def haversine(lat1, lng1, lat2, lng2):
    R = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)

    a = math.sin(dphi/2)**2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2

    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))



class DBWriter:
    def __init__(self, path: str | None = None):
        self.path = str(Path(path).resolve()) if path else str(DEFAULT_DB_PATH)
        
    def insert_post(
        self,
        *,
        lat: float,
        long: float,
        severity: float,
        category: str,
        content: str,
        human: bool,
    ) -> Dict[str, Any]:
        post_id = str(uuid4())
        category = category if category in CATEGORIES else "other"

        conn = sqlite3.connect(self.path)
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO posts (id, lat, long, severity, category, human, content)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (post_id, lat, long, float(severity), category, 1 if human else 0, content),
        )
        conn.commit()
        conn.close()
        return {"id": post_id}

    def update_truth(
        self,
        *,
        lat: float,
        long: float,
        category: str,
        severity: float,
        alpha: float = 0.25,
    ) -> None:
        category = category if category in CATEGORIES else "other"
        col = category

        conn = sqlite3.connect(self.path)
        cur = conn.cursor()

        cur.execute(
            "INSERT OR IGNORE INTO truth (lat, long) VALUES (?, ?)",
            (lat, long),
        )

        cur.execute(
            f"""
            UPDATE truth
            SET {col} = (1 - ?) * {col} + ? * ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE lat = ? AND long = ?
            """,
            (alpha, alpha, float(severity), lat, long),
        )

        conn.commit()
        conn.close()

    def get_truth(self, *, lat: float, long: float) -> Dict[str, Any] | None:
        conn = sqlite3.connect(self.path)
        cur = conn.cursor()
        cur.execute(
            """
            SELECT lat, long, updated_at, crime, public_safety, transport, infrastructure,
                   policy, protest, weather, other
            FROM truth
            WHERE lat = ? AND long = ?
            """,
            (lat, long),
        )
        row = cur.fetchone()
        conn.close()
        if not row:
            return None

        keys = ["lat", "long", "updated_at"] + CATEGORIES
        return dict(zip(keys, row))


    def get_feed(
        self,
        *,
        lat: float,
        lng: float,
        radius: float = 500,
        limit: int = 500,
        path: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        db_path = str(Path(path).resolve()) if path else str(DEFAULT_DB_PATH)

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # Pull recent posts; we'll do distance filtering in Python (simple + reliable)
        # Adjust created_at -> timestamp depending on your schema
        cur.execute(
            """
            SELECT id, lat, long, severity, category, human, content, created_at
            FROM posts
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = cur.fetchall()
        conn.close()

        nearby: List[Dict[str, Any]] = []
        for r in rows:
            distance = haversine(lat, lng, r["lat"], r["long"])
            if distance <= radius:
                nearby.append(
                    {
                        "id": r["id"],
                        "lat": r["lat"],
                        "lng": r["long"],
                        "content": r["content"],
                        "severity": float(r["severity"]),
                        "category": r["category"],
                        "human": bool(r["human"]),
                        "distance": distance,
                        "timestamp": r["created_at"],  # keep API field name the same
                    }
                )

        # Already sorted by created_at DESC, but keep this in case of ties / schema differences
        nearby.sort(key=lambda x: x["timestamp"], reverse=True)
        return nearby
    
    def count_truth_rows(self) -> int:
        conn = sqlite3.connect(self.path)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM truth")
        (n,) = cur.fetchone()
        conn.close()
        return int(n)

    def get_truth_nearest(self, *, lat: float, lng: float) -> Dict[str, Any] | None:
        conn = sqlite3.connect(self.path)
        cur = conn.cursor()
        cur.execute(
            f"""
            SELECT lat, long, updated_at, {", ".join(CATEGORIES)}
            FROM truth
            ORDER BY ((lat - ?) * (lat - ?)) + ((long - ?) * (long - ?)) ASC
            LIMIT 1
            """,
            (lat, lat, lng, lng),
        )
        row = cur.fetchone()
        conn.close()
        if not row:
            return None

        keys = ["lat", "long", "updated_at"] + CATEGORIES
        return dict(zip(keys, row))
