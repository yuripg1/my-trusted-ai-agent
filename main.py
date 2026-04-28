import random
import requests
from rich import console as rich_console, markdown as rich_markdown
import time
import typing
import subprocess
import json
import ddgs

FunctionType = typing.Literal["function"]
RoleType = typing.Literal["assistant", "tool", "user", "system"]
DeepSeekToolChoiceType = typing.Literal["none", "auto", "required"]
DeepSeekModelType = typing.Literal["deepseek-v4-flash", "deepseek-v4-pro"]
DeepSeekThinkingType = typing.Literal["enabled", "disabled"]
DeepSeekReasoningEffortType = typing.Literal["high", "max"]
DeepSeekResponseFormat = typing.Literal["text", "json_object"]
DuckDuckGoSafeSearchType = typing.Literal["off", "moderate", "on"]


class ToolCallFunction(typing.TypedDict):
    name: typing.Required[str]
    arguments: typing.Required[str]


class ToolCall(typing.TypedDict):
    id: typing.Required[str]
    type: typing.Required[FunctionType]
    function: typing.Required[ToolCallFunction]


class DeepSeekRequestMessage(typing.TypedDict):
    role: typing.Required[RoleType]
    content: typing.NotRequired[str]
    reasoning_content: typing.NotRequired[str]
    tool_calls: typing.NotRequired[list[ToolCall]]
    tool_call_id: typing.NotRequired[str]


class DeepSeekRequestThinking(typing.TypedDict):
    type: typing.Required[DeepSeekThinkingType]


class DeepSeekRequest(typing.TypedDict):
    model: typing.Required[DeepSeekModelType]
    messages: typing.Required[list[DeepSeekRequestMessage]]
    thinking: typing.Required[DeepSeekRequestThinking]
    reasoning_effort: typing.NotRequired[DeepSeekReasoningEffortType]
    max_tokens: typing.Required[int]
    stream: typing.Required[bool]
    tools: typing.Required[list[typing.Dict[str, typing.Any]]]
    tool_choice: typing.Required[str]


class DuckDuckGoSearchResult(typing.TypedDict):
    title: typing.Required[str]
    href: typing.Required[str]
    body: typing.Required[str]


class DeepSeekEnvironment(typing.TypedDict):
    api_key: typing.Required[str]
    base_url: typing.Required[str]
    max_tokens: typing.Required[int]
    tool_choice: typing.Required[DeepSeekToolChoiceType]
    tools: typing.Required[list[typing.Dict[str, typing.Any]]]
    response_format: typing.Required[DeepSeekResponseFormat]
    stream: typing.Required[bool]
    wait_after_error: typing.Required[int]
    model: typing.Required[DeepSeekModelType]
    thinking: typing.Required[DeepSeekThinkingType]
    reasoning_effort: typing.Required[DeepSeekReasoningEffortType]


class DuckDuckGoEnvironment(typing.TypedDict):
    safesearch: typing.Required[DuckDuckGoSafeSearchType]
    default_max_results: typing.Required[int]


class Environment(typing.TypedDict):
    deepseek: typing.Required[DeepSeekEnvironment]
    duckduckgo: typing.Required[DuckDuckGoEnvironment]


TOOLS: list[typing.Dict[str, typing.Any]] = [
    {
        "type": "function",
        "function": {
            "name": "run_bash_command",
            "description": "Run any bash command on the user's system",
            "parameters": {
                "type": "object",
                "properties": {"command": {"type": "string", "description": "The bash command to run"}},
                "required": ["command"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_random_integer",
            "description": "Return a random integer between min and max (inclusive)",
            "parameters": {
                "type": "object",
                "properties": {
                    "min": {"type": "integer", "description": "The minimum integer (inclusive)"},
                    "max": {"type": "integer", "description": "The maximum integer (inclusive)"},
                },
                "required": ["min", "max"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web using DuckDuckGo and return results with title, href, and body",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 10, max: 10)",
                    },
                    "page": {"type": "integer", "description": "Page of results (default: 1)"},
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        },
    },
]

ENVIRONMENT: Environment = Environment(
    deepseek=DeepSeekEnvironment(
        api_key="",
        base_url="https://api.deepseek.com",
        max_tokens=393216,
        tool_choice="auto",
        tools=TOOLS,
        response_format="text",
        stream=False,
        wait_after_error=2,
        model="deepseek-v4-flash",
        # model="deepseek-v4-pro",
        thinking="disabled",
        # thinking="enabled",
        reasoning_effort="high",
        # reasoning_effort="max",
    ),
    duckduckgo=DuckDuckGoEnvironment(
        safesearch="off",
        default_max_results=10,
    ),
)


def execute_bash_command(command: str) -> tuple[str, str, int]:
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout, result.stderr, result.returncode


SYSTEM_COMMAND_1 = "date"
SYSTEM_COMMAND_STDOUT_1, SYSTEM_COMMAND_STDERR_1, SYSTEM_COMMAND_RETURNCODE_1 = execute_bash_command(SYSTEM_COMMAND_1)

SYSTEM_COMMAND_2 = "getent passwd ${USER}"
SYSTEM_COMMAND_STDOUT_2, SYSTEM_COMMAND_STDERR_2, SYSTEM_COMMAND_RETURNCODE_2 = execute_bash_command(SYSTEM_COMMAND_2)

SYSTEM_COMMAND_3 = "uname -a"
SYSTEM_COMMAND_STDOUT_3, SYSTEM_COMMAND_STDERR_3, SYSTEM_COMMAND_RETURNCODE_3 = execute_bash_command(SYSTEM_COMMAND_3)

SYSTEM_COMMAND_4 = "cat /etc/os-release"
SYSTEM_COMMAND_STDOUT_4, SYSTEM_COMMAND_STDERR_4, SYSTEM_COMMAND_RETURNCODE_4 = execute_bash_command(SYSTEM_COMMAND_4)

SYSTEM_COMMAND_5 = "hostnamectl"
SYSTEM_COMMAND_STDOUT_5, SYSTEM_COMMAND_STDERR_5, SYSTEM_COMMAND_RETURNCODE_5 = execute_bash_command(SYSTEM_COMMAND_5)


def get_formatted_command_output(stdout: str, stderr: str, returncode: int) -> str:
    formatted_command_output: str = ""
    trimmed_stdout = stdout.strip()
    if len(trimmed_stdout) != 0:
        formatted_command_output += f"--- STDOUT ---\n\n{trimmed_stdout}\n\n"
    trimmed_stderr = stderr.strip()
    if len(trimmed_stderr) != 0:
        formatted_command_output += f"--- STDERR ---\n\n{trimmed_stderr}\n\n"
    if returncode != 0:
        formatted_command_output += f"--- RETURNCODE ---\n\n{returncode}\n\n"
    return formatted_command_output.strip()


SYSTEM_MESSAGES: list[str] = [
    "You must always reply using proper English (US) grammar",
    "You must always reply using strict Markdown syntax with proper formatting",
    "You are an AI assistant operating in a text-only terminal interface",
    'You are a capable of running any bash commands on the user\'s system using the "run_bash_command" function',
    'You are capable of getting a random integer number using the "get_random_integer" function',
    'You are capable of searching the web using the "web_search" function',
    f"$ {SYSTEM_COMMAND_1}\n\n{get_formatted_command_output(SYSTEM_COMMAND_STDOUT_1, SYSTEM_COMMAND_STDERR_1, SYSTEM_COMMAND_RETURNCODE_1)}",
    f"$ {SYSTEM_COMMAND_2}\n\n{get_formatted_command_output(SYSTEM_COMMAND_STDOUT_2, SYSTEM_COMMAND_STDERR_2, SYSTEM_COMMAND_RETURNCODE_2)}",
    f"$ {SYSTEM_COMMAND_3}\n\n{get_formatted_command_output(SYSTEM_COMMAND_STDOUT_3, SYSTEM_COMMAND_STDERR_3, SYSTEM_COMMAND_RETURNCODE_3)}",
    f"$ {SYSTEM_COMMAND_4}\n\n{get_formatted_command_output(SYSTEM_COMMAND_STDOUT_4, SYSTEM_COMMAND_STDERR_4, SYSTEM_COMMAND_RETURNCODE_4)}",
    f"$ {SYSTEM_COMMAND_5}\n\n{get_formatted_command_output(SYSTEM_COMMAND_STDOUT_5, SYSTEM_COMMAND_STDERR_5, SYSTEM_COMMAND_RETURNCODE_5)}",
]


def get_llm_output(
    deepseek_environment: DeepSeekEnvironment, llm_messages: list[DeepSeekRequestMessage]
) -> tuple[str, str, list[ToolCall]]:
    headers: typing.Mapping[str, str] = {
        "Authorization": f"Bearer {deepseek_environment["api_key"]}",
        "Content-Type": "application/json",
    }
    payload_thinking: DeepSeekRequestThinking = {"type": deepseek_environment["thinking"]}
    payload: DeepSeekRequest = {
        "model": deepseek_environment["model"],
        "messages": llm_messages,
        "thinking": payload_thinking,
        "max_tokens": deepseek_environment["max_tokens"],
        "stream": deepseek_environment["stream"],
        "tools": deepseek_environment["tools"],
        "tool_choice": deepseek_environment["tool_choice"],
    }
    if payload["thinking"]["type"] == "enabled":
        payload["reasoning_effort"] = deepseek_environment["reasoning_effort"]
    response = requests.post(f"{deepseek_environment["base_url"]}/chat/completions", headers=headers, json=payload)
    if response.status_code != 200:
        if (response.status_code >= 500 and response.status_code <= 599) or response.status_code == 429:
            time.sleep(deepseek_environment["wait_after_error"])
            return get_llm_output(deepseek_environment, llm_messages)
        print(json.dumps(payload, indent=2))
        print(response.status_code)
        print(json.dumps(response.json(), indent=2))
    data = response.json()
    message = data["choices"][0]["message"]
    content: str = message.get("content", "").strip()
    reasoning_content: str = message.get("reasoning_content", "").strip()
    tool_calls: list[ToolCall] = []
    message_tool_calls = message.get("tool_calls", [])
    for message_tool_call in message_tool_calls:
        tool_calls.append(
            ToolCall(
                id=message_tool_call["id"],
                type=message_tool_call["type"],
                function=ToolCallFunction(
                    name=message_tool_call["function"]["name"], arguments=message_tool_call["function"]["arguments"]
                ),
            )
        )
    return content, reasoning_content, tool_calls


def add_to_llm_messages(
    llm_messages: list[DeepSeekRequestMessage],
    role: RoleType,
    content: str,
    reasoning_content: str = "",
    tool_calls: list[ToolCall] = [],
    tool_call_id: str = "",
) -> None:
    trimmed_content: str = content.strip()
    trimmed_reasoning_content: str = reasoning_content.strip()
    if role in ["assistant", "system", "user"]:
        new_assistant_message: DeepSeekRequestMessage = {"role": role, "content": trimmed_content}
        if len(trimmed_reasoning_content) != 0:
            new_assistant_message["reasoning_content"] = trimmed_reasoning_content
        if len(tool_calls) != 0:
            new_assistant_message["tool_calls"] = tool_calls
        llm_messages.append(new_assistant_message)
    elif role == "tool":
        new_tool_message: DeepSeekRequestMessage = {
            "role": role,
            "content": trimmed_content,
            "tool_call_id": tool_call_id,
        }
        llm_messages.append(new_tool_message)


def print_bash_command(command: str) -> None:
    input(
        f"------------------------------------- TOOL -------------------------------------\n\n{command}\n\nPress ENTER to continue..."
    )
    print("\n", end="")


def print_random_integer(min_integer: int, max_integer: int) -> None:
    print(
        f'------------------------------------- TOOL -------------------------------------\n\nPicking a random integer between "{min_integer}" (inclusive) and "{max_integer}" (inclusive)\n\n',
        end="",
    )


def print_web_search(query: str, max_results: int, page: int) -> None:
    print(
        f'------------------------------------- TOOL -------------------------------------\n\nSearching the web for "{query}" ({max_results} results - page {page})\n\n',
        end="",
    )


def search_web(duckduckgo_environment: DuckDuckGoEnvironment, query: str, max_results: int, page: int) -> str:
    raw_search_results = list(
        ddgs.DDGS().text(
            query=query, safesearch=duckduckgo_environment["safesearch"], max_results=max_results, page=page
        )
    )
    if len(raw_search_results) == 0:
        return f'No results found for "{query}"'
    search_results: list[DuckDuckGoSearchResult] = []
    for raw_search_result in raw_search_results:
        search_results.append(
            DuckDuckGoSearchResult(
                title=raw_search_result["title"],
                href=raw_search_result["href"],
                body=raw_search_result["body"],
            )
        )
    text_results: list[str] = []
    for search_result in search_results:
        text_results.append(f"{search_result["title"]}\n\n{search_result["href"]}\n\n{search_result["body"]}")
    return "\n\n---\n\n".join(text_results)


def process_tool_calls(
    duckduckgo_environment: DuckDuckGoEnvironment, tool_calls: list[ToolCall], messages: list[DeepSeekRequestMessage]
) -> None:
    for tool_call in tool_calls:
        if tool_call["function"]["name"] == "run_bash_command":
            command: str = ""
            function_arguments = json.loads(tool_call["function"]["arguments"])
            command = function_arguments["command"]
            print_bash_command(command)
            stdout, stderr, returncode = execute_bash_command(command)
            formatted_command_output = get_formatted_command_output(stdout, stderr, returncode)
            add_to_llm_messages(messages, "tool", formatted_command_output, "", [], tool_call["id"])
        elif tool_call["function"]["name"] == "get_random_integer":
            function_arguments = json.loads(tool_call["function"]["arguments"])
            min_integer: int = function_arguments["min"]
            max_integer: int = function_arguments["max"]
            print_random_integer(min_integer, max_integer)
            random_integer = random.randint(min_integer, max_integer)
            add_to_llm_messages(messages, "tool", str(random_integer), "", [], tool_call["id"])
        elif tool_call["function"]["name"] == "web_search":
            function_arguments = json.loads(tool_call["function"]["arguments"])
            query: str = function_arguments["query"]
            max_results: int = function_arguments.get("max_results", duckduckgo_environment["default_max_results"])
            page: int = function_arguments.get("page", 1)
            print_web_search(query, max_results, page)
            text_results = search_web(duckduckgo_environment, query, max_results, page)
            add_to_llm_messages(messages, "tool", text_results, "", [], tool_call["id"])


def create_llm_messages(llm_system_messages: list[str]) -> list[DeepSeekRequestMessage]:
    llm_messages: list[DeepSeekRequestMessage] = []
    for llm_system_message in llm_system_messages:
        trimmed_system_message: str = llm_system_message.strip()
        if len(trimmed_system_message) != 0:
            add_to_llm_messages(llm_messages, "system", trimmed_system_message)
    return llm_messages


def print_message(message: str, reasoning: str = "") -> None:
    rich_console_instance = rich_console.Console(no_color=True)
    if len(reasoning) != 0:
        print(f"---------------------------- ASSISTANT (reasoning) -----------------------------\n\n", end="")
        rich_console_instance.print(rich_markdown.Markdown(reasoning))
        print("\n", end="")
    if len(message) != 0:
        print(f"---------------------------------- ASSISTANT -----------------------------------\n\n", end="")
        rich_console_instance.print(rich_markdown.Markdown(message))
        print("\n", end="")


def rewind_conversation(llm_messages: list[DeepSeekRequestMessage]) -> None:
    while len(llm_messages) != 0 and llm_messages[-1]["role"] != "user":
        del llm_messages[-1]
    if len(llm_messages) != 0:
        del llm_messages[-1]


def main() -> None:
    llm_messages = create_llm_messages(SYSTEM_MESSAGES)
    print("\n", end="")
    while True:
        try:
            llm_input: str = input(
                "------------------------------------- USER -------------------------------------\n\n> "
            ).strip()
        except KeyboardInterrupt:
            print("\n\n--------------------------------------------------------------------------------\n\n", end="")
            break
        if len(llm_input) == 0:
            print("\n", end="")
            continue
        print("\n", end="")
        if llm_input == "/rewind":
            rewind_conversation(llm_messages)
        elif llm_input == "/new":
            llm_messages = []
        else:
            add_to_llm_messages(llm_messages, "user", llm_input)
            while True:
                llm_output, llm_output_reasoning, tool_calls = get_llm_output(ENVIRONMENT["deepseek"], llm_messages)
                print_message(llm_output, llm_output_reasoning)
                add_to_llm_messages(llm_messages, "assistant", llm_output, llm_output_reasoning, tool_calls)
                if len(tool_calls) != 0:
                    process_tool_calls(ENVIRONMENT["duckduckgo"], tool_calls, llm_messages)
                else:
                    break


if __name__ == "__main__":
    main()
