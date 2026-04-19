import requests
import typing
import subprocess
import json

FunctionType = typing.Literal["function"]
ModelType = typing.Literal["deepseek-chat", "deepseek-reasoner"]
RoleType = typing.Literal["assistant", "tool", "user", "system"]
ToolChoiceType = typing.Literal["auto"]


class ToolCallFunction(typing.TypedDict):
    name: typing.Required[str]
    arguments: typing.Required[str]


class ToolCall(typing.TypedDict):
    id: typing.Required[str]
    type: typing.Required[FunctionType]
    function: typing.Required[ToolCallFunction]


class DeepSeekMessage(typing.TypedDict):
    role: typing.Required[RoleType]
    content: typing.NotRequired[str]
    reasoning_content: typing.NotRequired[str]
    tool_calls: typing.NotRequired[list[ToolCall]]
    tool_call_id: typing.NotRequired[str]


class DeepSeekRequest(typing.TypedDict):
    model: typing.Required[ModelType]
    messages: list[DeepSeekMessage]
    max_tokens: typing.Required[int]
    stream: typing.Required[bool]
    temperature: typing.Required[float]
    tools: typing.NotRequired[list[typing.Dict[str, typing.Any]]]
    tool_choice: typing.NotRequired[str]


API_KEY: str = ""
BASE_URL: str = "https://api.deepseek.com"

MODEL: ModelType = "deepseek-chat"
MAX_TOKENS: int = 8192

# MODEL: ModelType = "deepseek-reasoner"
# MAX_TOKENS: int = 65536

# TEMPERATURE: float = 0.0
TEMPERATURE: float = 1.0
# TEMPERATURE: float = 1.3
# TEMPERATURE: float = 1.5

TOOL_CHOICE: ToolChoiceType = "auto"

SYSTEM_MESSAGES: list[str] = []

TOOLS: list[typing.Dict[str, typing.Any]] = [
    {
        "type": "function",
        "function": {
            "name": "run_bash",
            "description": "Run any bash command",
            "parameters": {
                "type": "object",
                "properties": {"command": {"type": "string", "description": "The bash command to run"}},
                "required": ["command"],
                "additionalProperties": False,
            },
        },
    }
]


def get_llm_output(
    llm_base_url: str,
    llm_api_key: str,
    llm_model: ModelType,
    llm_messages: list[DeepSeekMessage],
    llm_max_tokens: int,
    llm_temperature: float,
    llm_tools: list[typing.Dict[str, typing.Any]],
    llm_tool_choice: ToolChoiceType,
) -> tuple[str, str, list[ToolCall]]:
    headers: typing.Mapping[str, str] = {"Authorization": f"Bearer {llm_api_key}", "Content-Type": "application/json"}
    payload: DeepSeekRequest = {
        "model": llm_model,
        "messages": llm_messages,
        "max_tokens": llm_max_tokens,
        "stream": False,
        "temperature": llm_temperature,
        "tools": llm_tools,
        "tool_choice": llm_tool_choice,
    }
    response = requests.post(f"{llm_base_url}/chat/completions", headers=headers, json=payload)
    data = response.json()
    if response.status_code != 200:
        print(json.dumps(payload, indent=2))
        print(response.status_code)
        print(json.dumps(data, indent=2))
    message = data["choices"][0]["message"]
    content = message.get("content", "").strip()
    reasoning_content = message.get("reasoning_content", "").strip()
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
    llm_messages: list[DeepSeekMessage],
    role: RoleType,
    content: str,
    reasoning_content: str = "",
    tool_calls: list[ToolCall] = [],
    tool_call_id: str = "",
) -> None:
    trimmed_content: str = content.strip()
    trimmed_reasoning_content: str = reasoning_content.strip()
    if role in ["system", "user"]:
        new_message: DeepSeekMessage = {"role": role, "content": trimmed_content}
        llm_messages.append(new_message)
    elif role == "assistant":
        new_assistant_message: DeepSeekMessage = {"role": role, "content": trimmed_content}
        if len(trimmed_reasoning_content) != 0:
            new_assistant_message["reasoning_content"] = trimmed_reasoning_content
        if len(tool_calls) != 0:
            new_assistant_message["tool_calls"] = tool_calls
        llm_messages.append(new_assistant_message)
    elif role == "tool":
        new_tool_message: DeepSeekMessage = {"role": role, "content": trimmed_content, "tool_call_id": tool_call_id}
        llm_messages.append(new_tool_message)


def execute_bash_command(command: str) -> tuple[str, str, int]:
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout, result.stderr, result.returncode


def print_command(command: str) -> None:
    input(f"Tool $ {command}\n\nPress ENTER to continue...")


def process_tool_calls(tool_calls: list[ToolCall], messages: list[DeepSeekMessage]) -> None:
    for tool_call in tool_calls:
        if tool_call["function"]["name"] == "run_bash":
            command: str = ""
            args = json.loads(tool_call["function"]["arguments"])
            command = args["command"]
            print_command(command)
            stdout, stderr, returncode = execute_bash_command(command)
            result_parts = []
            if stdout:
                result_parts.append(f"stdout:\n{stdout}")
            if stderr:
                result_parts.append(f"stderr:\n{stderr}")
            result_parts.append(f"returncode: {returncode}")
            result = "\n---\n".join(result_parts)
            add_to_llm_messages(messages, "tool", result, "", [], tool_call["id"])


def create_llm_messages(llm_system_messages: list[str]) -> list[DeepSeekMessage]:
    llm_messages: list[DeepSeekMessage] = []
    for llm_system_message in llm_system_messages:
        add_to_llm_messages(llm_messages, "system", llm_system_message.strip())
    return llm_messages


def print_message(message: str, reasoning: str = "") -> None:
    if len(reasoning) != 0 and len(message) != 0:
        print(f"\nAssistant * {reasoning}\n\nAssistant > {message}\n")
    elif len(reasoning) != 0:
        print(f"\nAssistant * {reasoning}\n")
    elif len(message) != 0:
        print(f"\nAssistant > {message}\n")


def main() -> None:
    llm_messages = create_llm_messages(SYSTEM_MESSAGES)
    try:
        while True:
            llm_input = input("User > ").strip()
            if len(llm_input) == 0:
                continue
            add_to_llm_messages(llm_messages, "user", llm_input)
            while True:
                llm_output, llm_output_reasoning, tool_calls = get_llm_output(
                    BASE_URL, API_KEY, MODEL, llm_messages, MAX_TOKENS, TEMPERATURE, TOOLS, TOOL_CHOICE
                )
                print_message(llm_output, llm_output_reasoning)
                add_to_llm_messages(llm_messages, "assistant", llm_output, llm_output_reasoning, tool_calls)
                if len(tool_calls) != 0:
                    process_tool_calls(tool_calls, llm_messages)
                else:
                    break
            print("--------------------------------------------------------------------------------\n")
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
