import ddgs
import dotenv
import json
import os
import random
import requests
import time
import trafilatura
import typing
import subprocess

import terminal_ui

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
    model: typing.Required[DeepSeekModelType]
    thinking: typing.Required[DeepSeekThinkingType]
    reasoning_effort: typing.Required[DeepSeekReasoningEffortType]
    max_tokens: typing.Required[int]
    tool_choice: typing.Required[DeepSeekToolChoiceType]
    tools: typing.Required[list[typing.Dict[str, typing.Any]]]
    response_format: typing.Required[DeepSeekResponseFormat]
    stream: typing.Required[bool]
    wait_after_error: typing.Required[int]


class DuckDuckGoEnvironment(typing.TypedDict):
    safesearch: typing.Required[DuckDuckGoSafeSearchType]
    default_max_results: typing.Required[int]
    default_page: typing.Required[int]


class Environment(typing.TypedDict):
    language: typing.Required[str]
    deepseek: typing.Required[DeepSeekEnvironment]
    duckduckgo: typing.Required[DuckDuckGoEnvironment]
    terminal: typing.Required[terminal_ui.TerminalEnvironment]


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
    {
        "type": "function",
        "function": {
            "name": "web_fetch",
            "description": "Fetch and extract the main text content from a web page URL",
            "parameters": {
                "type": "object",
                "properties": {"url": {"type": "string", "description": "The URL of the web page to fetch and read"}},
                "required": ["url"],
                "additionalProperties": False,
            },
        },
    },
]

dotenv.load_dotenv()

ENVIRONMENT: Environment = Environment(
    language=os.getenv("LANGUAGE", ""),
    deepseek=DeepSeekEnvironment(
        api_key=os.getenv("DEEPSEEK_API_KEY", ""),
        base_url=os.getenv("DEEPSEEK_BASE_URL", ""),
        model=typing.cast(DeepSeekModelType, os.getenv("DEEPSEEK_MODEL", "")),
        thinking=typing.cast(DeepSeekThinkingType, os.getenv("DEEPSEEK_THINKING", "")),
        reasoning_effort=typing.cast(DeepSeekReasoningEffortType, os.getenv("DEEPSEEK_REASONING_EFFORT", "")),
        max_tokens=int(os.getenv("DEEPSEEK_MAX_TOKENS", "")),
        tool_choice="auto",
        tools=TOOLS,
        response_format="text",
        stream=False,
        wait_after_error=2,
    ),
    duckduckgo=DuckDuckGoEnvironment(
        safesearch=typing.cast(DuckDuckGoSafeSearchType, os.getenv("DUCKDUCKGO_SAFESEARCH", "")),
        default_max_results=10,
        default_page=1,
    ),
    terminal=terminal_ui.TerminalEnvironment(
        show_reasoning=(os.getenv("TERMINAL_SHOW_REASONING", "").lower() in ("true", "1", "yes")),
    ),
)

if len(ENVIRONMENT["deepseek"]["api_key"]) == 0:
    raise ValueError("DEEPSEEK_API_KEY is not set")


def ui_startup() -> None:
    terminal_ui.startup()


def ui_teardown() -> None:
    terminal_ui.teardown()


def get_user_input() -> str:
    return terminal_ui.get_user_input()


def print_assistant_message(
    terminal_environment: terminal_ui.TerminalEnvironment, total_tokens: int, message: str, reasoning: str = ""
) -> None:
    terminal_ui.print_assistant_message(terminal_environment, total_tokens, message, reasoning)


def prompt_for_bash_command_permission(command: str) -> bool:
    return terminal_ui.prompt_for_bash_command_permission(command)


def print_random_integer(min_integer: int, max_integer: int) -> None:
    terminal_ui.print_random_integer(min_integer, max_integer)


def print_web_search(query: str, max_results: int, page: int) -> None:
    terminal_ui.print_web_search(query, max_results, page)


def print_web_fetch(url: str) -> None:
    terminal_ui.print_web_fetch(url)


def execute_bash_command(permission_granted: bool, command: str) -> tuple[str, str, int]:
    if not permission_granted:
        return "", "", 0
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout, result.stderr, result.returncode


def get_formatted_bash_command_output(
    command: str, permission_granted: bool, stdout: str, stderr: str, returncode: int
) -> str:
    if not permission_granted:
        return "Bash command execution manually denied by the user"
    result_lines: list[str] = []
    trimmed_command = command.strip()
    result_lines.append(f"<returncode>{returncode}</returncode>")
    result_lines.append(f"<command>\n{trimmed_command}\n</command>")
    trimmed_stdout = stdout.strip()
    if len(trimmed_stdout) != 0:
        result_lines.append(f"<stdout>\n{trimmed_stdout}\n</stdout>")
    trimmed_stderr = stderr.strip()
    if len(trimmed_stderr) != 0:
        result_lines.append(f"<stderr>\n{trimmed_stderr}\n</stderr>")
    joined_command_result: str = "\n".join(result_lines)
    return f"<command_execution>\n{joined_command_result}\n</command_execution>"


def get_bash_command_as_system_message(command: str) -> str:
    stdout, stderr, returncode = execute_bash_command(True, command)
    return get_formatted_bash_command_output(command, True, stdout, stderr, returncode)


def get_system_messages() -> list[str]:
    system_messages: list[str] = [
        f"You must always reply using {ENVIRONMENT["language"]} with proper grammar",
        "You must always reply using strict Markdown syntax with proper formatting",
        'You are capable of running any bash commands on the user\'s system using the "run_bash_command" function',
        'You are capable of getting a random integer number using the "get_random_integer" function',
        'You are capable of searching the web using the "web_search" function',
        'You are capable of fetching web pages using the "web_fetch" function',
        terminal_ui.get_system_instruction(),
        get_bash_command_as_system_message("getent passwd ${USER}"),
        get_bash_command_as_system_message("uname -a"),
        get_bash_command_as_system_message("cat /etc/os-release"),
        get_bash_command_as_system_message("hostnamectl"),
        get_bash_command_as_system_message("date"),
    ]
    return system_messages


def get_llm_output(
    deepseek_environment: DeepSeekEnvironment, llm_messages: list[DeepSeekRequestMessage]
) -> tuple[str, str, list[ToolCall], int]:
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
    total_tokens: int = int(data["usage"]["total_tokens"])
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
    return content, reasoning_content, tool_calls, total_tokens


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
        new_generic_message: DeepSeekRequestMessage = {"role": role, "content": trimmed_content}
        if len(trimmed_reasoning_content) != 0:
            new_generic_message["reasoning_content"] = trimmed_reasoning_content
        if len(tool_calls) != 0:
            new_generic_message["tool_calls"] = tool_calls
        llm_messages.append(new_generic_message)
    elif role == "tool":
        new_tool_message: DeepSeekRequestMessage = {
            "role": role,
            "content": trimmed_content,
            "tool_call_id": tool_call_id,
        }
        llm_messages.append(new_tool_message)


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
                title=raw_search_result["title"], href=raw_search_result["href"], body=raw_search_result["body"]
            )
        )
    text_results: list[str] = []
    for search_result in search_results:
        text_results.append(
            f"<search_result>\n<title>{search_result["title"]}</title>\n<href>{search_result["href"]}</href>\n<body>\n{search_result["body"]}\n</body>\n</search_result>"
        )
    joined_search_results: str = "\n".join(text_results)
    return f'<search_results query="{query}" max_results="{max_results}" page="{page}">\n{joined_search_results}\n</search_results>'


def fetch_web_page(url: str) -> str:
    downloaded = trafilatura.fetch_url(url)
    if downloaded is None:
        return f'Could not fetch content from "{url}"'
    result = trafilatura.extract(downloaded, output_format="markdown", with_metadata=False)
    trimmed_result: str = result.strip() if result is not None else ""
    if len(trimmed_result) == 0:
        return f'No extractable text content found at "{url}"'
    return f'<fetched_content url="{url}">\n{trimmed_result}\n</fetched_content>'


def process_tool_calls(
    duckduckgo_environment: DuckDuckGoEnvironment, tool_calls: list[ToolCall], messages: list[DeepSeekRequestMessage]
) -> None:
    for tool_call in tool_calls:
        if tool_call["function"]["name"] == "run_bash_command":
            function_arguments = json.loads(tool_call["function"]["arguments"])
            command: str = function_arguments["command"]
            permission_granted: bool = prompt_for_bash_command_permission(command)
            stdout, stderr, returncode = execute_bash_command(permission_granted, command)
            formatted_command_output: str = get_formatted_bash_command_output(
                command, permission_granted, stdout, stderr, returncode
            )
            add_to_llm_messages(messages, "tool", formatted_command_output, "", [], tool_call["id"])
        elif tool_call["function"]["name"] == "get_random_integer":
            function_arguments = json.loads(tool_call["function"]["arguments"])
            min_integer: int = function_arguments["min"]
            max_integer: int = function_arguments["max"]
            print_random_integer(min_integer, max_integer)
            random_integer: int = random.randint(min_integer, max_integer)
            text_result: str = (
                f'<random_integer min="{min_integer}" max="{max_integer}">{random_integer}</random_integer>'
            )
            add_to_llm_messages(messages, "tool", text_result, "", [], tool_call["id"])
        elif tool_call["function"]["name"] == "web_search":
            function_arguments = json.loads(tool_call["function"]["arguments"])
            query: str = function_arguments["query"]
            max_results: int = function_arguments.get("max_results", duckduckgo_environment["default_max_results"])
            page: int = function_arguments.get("page", duckduckgo_environment["default_page"])
            print_web_search(query, max_results, page)
            text_results: str = search_web(duckduckgo_environment, query, max_results, page)
            add_to_llm_messages(messages, "tool", text_results, "", [], tool_call["id"])
        elif tool_call["function"]["name"] == "web_fetch":
            function_arguments = json.loads(tool_call["function"]["arguments"])
            url: str = function_arguments["url"]
            print_web_fetch(url)
            text_content: str = fetch_web_page(url)
            add_to_llm_messages(messages, "tool", text_content, "", [], tool_call["id"])


def create_llm_messages(llm_system_messages: list[str]) -> list[DeepSeekRequestMessage]:
    llm_messages: list[DeepSeekRequestMessage] = []
    for llm_system_message in llm_system_messages:
        trimmed_system_message: str = llm_system_message.strip()
        if len(trimmed_system_message) != 0:
            add_to_llm_messages(llm_messages, "system", trimmed_system_message)
    return llm_messages


def rewind_conversation(llm_messages: list[DeepSeekRequestMessage]) -> None:
    while len(llm_messages) != 0 and llm_messages[-1]["role"] != "user":
        del llm_messages[-1]
    if len(llm_messages) != 0:
        del llm_messages[-1]


def llm_chat_loop() -> None:
    llm_messages: list[DeepSeekRequestMessage] = []
    ui_startup()
    try:
        while True:
            user_input: str = get_user_input()
            if user_input == "/rewind":
                rewind_conversation(llm_messages)
            elif user_input == "/new":
                llm_messages = []
            else:
                if len(llm_messages) == 0:
                    llm_messages = create_llm_messages(get_system_messages())
                add_to_llm_messages(llm_messages, "user", user_input)
                while True:
                    llm_output, llm_output_reasoning, tool_calls, total_tokens = get_llm_output(
                        ENVIRONMENT["deepseek"], llm_messages
                    )
                    print_assistant_message(ENVIRONMENT["terminal"], total_tokens, llm_output, llm_output_reasoning)
                    add_to_llm_messages(llm_messages, "assistant", llm_output, llm_output_reasoning, tool_calls)
                    if len(tool_calls) != 0:
                        process_tool_calls(ENVIRONMENT["duckduckgo"], tool_calls, llm_messages)
                    else:
                        break
    except KeyboardInterrupt:
        ui_teardown()


def main() -> None:
    llm_chat_loop()


if __name__ == "__main__":
    main()
