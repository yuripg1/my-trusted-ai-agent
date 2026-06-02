from json import dumps, loads
from sqlite3 import Connection, Cursor
from typing import Self

from ai.core import Ai, AiMessage, AiMessages, AiProviderType, AiTools
from tool.core import ToolCall


class Session:
    id: int | None
    ai_provider: AiProviderType
    agent_name: str
    context_length: int
    read_allowlist: list[str]
    _tools: AiTools
    _messages: AiMessages

    def __init__(self, ai: Ai, agent_name: str) -> None:
        self.id = None
        self.ai_provider = ai.provider
        self.agent_name = agent_name
        self.context_length = 0
        self.read_allowlist = []
        self._tools = ai.create_tools()
        self._messages = ai.create_messages()

    def load(self, ai: Ai, id: int, db_connection: Connection) -> Self:
        cursor: Cursor = db_connection.execute(
            "SELECT agent_name, context_length, read_allowlist, tools, messages FROM sessions WHERE id = ? and ai_provider = ?",
            (id, str(ai.provider)),
        )
        fetched_data = cursor.fetchone()
        if fetched_data is not None:
            self.id = id
            self.ai_provider = ai.provider
            self.agent_name = str(fetched_data["agent_name"])
            self.context_length = int(fetched_data["context_length"])
            self.read_allowlist = list(loads(str(fetched_data["read_allowlist"])))
            self._tools = ai.decode_tools_json(str(fetched_data["tools"]))
            self._messages = ai.decode_messages_json(str(fetched_data["messages"]))
        return self

    def save(self, ai: Ai, db_connection: Connection) -> None:
        tools: str = ai.encode_tools_json(self._tools)
        messages_json: str = ai.encode_messages_json(self._messages)
        read_allowlist: str = dumps(self.read_allowlist)
        if self.id is None:
            cursor: Cursor = db_connection.execute(
                "INSERT INTO sessions (ai_provider, agent_name, context_length, read_allowlist, tools, messages) VALUES (?, ?, ?, ?, ?, ?)",
                (str(self.ai_provider), self.agent_name, self.context_length, read_allowlist, tools, messages_json),
            )
            self.id = cursor.lastrowid
        else:
            db_connection.execute(
                'UPDATE sessions SET context_length = ?, read_allowlist = ?, messages = ?, updated_at = datetime("now") WHERE id = ?',
                (self.context_length, read_allowlist, messages_json, self.id),
            )
        db_connection.commit()

    def add_to_read_allowlist(self, path: str) -> None:
        if path not in self.read_allowlist:
            self.read_allowlist.append(path)
            self.read_allowlist.sort()

    def rewind_message(self, ai: Ai) -> None:
        self.id = None
        self.context_length = 0
        ai.rewind_message(self._messages)

    def add_tools(self, ai: Ai, tool_names: list[str]) -> None:
        ai.add_tools(self._tools, tool_names)

    def add_system_messages(self, ai: Ai, system_messages: list[str]) -> None:
        ai.add_system_messages(self._messages, system_messages)

    def add_user_message(self, ai: Ai, user_message: str) -> bool:
        return ai.add_user_message(self._messages, user_message)

    def add_tool_call(self, ai: Ai, tool_call: ToolCall, tool_call_output: str) -> None:
        return ai.add_tool_call(self._messages, tool_call, tool_call_output)

    def request_assistant_reply(self, ai: Ai) -> None:
        self.context_length = ai.request_assistant_reply(self._messages, self._tools)

    def prune(self, ai: Ai) -> None:
        ai.prune(self._messages)

    def has_user_messages(self, ai: Ai) -> bool:
        return ai.has_user_messages(self._messages)

    def get_messages_count(self, ai: Ai) -> int:
        return ai.get_messages_count(self._messages)

    def get_nth_message(self, ai: Ai, message_index: int) -> AiMessage | None:
        return ai.get_nth_message(self._messages, message_index)

    def get_tool_calls_from_nth_message(self, ai: Ai, message_index: int) -> list[ToolCall]:
        return ai.get_tool_calls_from_nth_message(self._messages, message_index)

    def export_to_json(self, ai: Ai) -> str:
        return ai.encode_messages_json(self._messages)

    def export_to_xml(self, ai: Ai) -> str:
        lines: list[str] = []
        lines.append('<?xml version="1.0" encoding="UTF-8"?>')
        lines.append("<session>")
        message_index: int = 0
        while True:
            message: AiMessage | None = self.get_nth_message(ai, message_index)
            if message is None:
                break
            message_content: str = message["message"]
            if len(message_content) == 0:
                message_index += 1
                continue
            role: str = message["role"]
            if role in ["user", "assistant"]:
                safe_content: str = message_content.replace("]]>", "]]]]><![CDATA[>")
                lines.append(f'<message role="{role}"><![CDATA[')
                lines.append(safe_content)
                lines.append("]]></message>")
            message_index += 1
        lines.append("</session>")
        return "\n".join(lines).strip() + "\n"

    def import_messages(self, ai: Ai, messages_json: str) -> None:
        self._messages = ai.decode_messages_json(messages_json)
        self.id = None
