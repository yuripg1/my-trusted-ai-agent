from json import dumps, loads
from requests import post, Response
from time import sleep
from typing import Any, cast, Dict, Literal, Mapping, NotRequired, Required, TypedDict

from ai.deepseek_api_tools import DEEPSEEK_API_TOOLS
from tool_calling import ToolCall, ToolCallArguments

DeepSeekToolCallType = Literal["function"]
DeepSeekRoleType = Literal["assistant", "tool", "user", "system"]
DeepSeekToolChoiceType = Literal["none", "auto", "required"]
DeepSeekModelType = Literal["deepseek-v4-flash", "deepseek-v4-pro"]
DeepSeekThinkingType = Literal["enabled", "disabled"]
DeepSeekReasoningEffortType = Literal["high", "max"]
DeepSeekResponseFormat = Literal["text", "json_object"]

API_STREAM: bool = False
API_TOOL_CHOICE: DeepSeekToolChoiceType = "auto"
API_TIMEOUT: int = 60
API_WAIT_AFTER_ERROR: int = 2


class DeepSeekToolCallFunction(TypedDict):
    name: Required[str]
    arguments: Required[str]


class DeepSeekToolCall(TypedDict):
    id: Required[str]
    type: Required[DeepSeekToolCallType]
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
            new_tool_message: DeepSeekMessage = {"role": role, "content": trimmed_content, "tool_call_id": tool_call_id}
            messages.append(new_tool_message)

    def create_messages(self) -> list[DeepSeekMessage]:
        messages: list[DeepSeekMessage] = []
        return messages

    def rewind_message(self, messages: list[DeepSeekMessage]) -> None:
        while len(messages) != 0 and messages[-1]["role"] != "user":
            del messages[-1]
        if len(messages) != 0:
            del messages[-1]

    def add_system_messages(self, messages: list[DeepSeekMessage], system_messages: list[str]) -> None:
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

    def add_tool_call(self, messages: list[DeepSeekMessage], tool_call: ToolCall, tool_call_output: str) -> bool:
        trimmed_tool_call_output: str = tool_call_output.strip()
        if len(trimmed_tool_call_output) != 0:
            self.__add_to_messages(messages, "tool", trimmed_tool_call_output, "", [], tool_call["id"])
            return True
        else:
            return False

    def request_assistant_reply(self, messages: list[DeepSeekMessage]) -> int:
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
            "stream": API_STREAM,
            "tool_choice": API_TOOL_CHOICE,
            "tools": DEEPSEEK_API_TOOLS,
        }
        if payload["thinking"]["type"] == "enabled":
            payload["reasoning_effort"] = self.reasoning_effort
        response: Response | None = None
        try:
            response = post(f"{self.base_url}/chat/completions", headers=headers, json=payload, timeout=API_TIMEOUT)
        except:
            pass
        if response is None or response.status_code != 200:
            if (
                response is None or response.status_code >= 500 and response.status_code <= 599
            ) or response.status_code == 429:
                sleep(self.wait_after_error)
                return self.request_assistant_reply(messages)
            print(dumps(payload, indent=API_WAIT_AFTER_ERROR))
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
                elif tool_call["function"]["name"] == "search_web":
                    tool_call_arguments = loads(tool_call["function"]["arguments"])
                    tool_calls.append(
                        ToolCall(
                            function_name="search_web",
                            id=tool_call["id"],
                            arguments=ToolCallArguments(
                                query=tool_call_arguments["query"],
                                max_results=tool_call_arguments["max_results"],
                                page=tool_call_arguments["page"],
                            ),
                        )
                    )
                elif tool_call["function"]["name"] == "read_pdf_document":
                    tool_call_arguments = loads(tool_call["function"]["arguments"])
                    tool_calls.append(
                        ToolCall(
                            id=tool_call["id"],
                            function_name="read_pdf_document",
                            arguments=ToolCallArguments(
                                source_type=tool_call_arguments["source_type"], source=tool_call_arguments["source"]
                            ),
                        )
                    )
                elif tool_call["function"]["name"] == "fetch_web_page":
                    tool_call_arguments = loads(tool_call["function"]["arguments"])
                    tool_calls.append(
                        ToolCall(
                            id=tool_call["id"],
                            function_name="fetch_web_page",
                            arguments=ToolCallArguments(url=tool_call_arguments["url"]),
                        )
                    )
        return tool_calls

    def decode_messages_json(self, parsed_messages: Any) -> list[DeepSeekMessage]:
        messages: list[DeepSeekMessage] = []
        for parsed_message in parsed_messages:
            new_message: DeepSeekMessage = DeepSeekMessage(role=parsed_message["role"])
            if "content" in parsed_message:
                new_message["content"] = str(parsed_message["content"])
            else:
                new_message["content"] = ""
            if "reasoning_content" in parsed_message:
                new_message["reasoning_content"] = str(parsed_message["reasoning_content"])
            if "tool_call_id" in parsed_message:
                new_message["tool_call_id"] = str(parsed_message["tool_call_id"])
            if "tool_calls" in parsed_message:
                new_tool_calls: list[DeepSeekToolCall] = []
                for parsed_tool_calls in parsed_message["tool_calls"]:
                    new_tool_call_type: DeepSeekToolCallType = cast(DeepSeekToolCallType, parsed_tool_calls["type"])
                    new_tool_call_function: DeepSeekToolCallFunction = DeepSeekToolCallFunction(
                        name=str(parsed_tool_calls["function"]["name"]),
                        arguments=str(parsed_tool_calls["function"]["arguments"]),
                    )
                    new_tool_call: DeepSeekToolCall = DeepSeekToolCall(
                        id=str(parsed_tool_calls["id"]), type=new_tool_call_type, function=new_tool_call_function
                    )
                    new_tool_calls.append(new_tool_call)
                new_message["tool_calls"] = new_tool_calls
            messages.append(new_message)
        return messages
