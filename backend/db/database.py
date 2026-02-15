import sqlite3
from pathlib import Path

# Force DB to live at backend/app.db
DB_PATH = Path(__file__).resolve().parents[1] / "app.db"

DDL = """
CREATE TABLE IF NOT EXISTS posts (
    id TEXT PRIMARY KEY,
    lat REAL NOT NULL,
    long REAL NOT NULL,
    severity REAL NOT NULL,
    category TEXT NOT NULL,
    human INTEGER NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS truth (
    lat REAL NOT NULL,
    long REAL NOT NULL,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    crime REAL NOT NULL DEFAULT 0.0,
    public_safety REAL NOT NULL DEFAULT 0.0,
    transport REAL NOT NULL DEFAULT 0.0,
    infrastructure REAL NOT NULL DEFAULT 0.0,
    policy REAL NOT NULL DEFAULT 0.0,
    protest REAL NOT NULL DEFAULT 0.0,
    weather REAL NOT NULL DEFAULT 0.0,
    other REAL NOT NULL DEFAULT 0.0,

    PRIMARY KEY (lat, long)
);

CREATE INDEX IF NOT EXISTS idx_posts_created_at ON posts(created_at);
CREATE INDEX IF NOT EXISTS idx_posts_human_created_at ON posts(human, created_at);
"""

def main():
    print("Initializing DB at:", DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(DDL)
    conn.commit()
    conn.close()
    print("✅ Initialized app.db with posts + truth tables")

if __name__ == "__main__":
    main()
