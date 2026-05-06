from os.path import dirname
from os import makedirs
from sqlite3 import Connection, connect, Row

def open_db_connection(db_path: str) -> Connection:
    makedirs(dirname(db_path), exist_ok=True)
    db_connection = connect(db_path)
    db_connection.row_factory = Row
    return db_connection

def close_db_connection(db_connection: Connection) -> None:
    db_connection.close()

def init_db(conn: Connection) -> None:
    db_version = conn.execute("PRAGMA user_version").fetchone()[0]
    if db_version < 1:
        conn.execute("""
            CREATE TABLE sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ai_provider TEXT NOT NULL,
                context_length INTEGER NOT NULL,
                messages TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """.strip())
        conn.execute("PRAGMA user_version = 1")
    conn.commit()
