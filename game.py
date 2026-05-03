import json
import random
import sqlite3
from dataclasses import dataclass, field
from typing import Optional

from config import MAX_PLAYERS, DATABASE_URL

# PostgreSQL faqat DATABASE_URL berilganda ishlatiladi
_USE_POSTGRES = bool(DATABASE_URL)
if _USE_POSTGRES:
    try:
        import psycopg2
        import psycopg2.extras
    except ImportError:
        print("psycopg2 topilmadi. SQLite ishlatiladi.")
        _USE_POSTGRES = False

DB_FILE = "game_state.db"
_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS games (
    chat_id BIGINT PRIMARY KEY,
    state_json TEXT NOT NULL
)
"""


# ─── GameState ───────────────────────────────────────────────────────────────

@dataclass
class GameState:
    state: str = "idle"          # idle | category | spies | joining | roles
    category: Optional[str] = None
    spy_count: int = 0
    players: list = field(default_factory=list)        # [user_id, ...]
    player_names: dict = field(default_factory=dict)   # user_id -> display name
    spies: list = field(default_factory=list)          # [user_id, ...]
    roles_received: list = field(default_factory=list) # [user_id, ...]
    join_message_id: Optional[int] = None
    join_chat_id: Optional[int] = None
    selected_image: Optional[str] = None

    def add_player(self, user_id: int, name: str) -> bool:
        if user_id in self.players or len(self.players) >= MAX_PLAYERS:
            return False
        self.players.append(user_id)
        self.player_names[user_id] = name
        return True

    def assign_spies(self) -> None:
        self.spies = random.sample(self.players, self.spy_count)

    def reset(self) -> None:
        self.__init__()

    def to_dict(self) -> dict:
        return {
            "state": self.state,
            "category": self.category,
            "spy_count": self.spy_count,
            "players": self.players,
            "player_names": {str(k): v for k, v in self.player_names.items()},
            "spies": self.spies,
            "roles_received": self.roles_received,
            "join_message_id": self.join_message_id,
            "join_chat_id": self.join_chat_id,
            "selected_image": self.selected_image,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GameState":
        gs = cls()
        gs.state           = data.get("state", "idle")
        gs.category        = data.get("category")
        gs.spy_count       = data.get("spy_count", 0)
        gs.players         = data.get("players", [])
        gs.player_names    = {int(k): v for k, v in data.get("player_names", {}).items()}
        gs.spies           = data.get("spies", [])
        gs.roles_received  = data.get("roles_received", [])
        gs.join_message_id = data.get("join_message_id")
        gs.join_chat_id    = data.get("join_chat_id")
        gs.selected_image  = data.get("selected_image")
        return gs


_games: dict[int, GameState] = {}


def get_game(chat_id: int) -> GameState:
    if chat_id not in _games:
        _games[chat_id] = GameState()
    return _games[chat_id]


# ─── SQLite backend ──────────────────────────────────────────────────────────

def _sqlite_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_FILE)
    conn.execute(_CREATE_TABLE)
    conn.commit()
    return conn


def _sqlite_save() -> None:
    conn = _sqlite_conn()
    for cid, game in _games.items():
        if game.state == "idle":
            conn.execute("DELETE FROM games WHERE chat_id = ?", (cid,))
        else:
            conn.execute(
                "INSERT OR REPLACE INTO games (chat_id, state_json) VALUES (?, ?)",
                (cid, json.dumps(game.to_dict()))
            )
    conn.commit()
    conn.close()


def _sqlite_load() -> None:
    conn = _sqlite_conn()
    rows = conn.execute("SELECT chat_id, state_json FROM games").fetchall()
    conn.close()
    for chat_id, state_json in rows:
        gs = GameState.from_dict(json.loads(state_json))
        if gs.state != "idle":
            _games[int(chat_id)] = gs


# ─── PostgreSQL backend ──────────────────────────────────────────────────────

def _pg_conn():
    return psycopg2.connect(DATABASE_URL)


def _pg_save() -> None:
    conn = _pg_conn()
    with conn:
        with conn.cursor() as cur:
            cur.execute(_CREATE_TABLE)
            for cid, game in _games.items():
                if game.state == "idle":
                    cur.execute("DELETE FROM games WHERE chat_id = %s", (cid,))
                else:
                    cur.execute(
                        """INSERT INTO games (chat_id, state_json) VALUES (%s, %s)
                           ON CONFLICT (chat_id) DO UPDATE SET state_json = EXCLUDED.state_json""",
                        (cid, json.dumps(game.to_dict()))
                    )
    conn.close()


def _pg_load() -> None:
    conn = _pg_conn()
    with conn:
        with conn.cursor() as cur:
            cur.execute(_CREATE_TABLE)
            cur.execute("SELECT chat_id, state_json FROM games")
            rows = cur.fetchall()
    conn.close()
    for chat_id, state_json in rows:
        gs = GameState.from_dict(json.loads(state_json))
        if gs.state != "idle":
            _games[int(chat_id)] = gs


# ─── public API ──────────────────────────────────────────────────────────────

def save_state() -> None:
    try:
        if _USE_POSTGRES:
            _pg_save()
        else:
            _sqlite_save()
    except Exception as e:
        print(f"save_state error: {e}")


def load_state() -> None:
    try:
        if _USE_POSTGRES:
            _pg_load()
        else:
            _sqlite_load()
    except Exception as e:
        print(f"load_state error: {e}")
