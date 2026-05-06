from sqlite3 import Connection
from typing import cast, Self

from ai.core import Ai, AiMessages, AiProviderType, ToolCall

class Session:
    id: int | None
    ai_provider: AiProviderType
    messages: AiMessages

    def __init__(self, ai: Ai) -> None:
        self.id = None
        self.ai_provider = ai.provider
        self.messages = ai.create_messages()

    def load(self, ai: Ai, id: int, db_connection: Connection) -> Self:
        ai_provider = str(ai.provider)
        cursor = db_connection.execute("SELECT id, ai_provider, messages FROM sessions WHERE id = ? and ai_provider = ?", (id,ai_provider))
        fetched_data = cursor.fetchone()
        if fetched_data is not None:
            self.id = int(fetched_data["id"])
            self.ai_provider = cast(AiProviderType, fetched_data["ai_provider"])
            self.messages = ai.decode_messages_json(str(fetched_data["messages"]))
        return self

    def save(self, ai: Ai, db_connection: Connection) -> None:
        ai_provider: str = str(self.ai_provider)
        messages_json: str = ai.encode_messages_json(self.messages)
        if self.id is None:
            cursor = db_connection.execute("INSERT INTO sessions (ai_provider, messages) VALUES (?, ?)",(ai_provider, messages_json))
            self.id = cursor.lastrowid
        else:
            db_connection.execute("UPDATE sessions SET ai_provider = ?, messages = ?, updated_at = datetime(\"now\") WHERE id = ?",(ai_provider, messages_json, self.id))
        db_connection.commit()

    def rewind_message(self, ai: Ai) -> None:
        self.id = None
        ai.rewind_message(self.messages)

    def add_system_messages(self, ai: Ai, system_messages: list[str]) -> None:
        ai.add_system_messages(self.messages, system_messages)

    def add_user_message(self, ai: Ai, user_message: str) -> bool:
        return ai.add_user_message(self.messages, user_message)

    def add_tool_call(self, ai: Ai, tool_call: ToolCall, tool_call_output: str) -> bool:
        return ai.add_tool_call(self.messages, tool_call, tool_call_output)

    def request_assistant_reply(self, ai: Ai) -> int:
        return ai.request_assistant_reply(self.messages)

    def is_messages_empty(self, ai: Ai) -> bool:
        return ai.is_messages_empty(self.messages)

    def get_latest_message(self, ai: Ai) -> tuple[str, str]:
        return ai.get_latest_message(self.messages)

    def get_tool_calls_from_latest_message(self, ai: Ai) -> list[ToolCall]:
        return ai.get_tool_calls_from_latest_message(self.messages)
