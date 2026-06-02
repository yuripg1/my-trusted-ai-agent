from typing import Literal, Required, TypedDict

from primp import Client, Response
from trafilatura import extract

from tool.common import BaseToolCall
from tool.read_pdf_document import ReadPdfDocumentArguments, read_pdf_document


class ReadWebPageArguments(TypedDict):
    url: Required[str]


class ReadWebPageToolCall(BaseToolCall):
    tool_name: Required[Literal["read_web_page"]]
    arguments: Required[ReadWebPageArguments]


_EXTRACT_FORMAT: str = "html"
_IMPERSONATE_BROWSER: str = "random"
_IMPERSONATE_OS: str = "random"
_REQUEST_TIMEOUT: int = 300


def get_read_web_page_message(arguments: ReadWebPageArguments) -> str:
    return f"Reading web site at **{arguments['url']}**"


def get_read_web_page_permission(arguments: ReadWebPageArguments) -> bool:
    return True


def read_web_page(arguments: ReadWebPageArguments) -> str:
    output_entries: list[str] = []
    errored: bool = False
    status_code: int | None = None
    content_type: str = ""
    raw_web_page_content: str = ""
    try:
        client = Client(impersonate=_IMPERSONATE_BROWSER, impersonate_os=_IMPERSONATE_OS, timeout=_REQUEST_TIMEOUT)
        response: Response = client.get(arguments["url"])
        status_code = response.status_code
        if status_code >= 200 and status_code <= 299:
            raw_web_page_content = response.text
            content_type = response.headers.get("content-type", "").strip()
        else:
            output_entries.append("<error>Could not fetch the web page</error>")
            errored = True
    except Exception:
        output_entries.append("<error>Could not fetch the web page</error>")
        errored = True
    if "application/pdf" in content_type.lower():
        return read_pdf_document(
            ReadPdfDocumentArguments(location_type="web", location=arguments["url"]),
            note='Redirected from "read_web_page"',
        )
    if not errored:
        try:
            extracted_content: str | None = extract(
                raw_web_page_content, output_format=_EXTRACT_FORMAT, include_links=True
            )
            if extracted_content is not None:
                trimmed_extracted_content: str = extracted_content.strip()
                if len(trimmed_extracted_content) != 0:
                    output_entries.append(f"<content>\n{trimmed_extracted_content}\n</content>")
        except Exception:
            output_entries.append("<error>Could not read the web page</error>")
            errored = True
    if len(output_entries) == 0:
        output_entries.append("<error>Could not read the web page</error>")
        errored = True
    if errored:
        if status_code is not None:
            output_entries.append(f"<status_code>{status_code}</status_code>")
        if len(content_type) != 0:
            output_entries.append(f"<content_type>{content_type}</content_type>")
    joined_output_entries: str = "\n".join(output_entries)
    return f'<web_page_read url="{arguments["url"]}">\n{joined_output_entries}\n</web_page_read>'
