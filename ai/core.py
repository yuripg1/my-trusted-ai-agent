from json import dumps, loads
from typing import cast, Literal, NotRequired, TypedDict

from ai.deepseek import (
    DeepSeekAi,
    DeepSeekMessage,
    DeepSeekModelType,
    DeepSeekReasoningEffortType,
    DeepSeekThinkingType,
    parse_messages_json as deepseek_parse_messages_json,
)
from environment import Environment
from tool_calling import ToolCall

AiProviderType = Literal["deepseek"]

class AiMessages(TypedDict):
    deepseek_messages: NotRequired[list[DeepSeekMessage]]

def serialize_messages_json(messages: AiMessages) -> str:
    return dumps(messages)

def parse_messages_json(messages_json: str) -> AiMessages:
    parsed_messages_json = loads(messages_json)
    if "deepseek_messages" in parsed_messages_json:
        return AiMessages(deepseek_messages=deepseek_parse_messages_json(parsed_messages_json["deepseek_messages"]))
    else:
        return AiMessages()

class Ai:
    provider: AiProviderType
    deepseek_ai: DeepSeekAi | None

    def __init__(self, environment: Environment) -> None:
        self.provider = cast(AiProviderType, environment.ai_provider)
        if (
            self.provider == "deepseek"
            and environment.deepseek_model is not None
            and environment.deepseek_thinking is not None
            and environment.deepseek_reasoning_effort is not None
        ):
            self.deepseek_ai = DeepSeekAi(
                api_key=environment.deepseek_api_key,
                base_url=environment.deepseek_base_url,
                model=cast(DeepSeekModelType, environment.deepseek_model),
                thinking=cast(DeepSeekThinkingType, environment.deepseek_thinking),
                reasoning_effort=cast(DeepSeekReasoningEffortType, environment.deepseek_reasoning_effort),
                max_tokens=environment.deepseek_max_tokens,
            )

    def create_messages(self) -> AiMessages:
        if self.provider == "deepseek" and self.deepseek_ai is not None:
            return AiMessages(deepseek_messages=self.deepseek_ai.create_messages())
        else:
            return AiMessages()

    def rewind_message(self, messages: AiMessages) -> None:
        if self.provider == "deepseek" and self.deepseek_ai is not None and "deepseek_messages" in messages:
            self.deepseek_ai.rewind_message(messages["deepseek_messages"])

    def is_messages_empty(self, messages: AiMessages) -> bool:
        if self.provider == "deepseek" and self.deepseek_ai is not None and "deepseek_messages" in messages:
            return self.deepseek_ai.is_messages_empty(messages["deepseek_messages"])
        else:
            return False

    def get_latest_message(self, messages: AiMessages) -> tuple[str, str]:
        if self.provider == "deepseek" and self.deepseek_ai is not None and "deepseek_messages" in messages:
            return self.deepseek_ai.get_latest_message(messages["deepseek_messages"])
        else:
            return "", ""

    def initialize_messages(self, messages: AiMessages, system_messages: list[str]) -> None:
        if self.provider == "deepseek" and self.deepseek_ai is not None and "deepseek_messages" in messages:
            self.deepseek_ai.initialize_messages(messages["deepseek_messages"], system_messages)

    def add_user_message(self, messages: AiMessages, user_message: str) -> bool:
        if self.provider == "deepseek" and self.deepseek_ai is not None and "deepseek_messages" in messages:
            return self.deepseek_ai.add_user_message(messages["deepseek_messages"], user_message)
        else:
            return False

    def add_tool_call(self, messages: AiMessages, tool_call: ToolCall, output: str) -> bool:
        if self.provider == "deepseek" and self.deepseek_ai is not None and "deepseek_messages" in messages:
            return self.deepseek_ai.add_tool_call(messages["deepseek_messages"], tool_call, output)
        else:
            return False

    def request_reply(self, messages: AiMessages) -> int:
        if self.provider == "deepseek" and self.deepseek_ai is not None and "deepseek_messages" in messages:
            total_tokens: int = self.deepseek_ai.request_reply(messages["deepseek_messages"])
            return total_tokens
        else:
            return 0

    def get_tool_calls_from_latest_message(self, messages: AiMessages) -> list[ToolCall]:
        if self.provider == "deepseek" and self.deepseek_ai is not None and "deepseek_messages" in messages:
            return self.deepseek_ai.get_tool_calls_from_latest_message(messages["deepseek_messages"])
        else:
            tool_calls: list[ToolCall] = []
            return tool_calls
