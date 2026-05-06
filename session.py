from sqlite3 import Connection

from ai.core import AiMessages, parse_messages_json, serialize_messages_json

class Session:
    id: int | None
    messages: AiMessages

    def __init__(self, session_id: int | None = None, db_connection: Connection | None = None, messages: AiMessages | None = None) -> None:
        self.id = None
        self.messages = AiMessages()
        if session_id is not None and db_connection is not None:
            query_result = db_connection.execute("SELECT id, messages FROM sessions WHERE id = ?", (session_id,))
            fetched_id, fetched_messages = query_result.fetchone()
            if fetched_id is not None:
                self.id = int(fetched_id)
            if fetched_messages is not None:
                self.messages = parse_messages_json(str(fetched_messages))
        elif messages is not None:
            self.messages = messages

    def save(self, db_connection: Connection) -> None:
        if self.messages is None:
            return None
        messages_json = serialize_messages_json(self.messages)
        if self.id is None:
            query_result = db_connection.execute("INSERT INTO sessions (messages) VALUES (?)",(messages_json,))
            self.id = query_result.lastrowid
        else:
            db_connection.execute("UPDATE sessions SET messages = ?, updated_at = datetime('now') WHERE id = ?",(messages_json, self.id))
        db_connection.commit()

    def clear_id(self) -> None:
        self.id = None
