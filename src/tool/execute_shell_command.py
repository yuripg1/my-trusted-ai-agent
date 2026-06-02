from subprocess import CompletedProcess, run
from typing import Literal, Required, TypedDict

from tool.common import BaseToolCall, make_safe_code_fence, make_xml_tag


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
    output_entries.append(make_xml_tag("command", arguments["command"].strip()))
    if not tool_call_permission:
        output_entries.append(
            "<error>Shell command execution manually denied by the user. The command was not executed</error>"
        )
    else:
        command_execution_result: CompletedProcess[str] = run(
            arguments["command"], shell=True, capture_output=True, text=True
        )
        output_entries.append(make_xml_tag("stdout", command_execution_result.stdout.strip()))
        output_entries.append(make_xml_tag("stderr", command_execution_result.stderr.strip()))
        output_entries.append(f"<exit_code>{command_execution_result.returncode}</exit_code>")
    joined_output_entries: str = "\n".join(output_entries)
    return f"<shell_command_execution>\n{joined_output_entries}\n</shell_command_execution>"
