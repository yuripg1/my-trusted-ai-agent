from typing import Literal, NotRequired, Required, TypedDict

from tool.common import BaseToolCall


class ReadFileArguments(TypedDict):
    path: Required[str]
    start_line: NotRequired[int]
    end_line: NotRequired[int]


class ReadFileToolCall(BaseToolCall):
    tool_name: Required[Literal["read_file"]]
    arguments: Required[ReadFileArguments]


def get_read_file_message(arguments: ReadFileArguments) -> str:
    start_line = arguments.get("start_line")
    end_line = arguments.get("end_line")
    if start_line is not None and end_line is not None:
        return f"Reading file at **{arguments['path']}** (lines **{start_line}** to **{end_line}**)"
    elif start_line is not None:
        return f"Reading file at **{arguments['path']}** (from line **{start_line}**)"
    elif end_line is not None:
        return f"Reading file at **{arguments['path']}** (up to line **{end_line}**)"
    else:
        return f"Reading file at **{arguments['path']}**"


def get_read_file_permission(arguments: ReadFileArguments, session_read_allowlist: list[str]) -> bool:
    if arguments["path"] in session_read_allowlist:
        return True
    else:
        return False


def get_read_file_read_path(arguments: ReadFileArguments, tool_call_permission: bool) -> str | None:
    if tool_call_permission:
        return arguments["path"]
    else:
        return None


def read_file(arguments: ReadFileArguments, tool_call_permission: bool = True) -> str:
    output_entries: list[str] = []
    start_line: int | None = arguments.get("start_line", None)
    end_line: int | None = arguments.get("end_line", None)
    if not tool_call_permission:
        output_entries.append("<error>File reading manually denied by the user</error>")
    else:
        try:
            if start_line is not None and start_line < 1:
                output_entries.append('<error>"start_line" must be greater than or equal to 1</error>')
            elif end_line is not None and end_line < 1:
                output_entries.append('<error>"end_line" must be greater than or equal to 1</error>')
            elif start_line is not None and end_line is not None and start_line > end_line:
                output_entries.append('<error>"start_line" must be less than or equal to "end_line"</error>')
            else:
                number_of_read_lines: int = 0
                number_of_file_lines: int = 0
                file_content: str = ""
                with open(arguments["path"]) as file:
                    file_content = file.read()
                file_lines: list[str] = file_content.splitlines()
                number_of_file_lines = len(file_lines)
                if start_line is not None or end_line is not None:
                    start_index: int = (start_line - 1) if start_line is not None else 0
                    end_index: int = end_line if end_line is not None else len(file_lines)
                    read_lines: list[str] = file_lines[start_index:end_index]
                    number_of_read_lines = len(read_lines)
                    file_content = "\n".join(read_lines)
                else:
                    number_of_read_lines = number_of_file_lines
                output_entries.append(f"<number_of_read_lines>{number_of_read_lines}</number_of_read_lines>")
                output_entries.append(f"<number_of_file_lines>{number_of_file_lines}</number_of_file_lines>")
                output_entries.append(f"<content>\n{file_content}\n</content>")
        except FileNotFoundError:
            output_entries.append("<error>File not found</error>")
        except PermissionError:
            output_entries.append("<error>Permission denied by the system</error>")
        except Exception:
            output_entries.append("<error>Could not read file</error>")
    tag_attributes: str = f'path="{arguments["path"]}"'
    if start_line is not None:
        tag_attributes += f' start_line="{start_line}"'
    if end_line is not None:
        tag_attributes += f' end_line="{end_line}"'
    joined_output_entries: str = "\n".join(output_entries)
    return f"<file_read {tag_attributes}>\n{joined_output_entries}\n</file_read>"
