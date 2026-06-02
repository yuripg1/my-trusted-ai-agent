from contextlib import suppress
from pathlib import Path
from typing import Literal, Required, TypedDict

from tool.common import BaseToolCall


class ListDirectoryArguments(TypedDict):
    path: Required[str]


class ListDirectoryToolCall(BaseToolCall):
    tool_name: Required[Literal["list_directory"]]
    arguments: Required[ListDirectoryArguments]


_MAX_COMPRESSION_DEPTH: int = 10


def get_list_directory_message(arguments: ListDirectoryArguments) -> str:
    return f"Listing directory at **{arguments['path']}**"


def get_list_directory_permission(arguments: ListDirectoryArguments) -> bool:
    return True


def _resolve_compressed_path(path: Path, depth: int = 0) -> Path:
    if depth >= _MAX_COMPRESSION_DEPTH:
        return path
    with suppress(Exception):
        entries: list[Path] = list(path.iterdir())
        if len(entries) == 1 and entries[0].is_dir() and not entries[0].is_symlink():
            return _resolve_compressed_path(entries[0], depth + 1)
    return path


def list_directory(arguments: ListDirectoryArguments) -> str:
    output_entries: list[str] = []
    try:
        directory_path: Path = Path(arguments["path"])
        compressed_path: Path = _resolve_compressed_path(directory_path)
        prefix_relative: str = ""
        if compressed_path != directory_path:
            prefix_relative = str(compressed_path.relative_to(directory_path)) + "/"
        for directory_entry in compressed_path.iterdir():
            entry_attributes: str = ""
            entry_name: str = prefix_relative + directory_entry.name
            with suppress(Exception):
                if directory_entry.is_symlink():
                    entry_attributes += ' type="symlink"'
                    target_path: Path = directory_entry.resolve(strict=False)
                    entry_attributes += f' target="{str(target_path)}"'
                    if target_path.is_dir():
                        entry_attributes += ' target_type="directory"'
                        entry_attributes += f' target_entries="{sum(1 for _ in target_path.iterdir())}"'
                    elif target_path.is_file():
                        entry_attributes += ' target_type="file"'
                        entry_attributes += f' target_size="{target_path.stat().st_size}"'
                elif directory_entry.is_dir():
                    entry_attributes += ' type="directory"'
                    entry_attributes += f' entries="{sum(1 for _ in directory_entry.iterdir())}"'
                elif directory_entry.is_file():
                    entry_attributes += ' type="file"'
                    entry_attributes += f' size="{directory_entry.stat().st_size}"'
            output_entries.append(f"<entry{entry_attributes}>{entry_name}</entry>")
    except FileNotFoundError:
        output_entries.append("<error>Directory not found</error>")
    except NotADirectoryError:
        output_entries.append("<error>Path is not a directory</error>")
    except PermissionError:
        output_entries.append("<error>Permission denied by the system</error>")
    except Exception:
        output_entries.append("<error>Could not list directory</error>")
    if len(output_entries) == 0:
        output_entries.append("<note>The directory is empty</note>")
    joined_output_entries: str = "\n".join(output_entries)
    return f'<directory_listing path="{arguments["path"]}">\n{joined_output_entries}\n</directory_listing>'
