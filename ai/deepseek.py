from json import dumps, loads
from requests import post
from time import sleep
from typing import Any, Dict, Literal, Mapping, NotRequired, Required, TypedDict

from ai.deepseek_tools import DEEPSEEK_TOOLS
from function import FunctionCallArguments,FunctionCallInfo,FunctionCall

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

    def add_to_messages(
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

    def initialize_messages(self, system_messages: list[str], messages: list[DeepSeekMessage]) -> None:
        messages = []
        for system_message in system_messages:
            trimmed_system_message: str = system_message.strip()
            if len(trimmed_system_message) != 0:
                self.add_to_messages(messages, "system", trimmed_system_message)

    def rewind_message(self, messages: list[DeepSeekMessage]) -> None:
        while len(messages) != 0 and messages[-1]["role"] != "user":
            del messages[-1]
        if len(messages) != 0:
            del messages[-1]

    def request_reply(self, messages: list[DeepSeekMessage]) -> None:
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
        message = data["choices"][0]["message"]
        content: str = message.get("content", "").strip()
        reasoning_content: str = message.get("reasoning_content", "").strip()
        tool_calls: list[DeepSeekToolCall] = []
        message_tool_calls = message.get("tool_calls", [])
        for message_tool_call in message_tool_calls:
            tool_calls.append(DeepSeekToolCall(id=message_tool_call["id"],type=message_tool_call["type"],function=DeepSeekToolCallFunction(name=message_tool_call["function"]["name"], arguments=message_tool_call["function"]["arguments"])))
        self.add_to_messages(messages,"assistant",content,reasoning_content,tool_calls)

    def decode_tool_call(self, tool_call: DeepSeekToolCall) -> FunctionCall | None:
        if tool_call["function"]["name"] == "run_bash_command":
            function_arguments = loads(tool_call["function"]["arguments"])
            permission_request_message:str = f"$ {function_arguments["command"]}"
            return FunctionCall(function_name="run_bash_command",info=FunctionCallInfo(tool_call_id=tool_call["id"]),arguments=FunctionCallArguments(command=function_arguments["command"]))
        elif tool_call["function"]["name"] == "get_random_integer":
            function_arguments = loads(tool_call["function"]["arguments"])
            return FunctionCall(function_name="get_random_integer",info=FunctionCallInfo(tool_call_id=tool_call["id"]),arguments=FunctionCallArguments(min=function_arguments["min"],max=function_arguments["max"]))
        elif tool_call["function"]["name"] == "web_search":
            function_arguments = loads(tool_call["function"]["arguments"])
            return FunctionCall(function_name="web_search",info=FunctionCallInfo(tool_call_id=tool_call["id"]),arguments=FunctionCallArguments(query=function_arguments["query"],max_results=function_arguments["max_results"],page=function_arguments["page"]))
        elif tool_call["function"]["name"] == "web_fetch":
            function_arguments = loads(tool_call["function"]["arguments"])
            return FunctionCall(function_name="web_fetch",info=FunctionCallInfo(tool_call_id=tool_call["id"]),arguments=FunctionCallArguments(url=function_arguments["url"]))
        else:
            return None

    def get_tools_declaration(self) -> list[Dict[str, Any]]:
        return
