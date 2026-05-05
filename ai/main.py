from typing import Any, cast, Dict, Literal

from ai.deepseek import (
    DeepSeekAi,
    DeepSeekMessage,
    DeepSeekModelType,
    DeepSeekReasoningEffortType,
    DeepSeekRoleType,
    DeepSeekThinkingType,
    DeepSeekToolCall,
)
from environment import Environment
from function import FunctionCall

AiProviderType = Literal["deepseek"]


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

    def create_deepseek_messages(self) -> list[DeepSeekMessage]:
        deepseek_messages: list[DeepSeekMessage] = []
        return deepseek_messages

    def create_deepseek_tool_calls(self) -> list[DeepSeekToolCall]:
        deepseek_tool_calls: list[DeepSeekToolCall] = []
        return deepseek_tool_calls

    def add_to_messages(
        self,
        deepseek_messages: list[DeepSeekMessage] = [],
        deepseek_role: DeepSeekRoleType | None = None,
        deepseek_content: str = "",
        deepseek_reasoning_content: str = "",
        deepseek_tool_calls: list[DeepSeekToolCall] = [],
        deepseek_tool_call_id: str = "",
    ) -> None:
        if self.provider == "deepseek" and self.deepseek_ai is not None and deepseek_role is not None:
            self.deepseek_ai.add_to_messages(
                messages=deepseek_messages,
                role=deepseek_role,
                content=deepseek_content,
                reasoning_content=deepseek_reasoning_content,
                tool_calls=deepseek_tool_calls,
                tool_call_id=deepseek_tool_call_id,
            )

    def initialize_messages(self, system_messages: list[str], deepseek_messages: list[DeepSeekMessage] = []) -> None:
        if self.provider == "deepseek" and self.deepseek_ai is not None:
            self.deepseek_ai.initialize_messages(system_messages=system_messages, messages=deepseek_messages)

    def rewind_message(self, deepseek_messages: list[DeepSeekMessage] = []) -> None:
        if self.provider == "deepseek" and self.deepseek_ai is not None:
            self.deepseek_ai.rewind_message(deepseek_messages)

    def request_reply(self, deepseek_messages: list[DeepSeekMessage] = []):
        if self.provider == "deepseek" and self.deepseek_ai is not None:
            self.deepseek_ai.request_reply(deepseek_messages)

    def decode_tool_call(self, deepseek_tool_call: DeepSeekToolCall | None = None) -> FunctionCall | None:
        if self.provider == "deepseek" and self.deepseek_ai is not None and deepseek_tool_call is not None:
            return self.deepseek_ai.decode_tool_call(tool_call=deepseek_tool_call)
        else:
            return None
