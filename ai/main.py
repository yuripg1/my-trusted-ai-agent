from typing import cast, Literal, NotRequired, TypedDict

from ai.deepseek import (
    DeepSeekAi,
    DeepSeekMessage,
    DeepSeekModelType,
    DeepSeekReasoningEffortType,
    DeepSeekThinkingType,
)
from environment import Environment
from function import FunctionCall

AiProviderType = Literal["deepseek"]

class AiMessages(TypedDict):
    deepseek_messages: NotRequired[list[DeepSeekMessage]]

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
            deepseek_messages: AiMessages = AiMessages(deepseek_messages=self.deepseek_ai.create_messages())
            return deepseek_messages
        else:
            ai_messages: AiMessages = AiMessages()
            return ai_messages

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

    def add_tool_call(self, messages: AiMessages, function_call: FunctionCall, output: str) -> bool:
        if self.provider == "deepseek" and self.deepseek_ai is not None and "deepseek_messages" in messages:
            return self.deepseek_ai.add_tool_call(messages["deepseek_messages"], function_call, output)
        else:
            return False

    def request_reply(self, messages: AiMessages) -> int:
        if self.provider == "deepseek" and self.deepseek_ai is not None and "deepseek_messages" in messages:
            total_tokens: int = self.deepseek_ai.request_reply(messages["deepseek_messages"])
            return total_tokens
        else:
            return 0

    def get_function_calls_from_latest_message(self, messages: AiMessages) -> list[FunctionCall]:
        if self.provider == "deepseek" and self.deepseek_ai is not None and "deepseek_messages" in messages:
            return self.deepseek_ai.get_function_calls_from_latest_message(messages["deepseek_messages"])
        else:
            function_calls: list[FunctionCall] = []
            return function_calls
