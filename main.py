from ai.main import Ai
from ai.deepseek import DeepSeekToolCall, DeepSeekMessage
from environment import Environment
from function import (
    execute_function_call,
    execute_bash_command,
    get_formatted_bash_command_output,
    get_function_call_message,
    get_default_function_call_permission,
)
from ui.main import Ui


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
    if ai.provider == "deepseek":
        deepseek_messages: list[DeepSeekMessage] = ai.create_deepseek_messages()
        ui.startup()
        try:
            while True:
                user_input: str = ui.get_user_input()
                if user_input == "/rewind":
                    ai.rewind_message(deepseek_messages=deepseek_messages)
                elif user_input == "/new":
                    deepseek_messages.clear()
                else:
                    if len(deepseek_messages) == 0:
                        ai.initialize_messages(
                            system_messages=get_system_messages(environment, ui.get_system_instruction()),
                            deepseek_messages=deepseek_messages,
                        )
                    ai.add_to_messages(
                        deepseek_messages=deepseek_messages, deepseek_role="user", deepseek_content=user_input
                    )
                    while True:
                        total_tokens: int = ai.request_reply(deepseek_messages=deepseek_messages)
                        assistant_message = deepseek_messages[-1]
                        reasoning_content: str = ""
                        if "reasoning_content" in assistant_message:
                            reasoning_content = assistant_message["reasoning_content"]
                        ui.display_assistant_message(total_tokens, assistant_message["content"], reasoning_content)
                        if "tool_calls" not in assistant_message or len(assistant_message["tool_calls"]) == 0:
                            break
                        deepseek_tool_calls: list[DeepSeekToolCall] = assistant_message["tool_calls"]
                        for deepseek_tool_call in deepseek_tool_calls:
                            function_call = ai.decode_tool_call(deepseek_tool_call=deepseek_tool_call)
                            if function_call is not None:
                                function_call_message: str = get_function_call_message(function_call)
                                default_function_call_permission: bool = get_default_function_call_permission(
                                    function_call
                                )
                                final_function_call_permission: bool = ui.display_tool_call_message(
                                    function_call_message, default_function_call_permission
                                )
                                tool_message: str = execute_function_call(function_call, final_function_call_permission)
                                if len(tool_message) != 0:
                                    ai.add_to_messages(
                                        deepseek_messages,
                                        "tool",
                                        tool_message,
                                        "",
                                        [],
                                        function_call["info"]["tool_call_id"],
                                    )
        except KeyboardInterrupt:
            ui.teardown()


def main() -> None:
    environment = Environment()
    ai = Ai(environment)
    ui = Ui(environment)
    ai_chat_loop(environment, ai, ui)


if __name__ == "__main__":
    main()
