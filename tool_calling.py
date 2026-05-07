from ddgs import DDGS
from ddgs.exceptions import DDGSException
from io import BytesIO
from pypdf import PdfReader
from random import randint
from requests import get, Response
from subprocess import run
from trafilatura import extract, fetch_url
from typing import Any, Literal, NotRequired, Required, TypedDict

FunctionNameType = Literal[
    "run_bash_command", "get_random_integer", "search_web", "fetch_web_page", "read_pdf_document"
]

SEARCH_TIMEOUT: int = 60
SEARCH_SAFESEARCH: str = "off"
DOCUMENT_REQUEST_TIMEOUT: int = 60


class ToolCallArguments(TypedDict):
    command: NotRequired[str]
    min: NotRequired[int]
    max: NotRequired[int]
    query: NotRequired[str]
    max_results: NotRequired[int]
    page: NotRequired[int]
    url: NotRequired[str]
    source_type: NotRequired[str]
    source: NotRequired[str]


class ToolCall(TypedDict):
    id: NotRequired[str]
    function_name: NotRequired[FunctionNameType]
    arguments: Required[ToolCallArguments]


class SearchResult(TypedDict):
    title: Required[str]
    href: Required[str]
    body: Required[str]


def get_tool_call_message(tool_call: ToolCall) -> str:
    if tool_call["function_name"] == "run_bash_command":
        return f"$ {tool_call["arguments"]["command"]}"
    elif tool_call["function_name"] == "get_random_integer":
        return f'Generating a random integer between "{tool_call["arguments"]["min"]}" and "{tool_call["arguments"]["max"]}"'
    elif tool_call["function_name"] == "search_web":
        return f'Searching the web for "{tool_call["arguments"]["query"]}" ({tool_call["arguments"]["max_results"]} results - page {tool_call["arguments"]["page"]})'
    elif tool_call["function_name"] == "fetch_web_page":
        return f'Fetching content from "{tool_call["arguments"]["url"]}"'
    elif tool_call["function_name"] == "read_pdf_document":
        return f'Reading PDF document from "{tool_call["arguments"]["source"]}"'
    return ""


def get_default_tool_call_permission(tool_call: ToolCall) -> bool:
    if tool_call["function_name"] in ["get_random_integer", "search_web", "fetch_web_page"]:
        return True
    elif tool_call["function_name"] == "read_pdf_document":
        return tool_call["arguments"]["source_type"] == "remote"
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
    raw_search_results = []
    try:
        raw_search_results = list(
            DDGS(timeout=SEARCH_TIMEOUT).text(
                query=query, safesearch=SEARCH_SAFESEARCH, max_results=max_results, page=page
            )
        )
    except DDGSException:
        pass
    if len(raw_search_results) == 0:
        return f'No results found for "{query}"'
    search_results: list[SearchResult] = []
    for raw_search_result in raw_search_results:
        search_results.append(
            SearchResult(
                title=raw_search_result["title"], href=raw_search_result["href"], body=raw_search_result["body"]
            )
        )
    text_results: list[str] = []
    for search_result in search_results:
        text_results.append(
            f"<search_result>\n<title>{search_result["title"]}</title>\n<href>{search_result["href"]}</href>\n<body>\n{search_result["body"]}\n</body>\n</search_result>"
        )
    joined_search_results: str = "\n".join(text_results)
    return f'<web_search query="{query}" max_results="{max_results}" page="{page}">\n{joined_search_results}\n</search_results>'


def fetch_web_page(url: str) -> str:
    text_content: str = ""
    try:
        raw_content = fetch_url(url)
        text_content = str(extract(raw_content, output_format="markdown", with_metadata=False)).strip()
    except:
        pass
    if len(text_content) == 0:
        return f'Could not fetch web page at "{url}"'
    return f'<fetched_content url="{url}">\n{text_content}\n</fetched_content>'


def read_pdf_document(source_type: str, source: str) -> str:
    text_pdf_content: str = ""
    raw_pdf_content: bytes | Any | None = None
    try:
        if source_type == "local":
            with open(source, "rb") as pdf_file:
                raw_pdf_content = pdf_file.read()
        elif source_type == "remote":
            response: Response = get(source, timeout=DOCUMENT_REQUEST_TIMEOUT)
            raw_pdf_content = response.content
    except:
        pass
    if type(raw_pdf_content) is bytes:
        reader = PdfReader(BytesIO(raw_pdf_content))
        text_parts: list[str] = []
        for page in reader.pages:
            page_text = page.extract_text()
            if len(page_text) != 0:
                text_parts.append(page_text)
        text_pdf_content = "\n".join(text_parts).strip()
    if len(text_pdf_content) == 0:
        return f'Could not read PDF document at "{source}"'
    return f'<pdf_document source_type="{source_type}" source="{source}">\n{text_pdf_content}\n</read_pdf_document>'


def execute_tool_call(tool_call: ToolCall, tool_call_permission: bool) -> str:
    if tool_call["function_name"] == "run_bash_command":
        command: str = tool_call["arguments"]["command"]
        stdout, stderr, returncode = execute_bash_command(tool_call_permission, command)
        return get_formatted_bash_command_output(command, tool_call_permission, stdout, stderr, returncode)
    elif tool_call["function_name"] == "get_random_integer":
        min: int = tool_call["arguments"]["min"]
        max: int = tool_call["arguments"]["max"]
        random_integer: int = randint(min, max)
        return f'<random_integer min="{min}" max="{max}">{random_integer}</random_integer>'
    elif tool_call["function_name"] == "search_web":
        query: str = tool_call["arguments"]["query"]
        max_results: int = tool_call["arguments"]["max_results"]
        page: int = tool_call["arguments"]["page"]
        return search_web(query, max_results, page)
    elif tool_call["function_name"] == "fetch_web_page":
        url: str = tool_call["arguments"]["url"]
        return fetch_web_page(url)
    elif tool_call["function_name"] == "read_pdf_document":
        source_type: str = tool_call["arguments"]["source_type"]
        source: str = tool_call["arguments"]["source"]
        return read_pdf_document(source_type, source)
    return ""
