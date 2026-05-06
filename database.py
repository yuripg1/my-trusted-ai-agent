from json import dumps, loads
from os import getenv
from os.path import dirname
from os import makedirs
from sqlite3 import Connection, connect
from typing import Any


def get_db_path() -> str:
    return getenv("DB_PATH", "data/chat_history.db")


def get_connection(db_path: str) -> Connection:
    makedirs(dirname(db_path), exist_ok=True)
    conn = connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(conn: Connection) -> None:
    version = conn.execute("PRAGMA user_version").fetchone()[0]
    if version < 1:
        conn.execute(
            """CREATE TABLE sessions (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                deepseek_messages TEXT    NOT NULL,
                created_at        TEXT    NOT NULL DEFAULT (datetime('now')),
                updated_at        TEXT    NOT NULL DEFAULT (datetime('now'))
            )"""
        )
        conn.execute("PRAGMA user_version = 1")
    conn.commit()


def save_session(conn: Connection, messages: list[dict[str, Any]], session_id: int | None = None) -> int | None:
    if len(messages) == 0:
        return None
    json_messages = dumps(messages)
    if session_id is None:
        cursor = conn.execute(
            "INSERT INTO sessions (deepseek_messages) VALUES (?)",
            (json_messages,),
        )
        conn.commit()
        return cursor.lastrowid
    else:
        conn.execute(
            "UPDATE sessions SET deepseek_messages = ?, updated_at = datetime('now') WHERE id = ?",
            (json_messages, session_id),
        )
        conn.commit()
        return session_id


def load_session(conn: Connection, session_id: int) -> list[dict[str, Any]] | None:
    cursor = conn.execute("SELECT deepseek_messages FROM sessions WHERE id = ?", (session_id,))
    row = cursor.fetchone()
    if row is None:
        return None
    return loads(row[0])
