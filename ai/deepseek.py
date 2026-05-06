from json import dumps, loads
from requests import post
from time import sleep
from typing import Any, Dict, Literal, Mapping, NotRequired, Required, TypedDict

from ai.deepseek_tools import DEEPSEEK_TOOLS
from tool_calling import ToolCall, ToolCallArguments

DeepSeekFunctionType = Literal["function"]
DeepSeekRoleType = Literal["assistant", "tool", "user", "system"]
DeepSeekToolChoiceType = Literal["none", "auto", "required"]
DeepSeekModelType = Literal["deepseek-v4-flash", "deepseek-v4-pro"]
DeepSeekThinkingType = Literal["enabled", "disabled"]
DeepSeekReasoningEffortType = Literal["high", "max"]
DeepSeekResponseFormat = Literal["text", "json_object"]


class DeepSeekToolCallFunction(TypedDict):
    name: Required[str]
    arguments: Required[str]


class DeepSeekToolCall(TypedDict):
    id: Required[str]
    type: Required[DeepSeekFunctionType]
    function: Required[DeepSeekToolCallFunction]


class DeepSeekMessage(TypedDict):
    role: Required[DeepSeekRoleType]
    content: NotRequired[str]
    reasoning_content: NotRequired[str]
    tool_calls: NotRequired[list[DeepSeekToolCall]]
    tool_call_id: NotRequired[str]


class DeepSeekRequestThinking(TypedDict):
    type: Required[DeepSeekThinkingType]


class DeepSeekRequest(TypedDict):
    model: Required[DeepSeekModelType]
    messages: Required[list[DeepSeekMessage]]
    thinking: Required[DeepSeekRequestThinking]
    reasoning_effort: NotRequired[DeepSeekReasoningEffortType]
    max_tokens: Required[int]
    stream: Required[bool]
    tools: Required[list[Dict[str, Any]]]
    tool_choice: Required[str]


class DeepSeekAi:
    api_key: str
    base_url: str
    model: DeepSeekModelType
    thinking: DeepSeekThinkingType
    reasoning_effort: DeepSeekReasoningEffortType
    max_tokens: int
    stream: bool
    tools: list[Dict[str, Any]]
    tool_choice: DeepSeekToolChoiceType
    wait_after_error: int

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: DeepSeekModelType,
        thinking: DeepSeekThinkingType,
        reasoning_effort: DeepSeekReasoningEffortType,
        max_tokens: int,
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.thinking = thinking
        self.reasoning_effort = reasoning_effort
        self.max_tokens = max_tokens
        self.stream = False
        self.tools = DEEPSEEK_TOOLS
        self.tool_choice = "auto"
        self.wait_after_error = 2

    def __add_to_messages(
        self,
        messages: list[DeepSeekMessage],
        role: DeepSeekRoleType,
        content: str,
        reasoning_content: str = "",
        tool_calls: list[DeepSeekToolCall] = [],
        tool_call_id: str = "",
    ) -> None:
        trimmed_content: str = content.strip()
        trimmed_reasoning_content: str = reasoning_content.strip()
        if role in ["assistant", "system", "user"]:
            new_generic_message: DeepSeekMessage = {"role": role, "content": trimmed_content}
            if len(trimmed_reasoning_content) != 0:
                new_generic_message["reasoning_content"] = trimmed_reasoning_content
            if len(tool_calls) != 0:
                new_generic_message["tool_calls"] = tool_calls
            messages.append(new_generic_message)
        elif role == "tool":
            new_tool_message: DeepSeekMessage = {
                "role": role,
                "content": trimmed_content,
                "tool_call_id": tool_call_id,
            }
            messages.append(new_tool_message)

    def create_messages(self) -> list[DeepSeekMessage]:
        messages: list[DeepSeekMessage] = []
        return messages

    def create_tool_calls(self) -> list[DeepSeekToolCall]:
        tool_calls: list[DeepSeekToolCall] = []
        return tool_calls

    def rewind_message(self, messages: list[DeepSeekMessage]) -> None:
        while len(messages) != 0 and messages[-1]["role"] != "user":
            del messages[-1]
        if len(messages) != 0:
            del messages[-1]

    def is_messages_empty(self, messages: list[DeepSeekMessage]) -> bool:
        return len(messages) == 0

    def get_latest_message(self, messages: list[DeepSeekMessage]) -> tuple[str, str]:
        message: str = ""
        reasoning: str = ""
        if len(messages) != 0:
            latest_message_object: DeepSeekMessage = messages[-1]
            message = latest_message_object["content"]
            if "reasoning_content" in latest_message_object:
                reasoning = latest_message_object["reasoning_content"]
        return message, reasoning

    def initialize_messages(self, messages: list[DeepSeekMessage], system_messages: list[str]) -> None:
        for system_message in system_messages:
            trimmed_system_message: str = system_message.strip()
            if len(trimmed_system_message) != 0:
                self.__add_to_messages(messages, "system", trimmed_system_message)

    def add_user_message(self, messages: list[DeepSeekMessage], user_message: str) -> bool:
        trimmed_user_message: str = user_message.strip()
        if len(trimmed_user_message) != 0:
            self.__add_to_messages(messages, "user", trimmed_user_message)
            return True
        else:
            return False

    def add_tool_call(self, messages: list[DeepSeekMessage], tool_call: ToolCall, output: str) -> bool:
        trimmed_output: str = output.strip()
        if len(trimmed_output) != 0:
            self.__add_to_messages(messages, "tool", trimmed_output, "", [], tool_call["id"])
            return True
        else:
            return False

    def request_reply(self, messages: list[DeepSeekMessage]) -> int:
        headers: Mapping[str, str] = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload_thinking: DeepSeekRequestThinking = {"type": self.thinking}
        payload: DeepSeekRequest = {
            "model": self.model,
            "messages": messages,
            "thinking": payload_thinking,
            "max_tokens": self.max_tokens,
            "stream": self.stream,
            "tool_choice": self.tool_choice,
            "tools": self.tools,
        }
        if payload["thinking"]["type"] == "enabled":
            payload["reasoning_effort"] = self.reasoning_effort
        response = post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
        if response.status_code != 200:
            if (response.status_code >= 500 and response.status_code <= 599) or response.status_code == 429:
                sleep(self.wait_after_error)
                return self.request_reply(messages)
            print(dumps(payload, indent=2))
            print(response.status_code)
            print(dumps(response.json(), indent=2))
        data = response.json()
        total_tokens: int = int(data["usage"]["total_tokens"])
        message = data["choices"][0]["message"]
        content: str = message.get("content", "").strip()
        reasoning_content: str = message.get("reasoning_content", "").strip()
        tool_calls: list[DeepSeekToolCall] = []
        message_tool_calls = message.get("tool_calls", [])
        for message_tool_call in message_tool_calls:
            tool_calls.append(
                DeepSeekToolCall(
                    id=message_tool_call["id"],
                    type=message_tool_call["type"],
                    function=DeepSeekToolCallFunction(
                        name=message_tool_call["function"]["name"], arguments=message_tool_call["function"]["arguments"]
                    ),
                )
            )
        self.__add_to_messages(messages, "assistant", content, reasoning_content, tool_calls)
        return total_tokens

    def get_tool_calls_from_latest_message(self, messages: list[DeepSeekMessage]) -> list[ToolCall]:
        tool_calls: list[ToolCall] = []
        latest_message_object: DeepSeekMessage = messages[-1]
        if "tool_calls" in latest_message_object:
            for tool_call in latest_message_object["tool_calls"]:
                if tool_call["function"]["name"] == "run_bash_command":
                    tool_call_arguments = loads(tool_call["function"]["arguments"])
                    tool_calls.append(
                        ToolCall(
                            id=tool_call["id"],
                            function_name="run_bash_command",
                            arguments=ToolCallArguments(command=tool_call_arguments["command"]),
                        )
                    )
                elif tool_call["function"]["name"] == "get_random_integer":
                    tool_call_arguments = loads(tool_call["function"]["arguments"])
                    tool_calls.append(
                        ToolCall(
                            id=tool_call["id"],
                            function_name="get_random_integer",
                            arguments=ToolCallArguments(min=tool_call_arguments["min"], max=tool_call_arguments["max"]),
                        )
                    )
                elif tool_call["function"]["name"] == "web_search":
                    tool_call_arguments = loads(tool_call["function"]["arguments"])
                    tool_calls.append(
                        ToolCall(
                            function_name="web_search",
                            id=tool_call["id"],
                            arguments=ToolCallArguments(
                                query=tool_call_arguments["query"],
                                max_results=tool_call_arguments["max_results"],
                                page=tool_call_arguments["page"],
                            ),
                        )
                    )
                elif tool_call["function"]["name"] == "web_fetch":
                    tool_call_arguments = loads(tool_call["function"]["arguments"])
                    tool_calls.append(
                        ToolCall(
                            id=tool_call["id"],
                            function_name="web_fetch",
                            arguments=ToolCallArguments(url=tool_call_arguments["url"]),
                        )
                    )
        return tool_calls
