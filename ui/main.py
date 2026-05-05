from typing import cast, Literal

from environment import Environment
from ui.terminal import TerminalUi

UiChannelType = Literal["terminal"]


class Ui:
    channel: UiChannelType
    terminal_ui: TerminalUi | None

    def __init__(self, environment: Environment) -> None:
        self.channel = cast(UiChannelType, environment.ui_channel)
        if self.channel == "terminal":
            self.terminal_ui = TerminalUi(show_reasoning=environment.show_reasoning)

    def get_system_instruction(self) -> str:
        if self.channel == "terminal" and self.terminal_ui is not None:
            return self.terminal_ui.get_system_instruction()
        else:
            return ""

    def startup(self) -> None:
        if self.channel == "terminal" and self.terminal_ui is not None:
            self.terminal_ui.startup()

    def teardown(self) -> None:
        if self.channel == "terminal" and self.terminal_ui is not None:
            self.terminal_ui.teardown()

    def get_user_input(self) -> str:
        if self.channel == "terminal" and self.terminal_ui is not None:
            return self.terminal_ui.get_user_input()
        else:
            return ""

    def display_assistant_message(self, total_tokens: int, message: str, reasoning: str = "") -> None:
        if self.channel == "terminal" and self.terminal_ui is not None:
            self.terminal_ui.display_assistant_message(total_tokens, message, reasoning)

    def display_tool_call_message(self, function_call_message: str, function_call_permission) -> bool:
        if self.channel == "terminal" and self.terminal_ui is not None:
            return self.terminal_ui.display_tool_call_message(function_call_message, function_call_permission)
        else:
            return False
