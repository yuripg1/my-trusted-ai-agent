from pathlib import Path
from unittest.mock import patch

from tool.read_file import (
    ReadFileArguments,
    get_read_file_message,
    get_read_file_permission,
    get_read_file_read_path,
    read_file,
)


class TestGetReadFileMessage:
    """Tests for the `get_read_file_message` function"""

    def test_format(self) -> None:
        """Format the message correctly"""
        arguments: ReadFileArguments = {"path": "/some/file.txt"}
        assert get_read_file_message(arguments) == "Reading file at **/some/file.txt**"

    def test_format_with_start_line(self) -> None:
        """Format the message with a start line"""
        arguments: ReadFileArguments = {"path": "/some/file.txt", "start_line": 5}
        assert get_read_file_message(arguments) == "Reading file at **/some/file.txt** (from line **5**)"

    def test_format_with_end_line(self) -> None:
        """Format the message with an end line"""
        arguments: ReadFileArguments = {"path": "/some/file.txt", "end_line": 10}
        assert get_read_file_message(arguments) == "Reading file at **/some/file.txt** (up to line **10**)"

    def test_format_with_both(self) -> None:
        """Format the message with both start and end lines"""
        arguments: ReadFileArguments = {"path": "/some/file.txt", "start_line": 5, "end_line": 10}
        assert get_read_file_message(arguments) == "Reading file at **/some/file.txt** (lines **5** to **10**)"


class TestGetReadFilePermission:
    """Tests for the `get_read_file_permission` function"""

    def test_requires_approval(self) -> None:
        """Permission should require user approval when not in allowlist"""
        arguments: ReadFileArguments = {"path": "/some/file.txt"}
        assert get_read_file_permission(arguments, []) is False

    def test_path_in_allowlist(self) -> None:
        """Return True when the path is in the session allowlist"""
        arguments: ReadFileArguments = {"path": "/some/file.txt"}
        session_read_allowlist: list[str] = ["/some/file.txt"]
        assert get_read_file_permission(arguments, session_read_allowlist=session_read_allowlist) is True

    def test_path_not_in_allowlist(self) -> None:
        """Return False when the path is not in the session allowlist"""
        arguments: ReadFileArguments = {"path": "/some/file.txt"}
        session_read_allowlist: list[str] = ["/other/file.txt"]
        assert get_read_file_permission(arguments, session_read_allowlist=session_read_allowlist) is False

    def test_empty_allowlist(self) -> None:
        """Return False when the session allowlist is empty"""
        arguments: ReadFileArguments = {"path": "/some/file.txt"}
        session_read_allowlist: list[str] = []
        assert get_read_file_permission(arguments, session_read_allowlist=session_read_allowlist) is False


class TestGetReadFileReadPath:
    """Tests for the `get_read_file_read_path` function"""

    def test_permission_granted(self) -> None:
        """Return the path when permission was granted"""
        arguments: ReadFileArguments = {"path": "/some/file.txt"}
        result: str | None = get_read_file_read_path(arguments, tool_call_permission=True)
        assert result == "/some/file.txt"

    def test_permission_denied(self) -> None:
        """Return None when permission was denied"""
        arguments: ReadFileArguments = {"path": "/some/file.txt"}
        result: str | None = get_read_file_read_path(arguments, tool_call_permission=False)
        assert result is None


class TestReadFile:
    """Tests for the `read_file` tool"""

    def test_read_file_successfully(self, tmp_path: Path) -> None:
        """Read a file that exists"""
        target: Path = tmp_path.joinpath("file.txt")
        target.write_text("hello world")
        result: str = read_file(ReadFileArguments(path=str(target)))
        assert (
            result
            == f'<file_read path="{str(target)}">\n<number_of_read_lines>1</number_of_read_lines>\n<number_of_file_lines>1</number_of_file_lines>\n<content>\nhello world\n</content>\n</file_read>'
        )

    def test_read_file_not_found(self, tmp_path: Path) -> None:
        """Do not read a file that does not exist"""
        target: Path = tmp_path.joinpath("nonexistent")
        result: str = read_file(ReadFileArguments(path=str(target)))
        assert result == f'<file_read path="{str(target)}">\n<error>File not found</error>\n</file_read>'

    def test_permission_denied(self, tmp_path: Path) -> None:
        """Do not read a file due to permission error"""
        target: Path = tmp_path.joinpath("file.txt")
        target.write_text("content")
        with patch("builtins.open", side_effect=PermissionError("Permission error")):
            result: str = read_file(ReadFileArguments(path=str(target)))
            assert (
                result
                == f'<file_read path="{str(target)}">\n<error>Permission denied by the system</error>\n</file_read>'
            )

    def test_unknown_error(self, tmp_path: Path) -> None:
        """Do not read a file due to an exception"""
        target: Path = tmp_path.joinpath("file.txt")
        target.write_text("content")
        with patch("builtins.open", side_effect=Exception("Exception")):
            result: str = read_file(ReadFileArguments(path=str(target)))
            assert result == f'<file_read path="{str(target)}">\n<error>Could not read file</error>\n</file_read>'

    def test_reading_denied_by_user(self, tmp_path: Path) -> None:
        """Do not read a file due to being denied by the user"""
        target: Path = tmp_path.joinpath("file.txt")
        target.write_text("content")
        result: str = read_file(ReadFileArguments(path=str(target)), tool_call_permission=False)
        assert (
            result
            == f'<file_read path="{str(target)}">\n<error>File reading manually denied by the user</error>\n</file_read>'
        )

    def test_read_partial_range(self, tmp_path: Path) -> None:
        """Read a range of lines from a file"""
        target: Path = tmp_path.joinpath("file.txt")
        target.write_text("line1\nline2\nline3\nline4\nline5\n")
        start_line: int = 2
        end_line: int = 4
        result: str = read_file(ReadFileArguments(path=str(target), start_line=start_line, end_line=end_line))
        assert (
            result
            == f'<file_read path="{str(target)}" start_line="{start_line}" end_line="{end_line}">\n<number_of_read_lines>3</number_of_read_lines>\n<number_of_file_lines>5</number_of_file_lines>\n<content>\nline2\nline3\nline4\n</content>\n</file_read>'
        )

    def test_read_from_start_line(self, tmp_path: Path) -> None:
        """Read from a start line to the end of the file"""
        target: Path = tmp_path.joinpath("file.txt")
        target.write_text("line1\nline2\nline3\n")
        start_line: int = 2
        result: str = read_file(ReadFileArguments(path=str(target), start_line=start_line))
        assert (
            result
            == f'<file_read path="{str(target)}" start_line="{start_line}">\n<number_of_read_lines>2</number_of_read_lines>\n<number_of_file_lines>3</number_of_file_lines>\n<content>\nline2\nline3\n</content>\n</file_read>'
        )

    def test_read_up_to_end_line(self, tmp_path: Path) -> None:
        """Read from the beginning up to an end line"""
        target: Path = tmp_path.joinpath("file.txt")
        target.write_text("line1\nline2\nline3\n")
        end_line: int = 2
        result: str = read_file(ReadFileArguments(path=str(target), end_line=end_line))
        assert (
            result
            == f'<file_read path="{str(target)}" end_line="{end_line}">\n<number_of_read_lines>2</number_of_read_lines>\n<number_of_file_lines>3</number_of_file_lines>\n<content>\nline1\nline2\n</content>\n</file_read>'
        )

    def test_read_single_line(self, tmp_path: Path) -> None:
        """Read a single line from a file"""
        target: Path = tmp_path.joinpath("file.txt")
        target.write_text("line1\nline2\nline3\n")
        start_line: int = 2
        end_line: int = 2
        result: str = read_file(ReadFileArguments(path=str(target), start_line=start_line, end_line=end_line))
        assert (
            result
            == f'<file_read path="{str(target)}" start_line="{start_line}" end_line="{end_line}">\n<number_of_read_lines>1</number_of_read_lines>\n<number_of_file_lines>3</number_of_file_lines>\n<content>\nline2\n</content>\n</file_read>'
        )

    def test_read_crlf_file(self, tmp_path: Path) -> None:
        """Read partial content from a CRLF file (newlines are normalized to LF)"""
        target: Path = tmp_path.joinpath("file.txt")
        target.write_text("line1\r\nline2\r\nline3\r\n")
        start_line: int = 2
        end_line: int = 2
        result: str = read_file(ReadFileArguments(path=str(target), start_line=start_line, end_line=end_line))
        assert (
            result
            == f'<file_read path="{str(target)}" start_line="{start_line}" end_line="{end_line}">\n<number_of_read_lines>1</number_of_read_lines>\n<number_of_file_lines>3</number_of_file_lines>\n<content>\nline2\n</content>\n</file_read>'
        )

    def test_read_start_line_past_eof(self, tmp_path: Path) -> None:
        """Read with start_line beyond end of file returns 0 lines"""
        target: Path = tmp_path.joinpath("file.txt")
        target.write_text("line1\nline2\nline3\n")
        start_line: int = 5
        result: str = read_file(ReadFileArguments(path=str(target), start_line=start_line))
        assert (
            result
            == f'<file_read path="{str(target)}" start_line="{start_line}">\n<number_of_read_lines>0</number_of_read_lines>\n<number_of_file_lines>3</number_of_file_lines>\n<content>\n\n</content>\n</file_read>'
        )

    def test_read_end_line_beyond_file(self, tmp_path: Path) -> None:
        """Read with end_line beyond end of file returns fewer lines than requested"""
        target: Path = tmp_path.joinpath("file.txt")
        target.write_text("line1\nline2\nline3\n")
        end_line: int = 10
        result: str = read_file(ReadFileArguments(path=str(target), end_line=end_line))
        assert (
            result
            == f'<file_read path="{str(target)}" end_line="{end_line}">\n<number_of_read_lines>3</number_of_read_lines>\n<number_of_file_lines>3</number_of_file_lines>\n<content>\nline1\nline2\nline3\n</content>\n</file_read>'
        )

    def test_read_start_line_less_than_1(self, tmp_path: Path) -> None:
        """Do not read a file when start_line is less than 1"""
        target: Path = tmp_path.joinpath("file.txt")
        target.write_text("content")
        start_line: int = 0
        result: str = read_file(ReadFileArguments(path=str(target), start_line=start_line))
        assert (
            result
            == f'<file_read path="{str(target)}" start_line="{start_line}">\n<error>"start_line" must be greater than or equal to 1</error>\n</file_read>'
        )

    def test_read_end_line_less_than_1(self, tmp_path: Path) -> None:
        """Do not read a file when end_line is less than 1"""
        target: Path = tmp_path.joinpath("file.txt")
        target.write_text("content")
        end_line: int = 0
        result: str = read_file(ReadFileArguments(path=str(target), end_line=end_line))
        assert (
            result
            == f'<file_read path="{str(target)}" end_line="{end_line}">\n<error>"end_line" must be greater than or equal to 1</error>\n</file_read>'
        )

    def test_read_start_line_greater_than_end_line(self, tmp_path: Path) -> None:
        """Do not read a file when start_line is greater than end_line"""
        target: Path = tmp_path.joinpath("file.txt")
        target.write_text("content")
        start_line: int = 5
        end_line: int = 3
        result: str = read_file(ReadFileArguments(path=str(target), start_line=start_line, end_line=end_line))
        assert (
            result
            == f'<file_read path="{str(target)}" start_line="{start_line}" end_line="{end_line}">\n<error>"start_line" must be less than or equal to "end_line"</error>\n</file_read>'
        )
