from ai.core import Ai, AiMessages
from environment import Environment
from tool_calling import (
    ToolCall,
    execute_bash_command,
    execute_tool_call,
    get_default_tool_call_permission,
    get_formatted_bash_command_output,
    get_tool_call_message,
)
from ui.core import Ui


def get_bash_command_as_system_message(command: str) -> str:
    stdout, stderr, returncode = execute_bash_command(True, command)
    return get_formatted_bash_command_output(command, True, stdout, stderr, returncode)


def get_system_messages(environment: Environment, ui_system_instruction: str) -> list[str]:
    system_messages: list[str] = [
        f"You must always reply using {environment.language} with proper grammar",
        "You must always reply using strict Markdown syntax with proper formatting",
        'You are capable of running any bash commands on the user\'s system using the "run_bash_command" function',
        'You are capable of getting a random integer number using the "get_random_integer" function',
        'You are capable of searching the web using the "web_search" function',
        'You are capable of fetching web pages using the "web_fetch" function',
        ui_system_instruction,
        get_bash_command_as_system_message("getent passwd ${USER}"),
        get_bash_command_as_system_message("uname -a"),
        get_bash_command_as_system_message("cat /etc/os-release"),
        get_bash_command_as_system_message("hostnamectl"),
        get_bash_command_as_system_message("date"),
    ]
    return system_messages


def ai_chat_loop(environment: Environment, ai: Ai, ui: Ui) -> None:
    messages: AiMessages = ai.create_messages()
    ui.startup()
    try:
        while True:
            user_input: str = ui.get_user_input()
            if user_input == "/rewind":
                ai.rewind_message(messages)
            elif user_input == "/new":
                messages = ai.create_messages()
            else:
                if ai.is_messages_empty(messages):
                    ai.initialize_messages(messages, get_system_messages(environment, ui.get_system_instruction()))
                has_added_user_message: bool = ai.add_user_message(messages, user_input)
                if not has_added_user_message:
                    continue
                while True:
                    total_tokens: int = ai.request_reply(messages)
                    message, reasoning = ai.get_latest_message(messages)
                    ui.display_assistant_message(total_tokens, message, reasoning)
                    tool_calls: list[ToolCall] = ai.get_tool_calls_from_latest_message(messages)
                    if len(tool_calls) == 0:
                        break
                    for tool_call in tool_calls:
                        tool_call_message: str = get_tool_call_message(tool_call)
                        default_tool_call_permission: bool = get_default_tool_call_permission(tool_call)
                        final_tool_call_permission: bool = ui.display_tool_call_message(
                            tool_call_message, default_tool_call_permission
                        )
                        tool_call_output: str = execute_tool_call(tool_call, final_tool_call_permission)
                        has_added_tool_call: bool = ai.add_tool_call(messages, tool_call, tool_call_output)
                        if not has_added_tool_call:
                            break
    except KeyboardInterrupt:
        ui.teardown()


def main() -> None:
    environment = Environment()
    ai = Ai(environment)
    ui = Ui(environment)
    ai_chat_loop(environment, ai, ui)


if __name__ == "__main__":
    main()
