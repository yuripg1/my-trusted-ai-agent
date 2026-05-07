from sqlite3 import Connection

from ai.core import Ai
from database import close_db_connection, init_db, open_db_connection
from environment import Environment
from entities.session import Session
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
        f"By default, you must always reply using {environment.language} with proper grammar (unless you see the need to reply in a different language)",
        "By default, you must always reply using strict Markdown syntax with proper formatting (unless you see the need to reply in a different way)",
        'You are capable of running any bash commands on the user\'s system using the "run_bash_command" function',
        'You are capable of getting a random integer number using the "get_random_integer" function',
        'You are capable of searching the web using the "search_web" function',
        'You are capable of reading PDF documents (from the web or local) using the "read_pdf_document" function',
        'You are capable of fetching web pages using the "fetch_web_page" function',
        ui_system_instruction,
        get_bash_command_as_system_message("getent passwd ${USER}"),
        get_bash_command_as_system_message("uname -a"),
        get_bash_command_as_system_message("cat /etc/os-release"),
        get_bash_command_as_system_message("hostnamectl"),
        get_bash_command_as_system_message("date"),
    ]
    return system_messages


def ai_chat_loop(environment: Environment, db_connection: Connection, ai: Ai, ui: Ui) -> None:
    session: Session = Session(ai)
    ui.startup()
    try:
        while True:
            session_id, context_length = session.get_info()
            user_input: str = ui.get_user_input(session_id, context_length)
            if user_input == "/new":
                session = Session(ai)
            elif user_input.startswith("/load "):
                referenced_session_id = int(user_input.split(" ")[1])
                session = Session(ai).load(ai, referenced_session_id, db_connection)
            elif user_input == "/rewind":
                session.rewind_message(ai)
            else:
                if session.is_messages_empty(ai):
                    session.add_system_messages(ai, get_system_messages(environment, ui.get_system_instruction()))
                has_added_user_message: bool = session.add_user_message(ai, user_input)
                if not has_added_user_message:
                    continue
                while True:
                    session.request_assistant_reply(ai)
                    session_id, context_length = session.get_info()
                    message, reasoning = session.get_latest_message(ai)
                    ui.display_assistant_message(session_id, context_length, message, reasoning)
                    tool_calls: list[ToolCall] = session.get_tool_calls_from_latest_message(ai)
                    if len(tool_calls) == 0:
                        break
                    for tool_call in tool_calls:
                        tool_call_message: str = get_tool_call_message(tool_call)
                        default_tool_call_permission: bool = get_default_tool_call_permission(tool_call)
                        final_tool_call_permission: bool = ui.display_tool_call_message(
                            session_id, context_length, tool_call_message, default_tool_call_permission
                        )
                        tool_call_output: str = execute_tool_call(tool_call, final_tool_call_permission)
                        has_added_tool_call: bool = session.add_tool_call(ai, tool_call, tool_call_output)
                        if not has_added_tool_call:
                            break
                session.auto_save(ai, db_connection)
    except KeyboardInterrupt:
        ui.teardown()


def main() -> None:
    environment = Environment()
    db_connection = open_db_connection(environment.db_path)
    init_db(db_connection)
    ai = Ai(environment)
    ui = Ui(environment)
    ai_chat_loop(environment, db_connection, ai, ui)
    close_db_connection


if __name__ == "__main__":
    main()
