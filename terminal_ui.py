from rich import console as rich_console, markdown as rich_markdown
import typing


class TerminalEnvironment(typing.TypedDict):
    show_reasoning: typing.Required[bool]


def get_system_instruction() -> str:
    return "You are an AI assistant operating in a text-only terminal interface"


def startup() -> None:
    print("\n", end="")


def teardown() -> None:
    print("\n\n--------------------------------------------------------------------------------\n\n", end="")


def get_user_input() -> str:
    print("------------------------------------- USER -------------------------------------\n\n", end="")
    user_input_lines: list[str] = []
    capturing_user_input: bool = True
    while capturing_user_input:
        user_input: str = input("> ").strip()
        if len(user_input) != 0:
            if user_input[-1] == "\\":
                user_input = user_input[:-1].strip()
            else:
                capturing_user_input = False
            user_input_lines.append(user_input)
        elif len(user_input_lines) != 0:
            capturing_user_input = False
    print("\n", end="")
    return "\n".join(user_input_lines).strip()


def print_assistant_message(
    terminal_environment: TerminalEnvironment, total_tokens: int, message: str, reasoning: str = ""
) -> None:
    rich_console_instance = rich_console.Console(no_color=True)
    if terminal_environment["show_reasoning"] and len(reasoning) != 0:
        print(f"----------------------- ASSISTANT (reasoning) ------------------------ ({total_tokens:>7})\n\n", end="")
        rich_console_instance.print(rich_markdown.Markdown(reasoning))
        print("\n", end="")
    if len(message) != 0:
        print(f"----------------------------- ASSISTANT ------------------------------ ({total_tokens:>7})\n\n", end="")
        rich_console_instance.print(rich_markdown.Markdown(message))
        print("\n", end="")


def prompt_for_bash_command_permission(command: str) -> bool:
    print(f"------------------------------------- TOOL -------------------------------------\n\n{command}\n\n", end="")
    permission_granted: bool = False
    try:
        input("Press ENTER to continue...")
        print("\n", end="")
        permission_granted = True
    except KeyboardInterrupt:
        print("\n\n", end="")
        permission_granted = False
    return permission_granted


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
