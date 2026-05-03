import sqlite3
from datetime import datetime, timedelta
from typing import Optional

DB_FILE = "subscriptions.db"

PLANS: dict[str, dict] = {
    "week":   {"stars": 5,   "days": 7,   "label": "1 Hafta",       "desc": "7 kunlik shaxsiy obuna",    "group": False},
    "month":  {"stars": 15,  "days": 30,  "label": "1 Oy",          "desc": "30 kunlik shaxsiy obuna",   "group": False},
    "half":   {"stars": 50,  "days": 180, "label": "6 Oy",          "desc": "180 kunlik shaxsiy obuna",  "group": False},
    "year":   {"stars": 100, "days": 365, "label": "1 Yil",         "desc": "365 kunlik shaxsiy obuna",  "group": False},
    "gweek":  {"stars": 15,  "days": 7,   "label": "Guruh 1 Hafta", "desc": "Butun guruh uchun 7 kun",   "group": True},
    "gmonth": {"stars": 30,  "days": 30,  "label": "Guruh 1 Oy",   "desc": "Butun guruh uchun 30 kun",  "group": True},
    "ghalf":  {"stars": 100, "days": 180, "label": "Guruh 6 Oy",   "desc": "Butun guruh uchun 180 kun", "group": True},
    "gyear":  {"stars": 150, "days": 365, "label": "Guruh 1 Yil",  "desc": "Butun guruh uchun 365 kun", "group": True},
}


def _conn() -> sqlite3.Connection:
    con = sqlite3.connect(DB_FILE)
    con.executescript("""
        CREATE TABLE IF NOT EXISTS subscriptions (
            user_id    INTEGER PRIMARY KEY,
            expires_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS group_subs (
            chat_id    INTEGER PRIMARY KEY,
            expires_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS promo_codes (
            code       TEXT PRIMARY KEY,
            plan_key   TEXT NOT NULL,
            max_uses   INTEGER NOT NULL,
            used_count INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS promo_uses (
            code    TEXT,
            user_id INTEGER,
            PRIMARY KEY (code, user_id)
        );
        CREATE TABLE IF NOT EXISTS game_history (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id    INTEGER NOT NULL,
            user_id    INTEGER NOT NULL,
            name       TEXT,
            was_spy    INTEGER DEFAULT 0,
            played_at  TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS referrals (
            referred_id  INTEGER PRIMARY KEY,
            referrer_id  INTEGER NOT NULL,
            rewarded     INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS payments (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL,
            plan_key   TEXT NOT NULL,
            stars      INTEGER NOT NULL,
            paid_at    TEXT NOT NULL
        );
    """)
    con.commit()
    return con


# ─── personal subscription ───────────────────────────────────────────────────

def is_subscribed(user_id: int) -> bool:
    con = _conn()
    row = con.execute(
        "SELECT expires_at FROM subscriptions WHERE user_id = ?", (user_id,)
    ).fetchone()
    con.close()
    return bool(row) and datetime.fromisoformat(row[0]) > datetime.utcnow()


def add_subscription(user_id: int, days: int) -> datetime:
    con = _conn()
    row = con.execute(
        "SELECT expires_at FROM subscriptions WHERE user_id = ?", (user_id,)
    ).fetchone()
    now = datetime.utcnow()
    base = datetime.fromisoformat(row[0]) if row and datetime.fromisoformat(row[0]) > now else now
    expires = base + timedelta(days=days)
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


def get_expiring_soon(hours: int = 24) -> list[tuple[int, datetime]]:
    con = _conn()
    now = datetime.utcnow()
    deadline = now + timedelta(hours=hours)
    rows = con.execute(
        "SELECT user_id, expires_at FROM subscriptions WHERE expires_at > ? AND expires_at <= ?",
        (now.isoformat(), deadline.isoformat())
    ).fetchall()
    con.close()
    return [(uid, datetime.fromisoformat(exp)) for uid, exp in rows]


# ─── group subscription ──────────────────────────────────────────────────────

def is_group_subscribed(chat_id: int) -> bool:
    con = _conn()
    row = con.execute(
        "SELECT expires_at FROM group_subs WHERE chat_id = ?", (chat_id,)
    ).fetchone()
    con.close()
    return bool(row) and datetime.fromisoformat(row[0]) > datetime.utcnow()


def add_group_subscription(chat_id: int, days: int) -> datetime:
    con = _conn()
    row = con.execute(
        "SELECT expires_at FROM group_subs WHERE chat_id = ?", (chat_id,)
    ).fetchone()
    now = datetime.utcnow()
    base = datetime.fromisoformat(row[0]) if row and datetime.fromisoformat(row[0]) > now else now
    expires = base + timedelta(days=days)
    con.execute(
        "INSERT OR REPLACE INTO group_subs (chat_id, expires_at) VALUES (?, ?)",
        (chat_id, expires.isoformat())
    )
    con.commit()
    con.close()
    return expires


def get_group_expiry(chat_id: int) -> Optional[datetime]:
    con = _conn()
    row = con.execute(
        "SELECT expires_at FROM group_subs WHERE chat_id = ?", (chat_id,)
    ).fetchone()
    con.close()
    return datetime.fromisoformat(row[0]) if row else None


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
    con.execute("UPDATE promo_codes SET used_count = used_count + 1 WHERE code = ?", (code.upper(),))
    con.execute("INSERT INTO promo_uses (code, user_id) VALUES (?, ?)", (code.upper(), user_id))
    con.commit()
    con.close()
    return plan_key


# ─── game history ─────────────────────────────────────────────────────────────

def track_game(chat_id: int, player_names: dict[int, str], spies: list[int]) -> None:
    con = _conn()
    now = datetime.utcnow().isoformat()
    for uid, name in player_names.items():
        con.execute(
            "INSERT INTO game_history (chat_id, user_id, name, was_spy, played_at) VALUES (?, ?, ?, ?, ?)",
            (chat_id, uid, name, 1 if uid in spies else 0, now)
        )
    con.commit()
    con.close()


def get_user_stats(user_id: int) -> dict:
    con = _conn()
    row = con.execute(
        "SELECT COUNT(*), SUM(was_spy) FROM game_history WHERE user_id = ?", (user_id,)
    ).fetchone()
    con.close()
    return {"games": row[0] or 0, "as_spy": row[1] or 0}


def get_group_leaderboard(chat_id: int) -> list[tuple[str, int, int]]:
    con = _conn()
    rows = con.execute("""
        SELECT name, COUNT(*) as games, SUM(was_spy) as spy_count
        FROM game_history WHERE chat_id = ?
        GROUP BY user_id ORDER BY games DESC LIMIT 10
    """, (chat_id,)).fetchall()
    con.close()
    return rows


# ─── referrals ───────────────────────────────────────────────────────────────

def add_referral(referrer_id: int, referred_id: int) -> None:
    con = _conn()
    con.execute(
        "INSERT OR IGNORE INTO referrals (referred_id, referrer_id) VALUES (?, ?)",
        (referred_id, referrer_id)
    )
    con.commit()
    con.close()


def get_referrer(referred_id: int) -> Optional[int]:
    con = _conn()
    row = con.execute(
        "SELECT referrer_id FROM referrals WHERE referred_id = ?", (referred_id,)
    ).fetchone()
    con.close()
    return row[0] if row else None


def claim_referral_bonus(referred_id: int) -> Optional[int]:
    """Birinchi to'lovdan keyin referrer ga bonus berish. referrer_id yoki None."""
    con = _conn()
    row = con.execute(
        "SELECT referrer_id, rewarded FROM referrals WHERE referred_id = ?", (referred_id,)
    ).fetchone()
    if not row or row[1]:
        con.close()
        return None
    con.execute("UPDATE referrals SET rewarded = 1 WHERE referred_id = ?", (referred_id,))
    con.commit()
    con.close()
    return row[0]


# ─── payments tracking ────────────────────────────────────────────────────────

def record_payment(user_id: int, plan_key: str, stars: int) -> None:
    con = _conn()
    con.execute(
        "INSERT INTO payments (user_id, plan_key, stars, paid_at) VALUES (?, ?, ?, ?)",
        (user_id, plan_key, stars, datetime.utcnow().isoformat())
    )
    con.commit()
    con.close()


# ─── global stats ─────────────────────────────────────────────────────────────

def get_global_stats() -> dict:
    con = _conn()
    now = datetime.utcnow().isoformat()
    users      = con.execute("SELECT COUNT(DISTINCT user_id) FROM game_history").fetchone()[0]
    active_sub = con.execute("SELECT COUNT(*) FROM subscriptions WHERE expires_at > ?", (now,)).fetchone()[0]
    active_grp = con.execute("SELECT COUNT(*) FROM group_subs WHERE expires_at > ?", (now,)).fetchone()[0]
    total_games = con.execute("SELECT COUNT(*) FROM game_history").fetchone()[0]
    total_stars = con.execute("SELECT COALESCE(SUM(stars),0) FROM payments").fetchone()[0]
    con.close()
    return {
        "users": users,
        "active_sub": active_sub,
        "active_grp": active_grp,
        "total_games": total_games // max(1, con.execute("SELECT COUNT(DISTINCT chat_id, played_at) FROM game_history").fetchone()[0] or 1),
        "total_stars": total_stars,
    }
