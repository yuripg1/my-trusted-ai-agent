from rich.console import Console
from rich.markdown import Markdown


class TerminalUi:
    show_reasoning: bool

    def __init__(self, show_reasoning: bool) -> None:
        self.show_reasoning = show_reasoning

    def get_system_instruction(self) -> str:
        return "You are an AI assistant operating in a text-only terminal interface"

    def startup(self) -> None:
        print("\n", end="")

    def teardown(self) -> None:
        print("\n\n--------------------------------------------------------------------------------\n\n", end="")

    def get_user_input(self) -> str:
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

    def display_assistant_message(self, total_tokens: int, message: str, reasoning: str = "") -> None:
        rich_console_instance = Console(no_color=True)
        if self.show_reasoning and len(reasoning) != 0:
            print(
                f"-------------------- ASSISTANT (reasoning) -------------------- ({total_tokens:>7} tokens)\n\n",
                end="",
            )
            rich_console_instance.print(Markdown(reasoning))
            print("\n", end="")
        if len(message) != 0:
            print(
                f"-------------------------- ASSISTANT -------------------------- ({total_tokens:>7} tokens)\n\n",
                end="",
            )
            rich_console_instance.print(Markdown(message))
            print("\n", end="")

    def display_tool_call_message(self, tool_call_message: str, tool_call_permission: bool) -> bool:
        print(
            f"------------------------------------- TOOL -------------------------------------\n\n{tool_call_message}\n\n",
            end="",
        )
        if tool_call_permission:
            return True
        try:
            input("Press ENTER to continue...")
            print("\n", end="")
            return True
        except KeyboardInterrupt:
            print("\n\n", end="")
            return False
