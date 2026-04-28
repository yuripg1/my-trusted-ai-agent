import random
import requests
from rich import console as rich_console, markdown as rich_markdown
import time
import typing
import subprocess
import json

FunctionType = typing.Literal["function"]
RoleType = typing.Literal["assistant", "tool", "user", "system"]
ToolChoiceType = typing.Literal["auto"]
DeepSeekModelType = typing.Literal["deepseek-v4-flash", "deepseek-v4-pro"]
DeepSeekThinkingType = typing.Literal["enabled", "disabled"]
DeepSeekReasoningEffortType = typing.Literal["high", "max"]


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


API_KEY: str = ""
BASE_URL: str = "https://api.deepseek.com"
MAX_TOKENS: int = 393216
TOOL_CHOICE: ToolChoiceType = "auto"
STREAM: bool = False
WAIT_AFTER_ERROR: int = 2

MODEL: DeepSeekModelType = "deepseek-v4-flash"
# MODEL: DeepSeekModelType = "deepseek-v4-pro"

THINKING: DeepSeekThinkingType = "disabled"
# THINKING: DeepSeekThinkingType = "enabled"

REASONING_EFFORT: DeepSeekReasoningEffortType = "high"
# REASONING_EFFORT: DeepSeekReasoningEffortType = "max"

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
]


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
    f"$ {SYSTEM_COMMAND_1}\n\n{get_formatted_command_output(SYSTEM_COMMAND_STDOUT_1, SYSTEM_COMMAND_STDERR_1, SYSTEM_COMMAND_RETURNCODE_1)}",
    f"$ {SYSTEM_COMMAND_2}\n\n{get_formatted_command_output(SYSTEM_COMMAND_STDOUT_2, SYSTEM_COMMAND_STDERR_2, SYSTEM_COMMAND_RETURNCODE_2)}",
    f"$ {SYSTEM_COMMAND_3}\n\n{get_formatted_command_output(SYSTEM_COMMAND_STDOUT_3, SYSTEM_COMMAND_STDERR_3, SYSTEM_COMMAND_RETURNCODE_3)}",
    f"$ {SYSTEM_COMMAND_4}\n\n{get_formatted_command_output(SYSTEM_COMMAND_STDOUT_4, SYSTEM_COMMAND_STDERR_4, SYSTEM_COMMAND_RETURNCODE_4)}",
    f"$ {SYSTEM_COMMAND_5}\n\n{get_formatted_command_output(SYSTEM_COMMAND_STDOUT_5, SYSTEM_COMMAND_STDERR_5, SYSTEM_COMMAND_RETURNCODE_5)}",
]


def get_llm_output(
    llm_base_url: str,
    llm_api_key: str,
    llm_model: DeepSeekModelType,
    llm_messages: list[DeepSeekRequestMessage],
    llm_thinking: DeepSeekThinkingType,
    llm_reasoning_effort: DeepSeekReasoningEffortType,
    llm_max_tokens: int,
    llm_tools: list[typing.Dict[str, typing.Any]],
    llm_tool_choice: ToolChoiceType,
    llm_stream: bool,
    llm_wait_after_error: int,
) -> tuple[str, str, list[ToolCall]]:
    headers: typing.Mapping[str, str] = {"Authorization": f"Bearer {llm_api_key}", "Content-Type": "application/json"}
    payload_thinking: DeepSeekRequestThinking = {"type": llm_thinking}
    payload: DeepSeekRequest = {
        "model": llm_model,
        "messages": llm_messages,
        "thinking": payload_thinking,
        "max_tokens": llm_max_tokens,
        "stream": llm_stream,
        "tools": llm_tools,
        "tool_choice": llm_tool_choice,
    }
    if llm_thinking == "enabled":
        payload["reasoning_effort"] = llm_reasoning_effort
    response = requests.post(f"{llm_base_url}/chat/completions", headers=headers, json=payload)
    if response.status_code != 200:
        if response.status_code >= 500 and response.status_code <= 599:
            time.sleep(llm_wait_after_error)
            return get_llm_output(
                llm_base_url,
                llm_api_key,
                llm_model,
                llm_messages,
                llm_thinking,
                llm_reasoning_effort,
                llm_max_tokens,
                llm_tools,
                llm_tool_choice,
                llm_stream,
                llm_wait_after_error,
            )
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
        f"------------------------------------- TOOL -------------------------------------\n{command}\n\nPress ENTER to continue..."
    )


def print_random_integer(min_integer: int, max_integer: int) -> None:
    print(
        f'------------------------------------- TOOL -------------------------------------\nPicking a random integer between "{min_integer}" (inclusive) and "{max_integer}" (inclusive)\n',
        end="",
    )


def process_tool_calls(tool_calls: list[ToolCall], messages: list[DeepSeekRequestMessage]) -> None:
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
        print(f"---------------------------- ASSISTANT (reasoning) -----------------------------\n", end="")
        rich_console_instance.print(rich_markdown.Markdown(reasoning))
    if len(message) != 0:
        print(f"---------------------------------- ASSISTANT -----------------------------------\n", end="")
        rich_console_instance.print(rich_markdown.Markdown(message))


def main() -> None:
    llm_messages = create_llm_messages(SYSTEM_MESSAGES)
    try:
        while True:
            llm_input = input(
                "------------------------------------- USER -------------------------------------\n> "
            ).strip()
            if len(llm_input) == 0:
                continue
            if llm_input == "/rewind":
                del llm_messages[-1]
            else:
                add_to_llm_messages(llm_messages, "user", llm_input)
            while True:
                llm_output, llm_output_reasoning, tool_calls = get_llm_output(
                    BASE_URL,
                    API_KEY,
                    MODEL,
                    llm_messages,
                    THINKING,
                    REASONING_EFFORT,
                    MAX_TOKENS,
                    TOOLS,
                    TOOL_CHOICE,
                    STREAM,
                    WAIT_AFTER_ERROR,
                )
                print_message(llm_output, llm_output_reasoning)
                add_to_llm_messages(llm_messages, "assistant", llm_output, llm_output_reasoning, tool_calls)
                if len(tool_calls) != 0:
                    process_tool_calls(tool_calls, llm_messages)
                else:
                    break
    except KeyboardInterrupt:
        print("\n--------------------------------------------------------------------------------\n", end="")


if __name__ == "__main__":
    main()
