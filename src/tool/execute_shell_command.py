from subprocess import CompletedProcess, run
from typing import Literal, Required, TypedDict

from tool.common import BaseToolCall, make_safe_code_fence


class ExecuteShellCommandArguments(TypedDict):
    command: Required[str]


class ExecuteShellCommandToolCall(BaseToolCall):
    tool_name: Required[Literal["execute_shell_command"]]
    arguments: Required[ExecuteShellCommandArguments]


def get_execute_shell_command_permission(arguments: ExecuteShellCommandArguments) -> bool:
    return False


def get_execute_shell_command_message(arguments: ExecuteShellCommandArguments) -> str:
    command_content: str = make_safe_code_fence(f"$ {arguments['command']}", "shell")
    return f"Executing shell command\n\n{command_content}"


def execute_shell_command(arguments: ExecuteShellCommandArguments, tool_call_permission: bool = True) -> str:
    output_entries: list[str] = []
    output_entries.append(f"<command>\n{arguments['command'].strip()}\n</command>")
    if not tool_call_permission:
        output_entries.append(
            "<error>Shell command execution manually denied by the user. The command was not executed</error>"
        )
    else:
        command_execution_result: CompletedProcess[str] = run(
            arguments["command"], shell=True, capture_output=True, text=True
        )
        trimmed_stdout = command_execution_result.stdout.strip()
        stdout_body: str = f"\n{trimmed_stdout}" if trimmed_stdout else ""
        output_entries.append(f"<stdout>{stdout_body}\n</stdout>")
        trimmed_stderr = command_execution_result.stderr.strip()
        stderr_body: str = f"\n{trimmed_stderr}" if trimmed_stderr else ""
        output_entries.append(f"<stderr>{stderr_body}\n</stderr>")
        output_entries.append(f"<exit_code>{command_execution_result.returncode}</exit_code>")
    joined_output_entries: str = "\n".join(output_entries)
    return f"<shell_command_execution>\n{joined_output_entries}\n</shell_command_execution>"
