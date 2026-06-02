from pathlib import Path
from unittest.mock import patch

from tool.list_directory import (
    ListDirectoryArguments,
    get_list_directory_message,
    get_list_directory_permission,
    list_directory,
)


class TestGetListDirectoryMessage:
    """Tests for the `get_list_directory_message` function"""

    def test_format(self) -> None:
        """Format the message correctly"""
        arguments: ListDirectoryArguments = {"path": "/some/dir"}
        assert get_list_directory_message(arguments) == "Listing directory at **/some/dir**"


class TestGetListDirectoryPermission:
    """Tests for the `get_list_directory_permission` function"""

    def test_auto_approved(self) -> None:
        """Permission should be automatically granted"""
        arguments: ListDirectoryArguments = {"path": "/some/dir"}
        assert get_list_directory_permission(arguments) is True


class TestListDirectory:
    """Tests for the `list_directory` tool"""

    def test_list_directory_with_entries(self, tmp_path: Path) -> None:
        """List a directory containing files and subdirectories"""
        target: Path = tmp_path.joinpath("docs")
        target.mkdir()
        readme_file: Path = target.joinpath("readme.txt")
        readme_file.write_text("hello")
        symlink: Path = target.joinpath("link_to_readme")
        symlink.symlink_to(readme_file)
        src_directory: Path = target.joinpath("src")
        src_directory.mkdir()
        result: str = list_directory(ListDirectoryArguments(path=str(target)))
        read_file_entry: str = f'<entry type="file" size="5">{readme_file.name}</entry>'
        symlink_entry: str = f'<entry type="symlink" target="{str(readme_file)}" target_type="file" target_size="5">{symlink.name}</entry>'
        sec_directory_entry: str = f'<entry type="directory" entries="0">{src_directory.name}</entry>'
        assert result.startswith(f'<directory_listing path="{str(target)}">\n<entry')
        assert result.endswith("</entry>\n</directory_listing>")
        assert read_file_entry in result
        assert symlink_entry in result
        assert sec_directory_entry in result

    def test_list_directory_with_symlink_to_directory(self, tmp_path: Path) -> None:
        """List a directory containing a symlink pointing to another directory"""
        target: Path = tmp_path.joinpath("docs")
        target.mkdir()
        target.joinpath("notes.txt").write_text("hello")
        symlink: Path = tmp_path.joinpath("link_to_docs")
        symlink.symlink_to(target)
        result: str = list_directory(ListDirectoryArguments(path=str(tmp_path)))
        expected_symlink_entry: str = f'<entry type="symlink" target="{str(target)}" target_type="directory" target_entries="1">{symlink.name}</entry>'
        assert expected_symlink_entry in result

    def test_list_directory_with_broken_symlink(self, tmp_path: Path) -> None:
        """List a directory containing a symlink whose target no longer exists"""
        target: Path = tmp_path.joinpath("ghost.txt")
        target.write_text("hello")
        symlink: Path = tmp_path.joinpath("broken_link")
        symlink.symlink_to(target)
        target.unlink()
        result: str = list_directory(ListDirectoryArguments(path=str(tmp_path)))
        resolved_target: str = str(symlink.resolve(strict=False))
        expected_symlink_entry: str = f'<entry type="symlink" target="{resolved_target}">{symlink.name}</entry>'
        assert expected_symlink_entry in result

    def test_list_directory_with_symlink_resolve_failure(self, tmp_path: Path) -> None:
        """List a directory containing a symlink whose target cannot be resolved"""
        target: Path = tmp_path.joinpath("docs")
        target.mkdir()
        symlink: Path = target.joinpath("link")
        symlink.symlink_to("/nonexistent")
        with patch.object(Path, "resolve", side_effect=Exception("Resolve error")):
            result: str = list_directory(ListDirectoryArguments(path=str(target)))
            expected_symlink_entry: str = f'<entry type="symlink">{symlink.name}</entry>'
            assert expected_symlink_entry in result

    def test_list_directory_with_single_directory_compression(self, tmp_path: Path) -> None:
        """Compress a chain of a single directory entry"""
        target: Path = tmp_path.joinpath("outer")
        target.mkdir()
        inner: Path = target.joinpath("inner")
        inner.mkdir()
        inner.joinpath("file1.txt").write_text("one")
        inner.joinpath("file2.txt").write_text("two")
        result: str = list_directory(ListDirectoryArguments(path=str(tmp_path)))
        assert result.startswith(f'<directory_listing path="{str(tmp_path)}">')
        assert result.endswith("</directory_listing>")
        assert '<entry type="file" size="3">outer/inner/file1.txt</entry>' in result
        assert '<entry type="file" size="3">outer/inner/file2.txt</entry>' in result

    def test_list_directory_with_nested_compression(self, tmp_path: Path) -> None:
        """Compress a chain of multiple single-directory entries"""
        target: Path = tmp_path.joinpath("a")
        target.mkdir()
        b: Path = target.joinpath("b")
        b.mkdir()
        c: Path = b.joinpath("c")
        c.mkdir()
        c.joinpath("data.txt").write_text("content")
        result: str = list_directory(ListDirectoryArguments(path=str(tmp_path)))
        assert (
            result
            == f'<directory_listing path="{str(tmp_path)}">\n<entry type="file" size="7">a/b/c/data.txt</entry>\n</directory_listing>'
        )

    def test_list_directory_compression_stops_at_symlink(self, tmp_path: Path) -> None:
        """Do not compress through a symlink directory"""
        target: Path = tmp_path.joinpath("real_dir")
        target.mkdir()
        target.joinpath("file.txt").write_text("content")
        link: Path = tmp_path.joinpath("link_to_dir")
        link.symlink_to(target)
        result: str = list_directory(ListDirectoryArguments(path=str(tmp_path)))
        resolved_target: str = str(target.resolve())
        expected_symlink_entry: str = f'<entry type="symlink" target="{resolved_target}" target_type="directory" target_entries="1">{link.name}</entry>'
        assert expected_symlink_entry in result

    def test_list_directory_compression_stops_at_multiple_entries(self, tmp_path: Path) -> None:
        """Compress through a single directory, then show the full contents of the next level"""
        inner: Path = tmp_path.joinpath("inner")
        inner.mkdir()
        subdir: Path = inner.joinpath("subdir")
        subdir.mkdir()
        inner.joinpath("readme.txt").write_text("hello")
        result: str = list_directory(ListDirectoryArguments(path=str(tmp_path)))
        assert result.startswith(f'<directory_listing path="{str(tmp_path)}">')
        assert result.endswith("</directory_listing>")
        assert '<entry type="directory" entries="0">inner/subdir</entry>' in result
        assert '<entry type="file" size="5">inner/readme.txt</entry>' in result

    def test_list_directory_compression_empty_final(self, tmp_path: Path) -> None:
        """Compress through a chain but find an empty directory at the end"""
        target: Path = tmp_path.joinpath("a")
        target.mkdir()
        b: Path = target.joinpath("b")
        b.mkdir()
        result: str = list_directory(ListDirectoryArguments(path=str(tmp_path)))
        assert (
            result
            == f'<directory_listing path="{str(tmp_path)}">\n<note>The directory is empty</note>\n</directory_listing>'
        )

    def test_list_directory_compression_max_depth(self, tmp_path: Path) -> None:
        """Stop compressing at the maximum depth limit"""
        current: Path = tmp_path
        for i in range(15):
            next_dir: Path = current.joinpath(f"level_{i}")
            next_dir.mkdir()
            current = next_dir
        current.joinpath("file.txt").write_text("deep")
        result: str = list_directory(ListDirectoryArguments(path=str(tmp_path)))
        expected_prefix: str = "/".join([f"level_{i}" for i in range(10)]) + "/"
        assert f'<entry type="directory" entries="1">{expected_prefix}level_10</entry>' in result

    def test_list_empty_directory(self, tmp_path: Path) -> None:
        """List an empty directory"""
        target: Path = tmp_path.joinpath("empty_dir")
        target.mkdir()
        result: str = list_directory(ListDirectoryArguments(path=str(target)))
        assert (
            result
            == f'<directory_listing path="{str(target)}">\n<note>The directory is empty</note>\n</directory_listing>'
        )

    def test_directory_not_found(self) -> None:
        """DO not list a directory that does not exist"""
        result: str = list_directory(ListDirectoryArguments(path="/nonexistent/path"))
        assert (
            result
            == '<directory_listing path="/nonexistent/path">\n<error>Directory not found</error>\n</directory_listing>'
        )

    def test_path_is_not_a_directory(self, tmp_path: Path) -> None:
        """Do not list a path that is a file, not a directory"""
        target: Path = tmp_path.joinpath("file.txt")
        target.write_text("content")
        result: str = list_directory(ListDirectoryArguments(path=str(target)))
        assert (
            result
            == f'<directory_listing path="{str(target)}">\n<error>Path is not a directory</error>\n</directory_listing>'
        )

    def test_permission_denied(self, tmp_path: Path) -> None:
        """Do not list a directory due to permission error"""
        target: Path = tmp_path.joinpath("secret")
        target.mkdir()
        with patch.object(Path, "iterdir", side_effect=PermissionError("Permission error")):
            result: str = list_directory(ListDirectoryArguments(path=str(target)))
            assert (
                result
                == f'<directory_listing path="{str(target)}">\n<error>Permission denied by the system</error>\n</directory_listing>'
            )

    def test_unknown_error(self, tmp_path: Path) -> None:
        """Do not list a directory due to an exception"""
        target: Path = tmp_path.joinpath("broken")
        target.mkdir()
        with patch.object(Path, "iterdir", side_effect=Exception("Exception")):
            result: str = list_directory(ListDirectoryArguments(path=str(target)))
            assert (
                result
                == f'<directory_listing path="{str(target)}">\n<error>Could not list directory</error>\n</directory_listing>'
            )

    def test_entry_classification_exception(self, tmp_path: Path) -> None:
        """List a directory containing an entry whose type cannot be determined"""
        target: Path = tmp_path.joinpath("mystery")
        target.mkdir()
        mystery_file: Path = target.joinpath("unknown")
        mystery_file.write_text("content")
        with patch.object(Path, "is_file", side_effect=Exception("Exception")):
            result: str = list_directory(ListDirectoryArguments(path=str(target)))
            mystery_file_entry: str = f"<entry>{mystery_file.name}</entry>"
            assert result == f'<directory_listing path="{str(target)}">\n{mystery_file_entry}\n</directory_listing>'

    def test_unknown_entry_type(self, tmp_path: Path) -> None:
        """List a directory containing an entry that is neither a file, a directory, nor a symlink"""
        target: Path = tmp_path.joinpath("mystery")
        target.mkdir()
        mystery_file: Path = target.joinpath("unknown")
        mystery_file.write_text("content")
        with (
            patch.object(Path, "is_symlink", return_value=False),
            patch.object(Path, "is_dir", return_value=False),
            patch.object(Path, "is_file", return_value=False),
        ):
            result: str = list_directory(ListDirectoryArguments(path=str(target)))
            mystery_file_entry: str = f"<entry>{mystery_file.name}</entry>"
            assert result == f'<directory_listing path="{str(target)}">\n{mystery_file_entry}\n</directory_listing>'
