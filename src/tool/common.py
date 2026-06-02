from contextlib import suppress
from typing import NotRequired, TypedDict

from pygments.lexers import get_lexer_for_filename


class BaseToolCall(TypedDict):
    id: NotRequired[str]


def make_safe_code_fence(content: str, info_string: str = "") -> str:
    max_backtick_run: int = 0
    current_backtick_run: int = 0
    for character in content:
        if character == "`":
            current_backtick_run += 1
            if current_backtick_run > max_backtick_run:
                max_backtick_run = current_backtick_run
        else:
            current_backtick_run = 0
    fence_length: int = 3
    if max_backtick_run >= 3:
        fence_length = max_backtick_run + 1
    fence: str = "`" * fence_length
    info: str = info_string.strip()
    if len(info) != 0:
        return f"{fence}{info}\n{content}\n{fence}"
    else:
        return f"{fence}\n{content}\n{fence}"


def get_language_from_filename(path: str) -> str:
    with suppress(Exception):
        path = path.rstrip("/")
        lexer = get_lexer_for_filename(path)
        if len(lexer.aliases) != 0:
            return lexer.aliases[0]
    return ""
