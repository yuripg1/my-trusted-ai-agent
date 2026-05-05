from ddgs import DDGS
from random import randint
from subprocess import run
from trafilatura import extract, fetch_url
from typing import Literal, NotRequired, Required, TypedDict

FunctionNameType = Literal["run_bash_command", "get_random_integer", "web_search", "web_fetch"]


class FunctionCallInfo(TypedDict):
    tool_call_id: NotRequired[str]


class FunctionCallArguments(TypedDict):
    command: NotRequired[str]
    min: NotRequired[int]
    max: NotRequired[int]
    query: NotRequired[str]
    max_results: NotRequired[int]
    page: NotRequired[int]
    url: NotRequired[str]


class FunctionCall(TypedDict):
    function_name: Required[FunctionNameType]
    info: NotRequired[FunctionCallInfo]
    arguments: NotRequired[FunctionCallArguments]


class DuckDuckGoSearchResult(TypedDict):
    title: Required[str]
    href: Required[str]
    body: Required[str]


def get_function_call_message(function_call: FunctionCall) -> str:
    if function_call["function_name"] == "run_bash_command":
        return f"$ {function_call["arguments"]["command"]}"
    elif function_call["function_name"] == "get_random_integer":
        return f'Generating a random integer between "{function_call["arguments"]["min"]}" (inclusive) and "{function_call["arguments"]["max"]}" (inclusive)'
    elif function_call["function_name"] == "web_search":
        return f'Searching the web for "{function_call["arguments"]["query"]}" ({function_call["arguments"]["max_results"]} results - page {function_call["arguments"]["page"]})'
    elif function_call["function_name"] == "web_fetch":
        return f'Fetching content from "{function_call["arguments"]["url"]}"'
    return ""


def get_default_function_call_permission(function_call: FunctionCall) -> bool:
    permitted_functions: list[FunctionNameType] = ["get_random_integer", "web_search", "web_fetch"]
    if function_call["function_name"] in permitted_functions:
        return True
    else:
        return False


def execute_bash_command(permission_granted: bool, command: str) -> tuple[str, str, int]:
    if not permission_granted:
        return "", "", 0
    result = run(command, shell=True, capture_output=True, text=True)
    return result.stdout, result.stderr, result.returncode


def get_formatted_bash_command_output(
    command: str, permission_granted: bool, stdout: str, stderr: str, returncode: int
) -> str:
    if not permission_granted:
        return "Bash command execution manually denied by the user"
    result_lines: list[str] = []
    trimmed_command = command.strip()
    result_lines.append(f"<returncode>{returncode}</returncode>")
    result_lines.append(f"<command>\n{trimmed_command}\n</command>")
    trimmed_stdout = stdout.strip()
    if len(trimmed_stdout) != 0:
        result_lines.append(f"<stdout>\n{trimmed_stdout}\n</stdout>")
    trimmed_stderr = stderr.strip()
    if len(trimmed_stderr) != 0:
        result_lines.append(f"<stderr>\n{trimmed_stderr}\n</stderr>")
    joined_command_result: str = "\n".join(result_lines)
    return f"<command_execution>\n{joined_command_result}\n</command_execution>"


def search_web(query: str, max_results: int, page: int) -> str:
    raw_search_results = list(DDGS().text(query=query, safesearch="off", max_results=max_results, page=page))
    if len(raw_search_results) == 0:
        return f'No results found for "{query}"'
    search_results: list[DuckDuckGoSearchResult] = []
    for raw_search_result in raw_search_results:
        search_results.append(
            DuckDuckGoSearchResult(
                title=raw_search_result["title"], href=raw_search_result["href"], body=raw_search_result["body"]
            )
        )
    text_results: list[str] = []
    for search_result in search_results:
        text_results.append(
            f"<search_result>\n<title>{search_result["title"]}</title>\n<href>{search_result["href"]}</href>\n<body>\n{search_result["body"]}\n</body>\n</search_result>"
        )
    joined_search_results: str = "\n".join(text_results)
    return f'<search_results query="{query}" max_results="{max_results}" page="{page}">\n{joined_search_results}\n</search_results>'


def fetch_web_page(url: str) -> str:
    downloaded = fetch_url(url)
    if downloaded is None:
        return f'Could not fetch content from "{url}"'
    result = extract(downloaded, output_format="markdown", with_metadata=False)
    trimmed_result: str = result.strip() if result is not None else ""
    if len(trimmed_result) == 0:
        return f'No extractable text content found at "{url}"'
    return f'<fetched_content url="{url}">\n{trimmed_result}\n</fetched_content>'


def execute_function_call(function_call: FunctionCall, function_call_permission: bool) -> str:
    if function_call["function_name"] == "run_bash_command":
        command: str = function_call["arguments"]["command"]
        stdout, stderr, returncode = execute_bash_command(function_call_permission, command)
        return get_formatted_bash_command_output(command, function_call_permission, stdout, stderr, returncode)
    elif function_call["function_name"] == "get_random_integer":
        min: int = function_call["arguments"]["min"]
        max: int = function_call["arguments"]["max"]
        random_integer: int = randint(min, max)
        return f'<random_integer min="{min}" max="{max}">{random_integer}</random_integer>'
    elif function_call["function_name"] == "web_search":
        query: str = function_call["arguments"]["query"]
        max_results: int = function_call["arguments"]["max_results"]
        page: int = function_call["arguments"]["page"]
        return search_web(query, max_results, page)
    elif function_call["function_name"] == "web_fetch":
        url: str = function_call["arguments"]["url"]
        return fetch_web_page(url)
    return ""
