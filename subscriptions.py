import sqlite3
from datetime import datetime, timedelta
from typing import Optional

DB_FILE = "subscriptions.db"

PLANS: dict[str, dict] = {
    "week":  {"stars": 5,   "days": 7,   "label": "1 Hafta", "desc": "7 kunlik obuna"},
    "month": {"stars": 15,  "days": 30,  "label": "1 Oy",    "desc": "30 kunlik obuna"},
    "half":  {"stars": 50,  "days": 180, "label": "6 Oy",    "desc": "180 kunlik obuna"},
    "year":  {"stars": 100, "days": 365, "label": "1 Yil",   "desc": "365 kunlik obuna"},
}


def _conn() -> sqlite3.Connection:
    con = sqlite3.connect(DB_FILE)
    con.execute("""
        CREATE TABLE IF NOT EXISTS subscriptions (
            user_id    INTEGER PRIMARY KEY,
            expires_at TEXT NOT NULL
        )
    """)
    con.commit()
    return con


def is_subscribed(user_id: int) -> bool:
    con = _conn()
    row = con.execute(
        "SELECT expires_at FROM subscriptions WHERE user_id = ?", (user_id,)
    ).fetchone()
    con.close()
    if not row:
        return False
    return datetime.fromisoformat(row[0]) > datetime.utcnow()


def add_subscription(user_id: int, days: int) -> datetime:
    con = _conn()
    row = con.execute(
        "SELECT expires_at FROM subscriptions WHERE user_id = ?", (user_id,)
    ).fetchone()
    now = datetime.utcnow()
    if row and datetime.fromisoformat(row[0]) > now:
        expires = datetime.fromisoformat(row[0]) + timedelta(days=days)
    else:
        expires = now + timedelta(days=days)
    con.execute(
        "INSERT OR REPLACE INTO subscriptions (user_id, expires_at) VALUES (?, ?)",
        (user_id, expires.isoformat())
    )
    con.commit()
    con.close()
    return expires


def get_expiry(user_id: int) -> Optional[datetime]:
    con = _conn()
    row = con.execute(
        "SELECT expires_at FROM subscriptions WHERE user_id = ?", (user_id,)
    ).fetchone()
    con.close()
    return datetime.fromisoformat(row[0]) if row else None
