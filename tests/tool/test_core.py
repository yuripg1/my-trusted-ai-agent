from tool.core import (
    execute_tool_call,
    get_group_tool_call_messages,
    get_individual_tool_call_message,
    get_individual_tool_call_permission,
    get_number_of_required_permissions,
    get_tool_read_path,
    get_tool_system_instructions,
)


class TestGetToolSystemInstruction:
    """Tests for the `get_tool_system_instruction` function"""

    def test_return_value(self) -> None:
        """Return the expected system instruction"""
        assert get_tool_system_instructions() == [
            "You have access to tools",
            "When you issue many tool calls in one go, they are executed sequentially and in order",
            "Whenever possible, you should strongly prioritize issuing as many tool calls as possible in one go instead of issuing them one by one",
        ]


class TestGetIndividualToolCallMessage:
    """Tests for the `get_individual_tool_call_message` dispatching function"""

    def test_create_directory(self) -> None:
        """Dispatch to the correct message function for create_directory"""
        result: str = get_individual_tool_call_message(
            {"tool_name": "create_directory", "arguments": {"path": "/tmp/test_dir"}}
        )
        assert result == "Creating directory at **/tmp/test_dir**"

    def test_delete_path(self) -> None:
        """Dispatch to the correct message function for delete_path"""
        result: str = get_individual_tool_call_message(
            {"tool_name": "delete_path", "arguments": {"type": "file", "path": "/tmp/test.txt"}}
        )
        assert result == "Deleting **/tmp/test.txt** (**file**)"

    def test_edit_file(self) -> None:
        """Dispatch to the correct message function for edit_file"""
        result: str = get_individual_tool_call_message(
            {
                "tool_name": "edit_file",
                "arguments": {
                    "path": "/tmp/test.txt",
                    "search_for": "old text",
                    "replace_with": "new text",
                    "number_of_substitutions": 1,
                },
            }
        )
        expected: str = "Editing file at **/tmp/test.txt** (**1** substitutions)\n\n```diff\n--- /tmp/test.txt\n+++ /tmp/test.txt\n@@ -1 +1 @@\n-old text\n+new text\n```"
        assert result == expected

    def test_execute_shell_command(self) -> None:
        """Dispatch to the correct message function for execute_shell_command"""
        result: str = get_individual_tool_call_message(
            {"tool_name": "execute_shell_command", "arguments": {"command": "ls -la"}}
        )
        assert result == "Executing shell command\n\n```shell\n$ ls -la\n```"

    def test_generate_random_integer(self) -> None:
        """Dispatch to the correct message function for generate_random_integer"""
        result: str = get_individual_tool_call_message(
            {"tool_name": "generate_random_integer", "arguments": {"min": 1, "max": 10}}
        )
        assert result == "Generating a random integer between **1** and **10**"

    def test_invalid(self) -> None:
        """Dispatch to the correct message function for invalid"""
        result: str = get_individual_tool_call_message(
            {
                "tool_name": "invalid",
                "arguments": {"tool_name": "write_file", "error_message": "Missing required argument: 'path'"},
            }
        )
        assert result == "Skipping invalid tool call **write_file**"

    def test_list_directory(self) -> None:
        """Dispatch to the correct message function for list_directory"""
        result: str = get_individual_tool_call_message({"tool_name": "list_directory", "arguments": {"path": "/tmp"}})
        assert result == "Listing directory at **/tmp**"

    def test_move_path(self) -> None:
        """Dispatch to the correct message function for move_path"""
        result: str = get_individual_tool_call_message(
            {
                "tool_name": "move_path",
                "arguments": {"type": "file", "source": "/tmp/a.txt", "destination": "/tmp/b.txt"},
            }
        )
        assert result == "Moving **file** at **/tmp/a.txt** to **/tmp/b.txt**"

    def test_read_file(self) -> None:
        """Dispatch to the correct message function for read_file"""
        result: str = get_individual_tool_call_message(
            {"tool_name": "read_file", "arguments": {"path": "/tmp/test.txt"}}
        )
        assert result == "Reading file at **/tmp/test.txt**"

    def test_read_pdf_document(self) -> None:
        """Dispatch to the correct message function for read_pdf_document"""
        result: str = get_individual_tool_call_message(
            {
                "tool_name": "read_pdf_document",
                "arguments": {"location_type": "web", "location": "https://example.com/doc.pdf"},
            }
        )
        assert result == "Reading PDF document at **https://example.com/doc.pdf** (**web**)"

    def test_read_web_page(self) -> None:
        """Dispatch to the correct message function for read_web_page"""
        result: str = get_individual_tool_call_message(
            {"tool_name": "read_web_page", "arguments": {"url": "https://example.com"}}
        )
        assert result == "Reading web site at **https://example.com**"

    def test_search_web(self) -> None:
        """Dispatch to the correct message function for search_web"""
        result: str = get_individual_tool_call_message(
            {"tool_name": "search_web", "arguments": {"query": "test query", "max_results_per_page": 5}}
        )
        assert result == "Searching the web for **test query** (**5** results - page **1**)"

    def test_write_file(self) -> None:
        """Dispatch to the correct message function for write_file"""
        result: str = get_individual_tool_call_message(
            {
                "tool_name": "write_file",
                "arguments": {"path": "/tmp/test.txt", "mode": "create_or_overwrite", "content": "hello"},
            }
        )
        assert result == "Writing file at **/tmp/test.txt** (**create_or_overwrite** mode)\n\n```text\nhello\n```"

    def test_unknown_tool_name(self) -> None:
        """Return an error message for unknown tool names"""
        result: str = get_individual_tool_call_message({"tool_name": "unknown_tool", "arguments": {}})
        assert result == 'Error on "unknown_tool"'


class TestGetGroupToolCallMessages:
    """Tests for the `get_group_tool_call_messages` function"""

    def test_single_tool(self) -> None:
        """Return a list with a single message for one tool call"""
        result: list[str] = get_group_tool_call_messages(
            [{"tool_name": "generate_random_integer", "arguments": {"min": 1, "max": 10}}]
        )
        assert result == ["Generating a random integer between **1** and **10**"]

    def test_multiple_tools(self) -> None:
        """Return a list with messages for multiple tool calls, in order"""
        result: list[str] = get_group_tool_call_messages(
            [
                {"tool_name": "create_directory", "arguments": {"path": "/tmp/a"}},
                {"tool_name": "create_directory", "arguments": {"path": "/tmp/b"}},
            ]
        )
        assert result == [
            "Creating directory at **/tmp/a**",
            "Creating directory at **/tmp/b**",
        ]

    def test_empty_list(self) -> None:
        """Return an empty list for no tool calls"""
        result: list[str] = get_group_tool_call_messages([])
        assert result == []

    def test_unknown_tool_name(self) -> None:
        """Handle an unknown tool name in the group"""
        result: list[str] = get_group_tool_call_messages([{"tool_name": "unknown_tool", "arguments": {}}])
        assert result == ['Error on "unknown_tool"']


class TestGetIndividualToolCallPermission:
    """Tests for the `get_individual_tool_call_permission` dispatching function"""

    _empty_allowlist: list[str] = []

    def test_read_only_tools_are_auto_approved(self) -> None:
        """Read-only and low-risk tools should return True"""
        assert (
            get_individual_tool_call_permission(
                {"tool_name": "create_directory", "arguments": {"path": "/tmp/test"}}, self._empty_allowlist
            )
            is True
        )
        assert (
            get_individual_tool_call_permission(
                {"tool_name": "generate_random_integer", "arguments": {"min": 1, "max": 10}}, self._empty_allowlist
            )
            is True
        )
        assert (
            get_individual_tool_call_permission(
                {"tool_name": "invalid", "arguments": {"tool_name": "write_file", "error_message": "error"}},
                self._empty_allowlist,
            )
            is True
        )
        assert (
            get_individual_tool_call_permission(
                {"tool_name": "list_directory", "arguments": {"path": "/tmp"}}, self._empty_allowlist
            )
            is True
        )
        assert (
            get_individual_tool_call_permission(
                {
                    "tool_name": "read_pdf_document",
                    "arguments": {"location_type": "web", "location": "https://example.com/doc.pdf"},
                },
                self._empty_allowlist,
            )
            is True
        )
        assert (
            get_individual_tool_call_permission(
                {"tool_name": "read_web_page", "arguments": {"url": "https://example.com"}}, self._empty_allowlist
            )
            is True
        )
        assert (
            get_individual_tool_call_permission(
                {"tool_name": "search_web", "arguments": {"query": "test", "max_results_per_page": 5}},
                self._empty_allowlist,
            )
            is True
        )

    def test_destructive_tools_require_approval(self) -> None:
        """Potentially destructive or sensitive tools should return False"""
        assert (
            get_individual_tool_call_permission(
                {"tool_name": "delete_path", "arguments": {"type": "file", "path": "/tmp/test.txt"}},
                self._empty_allowlist,
            )
            is False
        )
        assert (
            get_individual_tool_call_permission(
                {
                    "tool_name": "edit_file",
                    "arguments": {
                        "path": "/tmp/test.txt",
                        "search_for": "a",
                        "replace_with": "b",
                        "number_of_substitutions": 1,
                    },
                },
                self._empty_allowlist,
            )
            is False
        )
        assert (
            get_individual_tool_call_permission(
                {"tool_name": "execute_shell_command", "arguments": {"command": "ls"}}, self._empty_allowlist
            )
            is False
        )
        assert (
            get_individual_tool_call_permission(
                {
                    "tool_name": "move_path",
                    "arguments": {"type": "file", "source": "/tmp/a.txt", "destination": "/tmp/b.txt"},
                },
                self._empty_allowlist,
            )
            is False
        )
        assert (
            get_individual_tool_call_permission(
                {"tool_name": "read_file", "arguments": {"path": "/tmp/test.txt"}}, self._empty_allowlist
            )
            is False
        )
        assert (
            get_individual_tool_call_permission(
                {"tool_name": "read_pdf_document", "arguments": {"location_type": "local", "location": "/tmp/doc.pdf"}},
                self._empty_allowlist,
            )
            is False
        )
        assert (
            get_individual_tool_call_permission(
                {
                    "tool_name": "write_file",
                    "arguments": {"path": "/tmp/test.txt", "mode": "create_or_overwrite", "content": "hello"},
                },
                self._empty_allowlist,
            )
            is False
        )

    def test_unknown_tool_name(self) -> None:
        """Return False for unknown tool names"""
        assert (
            get_individual_tool_call_permission({"tool_name": "unknown_tool", "arguments": {}}, self._empty_allowlist)
            is False
        )

    def test_read_file_allowlisted_path(self) -> None:
        """Return True for read_file when the path is in the session allowlist"""
        result: bool = get_individual_tool_call_permission(
            {"tool_name": "read_file", "arguments": {"path": "/tmp/test.txt"}},
            session_read_allowlist=["/tmp/test.txt"],
        )
        assert result is True

    def test_read_file_not_allowlisted(self) -> None:
        """Return False for read_file when the path is not in the session allowlist"""
        result: bool = get_individual_tool_call_permission(
            {"tool_name": "read_file", "arguments": {"path": "/tmp/test.txt"}},
            session_read_allowlist=["/other/file.txt"],
        )
        assert result is False

    def test_read_pdf_document_allowlisted_local_path(self) -> None:
        """Return True for read_pdf_document when the local path is in the session allowlist"""
        result: bool = get_individual_tool_call_permission(
            {
                "tool_name": "read_pdf_document",
                "arguments": {"location_type": "local", "location": "/tmp/doc.pdf"},
            },
            session_read_allowlist=["/tmp/doc.pdf"],
        )
        assert result is True

    def test_read_pdf_document_not_allowlisted_local_path(self) -> None:
        """Return False for read_pdf_document when the local path is not in the session allowlist"""
        result: bool = get_individual_tool_call_permission(
            {
                "tool_name": "read_pdf_document",
                "arguments": {"location_type": "local", "location": "/tmp/doc.pdf"},
            },
            session_read_allowlist=["/other/doc.pdf"],
        )
        assert result is False

    def test_read_pdf_document_web_is_auto_approved_regardless_of_allowlist(self) -> None:
        """Return True for read_pdf_document web even without allowlist match"""
        result: bool = get_individual_tool_call_permission(
            {
                "tool_name": "read_pdf_document",
                "arguments": {"location_type": "web", "location": "https://example.com/doc.pdf"},
            },
            session_read_allowlist=[],
        )
        assert result is True


class TestGetNumberOfRequiredPermissions:
    """Tests for the `get_number_of_required_permissions` function"""

    _empty_allowlist: list[str] = []

    def test_all_auto_approved(self) -> None:
        """Return 0 when all tools are auto-approved"""
        result: int = get_number_of_required_permissions(
            [
                {"tool_name": "create_directory", "arguments": {"path": "/tmp/a"}},
                {"tool_name": "generate_random_integer", "arguments": {"min": 1, "max": 10}},
            ],
            self._empty_allowlist,
        )
        assert result == 0

    def test_all_require_approval(self) -> None:
        """Return the count when all tools require approval"""
        result: int = get_number_of_required_permissions(
            [
                {"tool_name": "delete_path", "arguments": {"type": "file", "path": "/tmp/a.txt"}},
                {
                    "tool_name": "write_file",
                    "arguments": {"path": "/tmp/b.txt", "mode": "create_or_overwrite", "content": "hello"},
                },
            ],
            self._empty_allowlist,
        )
        assert result == 2

    def test_mixed_permissions(self) -> None:
        """Return only the count of tools that require approval"""
        result: int = get_number_of_required_permissions(
            [
                {"tool_name": "create_directory", "arguments": {"path": "/tmp/a"}},
                {"tool_name": "delete_path", "arguments": {"type": "file", "path": "/tmp/a.txt"}},
                {"tool_name": "generate_random_integer", "arguments": {"min": 1, "max": 10}},
            ],
            self._empty_allowlist,
        )
        assert result == 1

    def test_empty_list(self) -> None:
        """Return 0 for an empty list"""
        result: int = get_number_of_required_permissions([], self._empty_allowlist)
        assert result == 0

    def test_all_allowlisted(self) -> None:
        """Return 0 when all tools are allowlisted"""
        result: int = get_number_of_required_permissions(
            [
                {"tool_name": "read_file", "arguments": {"path": "/tmp/a.txt"}},
                {
                    "tool_name": "read_pdf_document",
                    "arguments": {"location_type": "local", "location": "/tmp/b.pdf"},
                },
            ],
            session_read_allowlist=["/tmp/a.txt", "/tmp/b.pdf"],
        )
        assert result == 0

    def test_some_allowlisted_some_not(self) -> None:
        """Return only the count of tools not in the allowlist"""
        result: int = get_number_of_required_permissions(
            [
                {"tool_name": "read_file", "arguments": {"path": "/tmp/a.txt"}},
                {"tool_name": "read_file", "arguments": {"path": "/tmp/b.txt"}},
            ],
            session_read_allowlist=["/tmp/a.txt"],
        )
        assert result == 1

    def test_allowlist_only_affects_read_tools(self) -> None:
        """Allowlist does not affect destructive tools"""
        result: int = get_number_of_required_permissions(
            [
                {"tool_name": "delete_path", "arguments": {"type": "file", "path": "/tmp/a.txt"}},
            ],
            session_read_allowlist=["/tmp/a.txt"],
        )
        assert result == 1


class TestGetToolReadPath:
    """Tests for the `get_tool_read_path` dispatching function"""

    def test_edit_file_permission_granted(self) -> None:
        """Return the path for edit_file when permission was granted"""
        result: str | None = get_tool_read_path(
            {
                "tool_name": "edit_file",
                "arguments": {
                    "path": "/tmp/test.txt",
                    "search_for": "old",
                    "replace_with": "new",
                    "number_of_substitutions": 1,
                },
            },
            tool_call_permission=True,
        )
        assert result == "/tmp/test.txt"

    def test_edit_file_permission_denied(self) -> None:
        """Return None for edit_file when permission was denied"""
        result: str | None = get_tool_read_path(
            {
                "tool_name": "edit_file",
                "arguments": {
                    "path": "/tmp/test.txt",
                    "search_for": "old",
                    "replace_with": "new",
                    "number_of_substitutions": 1,
                },
            },
            tool_call_permission=False,
        )
        assert result is None

    def test_move_path_permission_granted(self) -> None:
        """Return the destination for move_path when permission was granted"""
        result: str | None = get_tool_read_path(
            {
                "tool_name": "move_path",
                "arguments": {"type": "file", "source": "/tmp/a.txt", "destination": "/tmp/b.txt"},
            },
            tool_call_permission=True,
        )
        assert result == "/tmp/b.txt"

    def test_move_path_permission_denied(self) -> None:
        """Return None for move_path when permission was denied"""
        result: str | None = get_tool_read_path(
            {
                "tool_name": "move_path",
                "arguments": {"type": "file", "source": "/tmp/a.txt", "destination": "/tmp/b.txt"},
            },
            tool_call_permission=False,
        )
        assert result is None

    def test_read_file_permission_granted(self) -> None:
        """Return the path for read_file when permission was granted"""
        result: str | None = get_tool_read_path(
            {"tool_name": "read_file", "arguments": {"path": "/tmp/test.txt"}},
            tool_call_permission=True,
        )
        assert result == "/tmp/test.txt"

    def test_read_file_permission_denied(self) -> None:
        """Return None for read_file when permission was denied"""
        result: str | None = get_tool_read_path(
            {"tool_name": "read_file", "arguments": {"path": "/tmp/test.txt"}},
            tool_call_permission=False,
        )
        assert result is None

    def test_read_pdf_document_local_permission_granted(self) -> None:
        """Return the path for a local PDF when permission was granted"""
        result: str | None = get_tool_read_path(
            {
                "tool_name": "read_pdf_document",
                "arguments": {"location_type": "local", "location": "/tmp/doc.pdf"},
            },
            tool_call_permission=True,
        )
        assert result == "/tmp/doc.pdf"

    def test_read_pdf_document_permission_denied(self) -> None:
        """Return None for read_pdf_document when permission was denied"""
        result: str | None = get_tool_read_path(
            {
                "tool_name": "read_pdf_document",
                "arguments": {"location_type": "local", "location": "/tmp/doc.pdf"},
            },
            tool_call_permission=False,
        )
        assert result is None

    def test_read_pdf_document_web_permission_granted(self) -> None:
        """Return None for a web PDF even when permission was granted"""
        result: str | None = get_tool_read_path(
            {
                "tool_name": "read_pdf_document",
                "arguments": {"location_type": "web", "location": "https://example.com/doc.pdf"},
            },
            tool_call_permission=True,
        )
        assert result is None

    def test_write_file_permission_granted(self) -> None:
        """Return the path for write_file when permission was granted"""
        result: str | None = get_tool_read_path(
            {
                "tool_name": "write_file",
                "arguments": {"path": "/tmp/test.txt", "mode": "create_or_overwrite", "content": "hello"},
            },
            tool_call_permission=True,
        )
        assert result == "/tmp/test.txt"

    def test_write_file_permission_denied(self) -> None:
        """Return None for write_file when permission was denied"""
        result: str | None = get_tool_read_path(
            {
                "tool_name": "write_file",
                "arguments": {"path": "/tmp/test.txt", "mode": "create_or_overwrite", "content": "hello"},
            },
            tool_call_permission=False,
        )
        assert result is None

    def test_other_tool_returns_none(self) -> None:
        """Return None for tools that do not participate in the allowlist"""
        result: str | None = get_tool_read_path(
            {"tool_name": "create_directory", "arguments": {"path": "/tmp/test"}},
            tool_call_permission=True,
        )
        assert result is None

    def test_unknown_tool_returns_none(self) -> None:
        """Return None for unknown tool names"""
        result: str | None = get_tool_read_path(
            {"tool_name": "unknown_tool", "arguments": {}},
            tool_call_permission=True,
        )
        assert result is None


class TestExecuteToolCall:
    """Tests for the `execute_tool_call` dispatching function"""

    def test_generate_random_integer(self) -> None:
        """Dispatch to the correct execution function for generate_random_integer"""
        result: str = execute_tool_call(
            {"tool_name": "generate_random_integer", "arguments": {"min": 5, "max": 5}},
            True,
        )
        assert result == '<random_integer_generation min="5" max="5">\n<result>5</result>\n</random_integer_generation>'

    def test_create_directory(self) -> None:
        """Dispatch to the correct execution function for create_directory"""
        result: str = execute_tool_call(
            {"tool_name": "create_directory", "arguments": {"path": "/tmp/nonexistent_test_dir_for_testing_purposes"}},
            True,
        )
        expected: str = '<directory_creation path="/tmp/nonexistent_test_dir_for_testing_purposes">\n<result>Directory created successfully</result>\n</directory_creation>'
        assert result == expected
        from pathlib import Path

        Path("/tmp/nonexistent_test_dir_for_testing_purposes").rmdir()

    def test_invalid(self) -> None:
        """Dispatch to the correct execution function for invalid"""
        result: str = execute_tool_call(
            {
                "tool_name": "invalid",
                "arguments": {"tool_name": "write_file", "error_message": "Missing required argument: 'path'"},
            },
            True,
        )
        expected: str = "<skipped_invalid_tool_call tool_name=\"write_file\">\n<error>Missing required argument: 'path'</error>\n</skipped_invalid_tool_call>"
        assert result == expected

    def test_permission_denied(self) -> None:
        """Return a permission denied error when permission is False for destructive tools"""
        result: str = execute_tool_call(
            {"tool_name": "delete_path", "arguments": {"type": "file", "path": "/tmp/test.txt"}},
            False,
        )
        expected: str = '<path_deletion type="file" path="/tmp/test.txt">\n<error>Path deletion manually denied by the user. The path was not deleted</error>\n</path_deletion>'
        assert result == expected

    def test_unknown_tool_name(self) -> None:
        """Return an error message for unknown tool names"""
        result: str = execute_tool_call(
            {"tool_name": "unknown_tool", "arguments": {}},
            True,
        )
        assert result == 'Error on "unknown_tool"'

    def test_delete_path_not_found(self) -> None:
        """Handle a path that does not exist"""
        result: str = execute_tool_call(
            {"tool_name": "delete_path", "arguments": {"type": "file", "path": "/tmp/this_path_does_not_exist_12345"}},
            True,
        )
        expected: str = '<path_deletion type="file" path="/tmp/this_path_does_not_exist_12345">\n<error>Path not found</error>\n</path_deletion>'
        assert result == expected

    def test_missing_tool_name_key(self) -> None:
        """Return 'Error' when the tool_call dict lacks a 'tool_name' key"""
        result: str = execute_tool_call({"arguments": {}}, True)
        assert result == "Error"


class TestGetIndividualToolCallMessageEdgeCases:
    """Tests for edge cases in `get_individual_tool_call_message`"""

    def test_missing_tool_name_key(self) -> None:
        """Return 'Error' when the tool_call dict lacks a 'tool_name' key"""
        result: str = get_individual_tool_call_message({"arguments": {}})
        assert result == "Error"


class TestExecuteToolCallDispatch:
    """Tests that `execute_tool_call` dispatches to the correct function for each tool"""

    def test_edit_file(self) -> None:
        """Dispatch to edit_file with correct arguments"""
        result: str = execute_tool_call(
            {
                "tool_name": "edit_file",
                "arguments": {
                    "path": "/tmp/test.txt",
                    "search_for": "old",
                    "replace_with": "new",
                    "number_of_substitutions": 1,
                },
            },
            False,
        )
        expected: str = '<file_edit path="/tmp/test.txt" number_of_substitutions="1">\n<error>File editing manually denied by the user. The file was not modified</error>\n</file_edit>'
        assert result == expected

    def test_execute_shell_command(self) -> None:
        """Dispatch to execute_shell_command with correct arguments"""
        result: str = execute_tool_call(
            {"tool_name": "execute_shell_command", "arguments": {"command": "echo hello"}},
            True,
        )
        expected: str = "<shell_command_execution>\n<command>\necho hello\n</command>\n<stdout>\nhello\n</stdout>\n<stderr>\n</stderr>\n<exit_code>0</exit_code>\n</shell_command_execution>"
        assert result == expected

    def test_list_directory(self) -> None:
        """Dispatch to list_directory with correct arguments"""
        result: str = execute_tool_call(
            {"tool_name": "list_directory", "arguments": {"path": "/tmp"}},
            True,
        )
        assert result.startswith('<directory_listing path="/tmp">')
        assert result.endswith("</directory_listing>")

    def test_move_path_not_found(self) -> None:
        """Dispatch to move_path and handle missing source"""
        result: str = execute_tool_call(
            {
                "tool_name": "move_path",
                "arguments": {
                    "type": "file",
                    "source": "/tmp/nonexistent_source_abc",
                    "destination": "/tmp/nonexistent_dest_abc",
                },
            },
            True,
        )
        expected: str = '<path_move type="file" source="/tmp/nonexistent_source_abc" destination="/tmp/nonexistent_dest_abc">\n<error>Source path not found</error>\n</path_move>'
        assert result == expected

    def test_read_file_not_found(self) -> None:
        """Dispatch to read_file and handle missing file"""
        result: str = execute_tool_call(
            {"tool_name": "read_file", "arguments": {"path": "/tmp/nonexistent_file_for_testing_abc123"}},
            True,
        )
        expected: str = (
            '<file_read path="/tmp/nonexistent_file_for_testing_abc123">\n<error>File not found</error>\n</file_read>'
        )
        assert result == expected

    def test_read_web_page(self) -> None:
        """Dispatch to read_web_page"""
        result: str = execute_tool_call(
            {"tool_name": "read_web_page", "arguments": {"url": "https://example.com"}},
            True,
        )
        assert result.startswith('<web_page_read url="https://example.com">')
        assert result.endswith("</web_page_read>")

    def test_search_web(self) -> None:
        """Dispatch to search_web with correct arguments"""
        result: str = execute_tool_call(
            {
                "tool_name": "search_web",
                "arguments": {"query": "nonexistent_search_term_xyz_123", "max_results_per_page": 1},
            },
            True,
        )
        assert result.startswith('<web_search max_results_per_page="1" results_page_number="1">')
        assert result.endswith("</web_search>")

    def test_write_file_permission_denied(self) -> None:
        """Dispatch to write_file and respect permission denied"""
        result: str = execute_tool_call(
            {
                "tool_name": "write_file",
                "arguments": {"path": "/tmp/test_write_perm.txt", "mode": "create_or_overwrite", "content": "test"},
            },
            False,
        )
        expected: str = '<file_write path="/tmp/test_write_perm.txt" mode="create_or_overwrite">\n<error>File writing manually denied by the user. No content was written to the file</error>\n</file_write>'
        assert result == expected

    def test_read_pdf_document_not_found(self) -> None:
        """Dispatch to read_pdf_document and handle a non-existent local file"""
        result: str = execute_tool_call(
            {
                "tool_name": "read_pdf_document",
                "arguments": {"location_type": "local", "location": "/tmp/nonexistent_doc.pdf"},
            },
            True,
        )
        expected: str = '<pdf_document_read location_type="local" location="/tmp/nonexistent_doc.pdf">\n<error>Could not fetch the PDF document</error>\n</pdf_document_read>'
        assert result == expected
