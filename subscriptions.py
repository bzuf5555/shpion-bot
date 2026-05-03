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
    con.execute("""
        CREATE TABLE IF NOT EXISTS promo_codes (
            code       TEXT PRIMARY KEY,
            plan_key   TEXT NOT NULL,
            max_uses   INTEGER NOT NULL,
            used_count INTEGER DEFAULT 0
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS promo_uses (
            code    TEXT,
            user_id INTEGER,
            PRIMARY KEY (code, user_id)
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


# ─── promo codes ─────────────────────────────────────────────────────────────

def create_promo(code: str, plan_key: str, max_uses: int) -> None:
    con = _conn()
    con.execute(
        "INSERT OR REPLACE INTO promo_codes (code, plan_key, max_uses, used_count) VALUES (?, ?, ?, 0)",
        (code.upper(), plan_key, max_uses)
    )
    con.commit()
    con.close()


def use_promo(code: str, user_id: int) -> str:
    """Returns: plan_key | 'not_found' | 'already_used' | 'expired'"""
    con = _conn()
    row = con.execute(
        "SELECT plan_key, max_uses, used_count FROM promo_codes WHERE code = ?",
        (code.upper(),)
    ).fetchone()

    if not row:
        con.close()
        return "not_found"

    plan_key, max_uses, used_count = row

    already = con.execute(
        "SELECT 1 FROM promo_uses WHERE code = ? AND user_id = ?",
        (code.upper(), user_id)
    ).fetchone()

    if already:
        con.close()
        return "already_used"

    if used_count >= max_uses:
        con.close()
        return "expired"

    con.execute(
        "UPDATE promo_codes SET used_count = used_count + 1 WHERE code = ?",
        (code.upper(),)
    )
    con.execute(
        "INSERT INTO promo_uses (code, user_id) VALUES (?, ?)",
        (code.upper(), user_id)
    )
    con.commit()
    con.close()
    return plan_key


def get_expiry(user_id: int) -> Optional[datetime]:
    con = _conn()
    row = con.execute(
        "SELECT expires_at FROM subscriptions WHERE user_id = ?", (user_id,)
    ).fetchone()
    con.close()
    return datetime.fromisoformat(row[0]) if row else None
