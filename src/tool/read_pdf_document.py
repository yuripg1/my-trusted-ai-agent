from io import BytesIO
from typing import Any, Literal, Required, TypedDict

from primp import Client, Response
from pypdf import PdfReader

from tool.common import BaseToolCall


class ReadPdfDocumentArguments(TypedDict):
    location_type: Required[str]
    location: Required[str]


class ReadPdfDocumentToolCall(BaseToolCall):
    tool_name: Required[Literal["read_pdf_document"]]
    arguments: Required[ReadPdfDocumentArguments]


_EXTRACT_MODE: Literal["plain", "layout"] = "layout"
_IMPERSONATE_BROWSER: str = "random"
_IMPERSONATE_OS: str = "random"
_REQUEST_TIMEOUT: int = 300


def get_read_pdf_document_permission(arguments: ReadPdfDocumentArguments, session_read_allowlist: list[str]) -> bool:
    if arguments["location_type"] == "web":
        return True
    elif arguments["location"] in session_read_allowlist:
        return True
    else:
        return False


def get_read_pdf_document_read_path(arguments: ReadPdfDocumentArguments, tool_call_permission: bool) -> str | None:
    if arguments["location_type"] == "local" and tool_call_permission:
        return arguments["location"]
    else:
        return None


def get_read_pdf_document_message(arguments: ReadPdfDocumentArguments) -> str:
    return f"Reading PDF document at **{arguments['location']}** (**{arguments['location_type']}**)"


def read_pdf_document(arguments: ReadPdfDocumentArguments, tool_call_permission: bool = True, note: str = "") -> str:
    output_entries: list[str] = []
    if not tool_call_permission:
        output_entries.append("<error>PDF document reading manually denied by the user</error>")
    else:
        errored: bool = False
        status_code: int | None = None
        content_type: str = ""
        raw_pdf_document_content: Any = None
        try:
            if arguments["location_type"] == "web" or arguments["location"].startswith(("http", "https")):
                client: Client = Client(
                    impersonate=_IMPERSONATE_BROWSER, impersonate_os=_IMPERSONATE_OS, timeout=_REQUEST_TIMEOUT
                )
                response: Response = client.get(arguments["location"])
                status_code = response.status_code
                if status_code >= 200 and status_code <= 299:
                    raw_pdf_document_content = response.content
                    content_type = response.headers.get("content-type", "").strip()
                else:
                    output_entries.append("<error>Could not fetch the PDF document</error>")
                    errored = True
            elif arguments["location_type"] == "local":
                with open(arguments["location"], "rb") as pdf_document_file:
                    raw_pdf_document_content = pdf_document_file.read()
            else:
                output_entries.append(f'<error>Invalid location_type "{arguments["location_type"]}"</error>')
                errored = True
        except Exception:
            output_entries.append("<error>Could not fetch the PDF document</error>")
            errored = True
        if not errored:
            try:
                if raw_pdf_document_content[:4] != b"%PDF":
                    output_entries.append("<error>The fetched file does not seem to be a valid PDF document</error>")
                    errored = True
                else:
                    pdf_document_reader = PdfReader(BytesIO(raw_pdf_document_content))
                    output_pages_entries: list[str] = []
                    for page_number, raw_pdf_document_page in enumerate(pdf_document_reader.pages, 1):
                        pdf_document_page_text = raw_pdf_document_page.extract_text(
                            extraction_mode=_EXTRACT_MODE
                        ).strip()
                        if len(pdf_document_page_text) != 0:
                            output_pages_entries.append(
                                f'<page number="{page_number}">\n{pdf_document_page_text}\n</page>'
                            )
                    if len(output_pages_entries) != 0:
                        joined_output_pages_entries = "\n".join(output_pages_entries)
                        output_entries.append(f"<pages>\n{joined_output_pages_entries}\n</pages>")
            except Exception:
                output_entries.append("<error>Could not read the PDF document</error>")
                errored = True
        if len(output_entries) == 0:
            output_entries.append("<error>Could not read the PDF document</error>")
            errored = True
        if errored:
            if status_code is not None:
                output_entries.append(f"<status_code>{status_code}</status_code>")
            if len(content_type) != 0:
                output_entries.append(f"<content_type>{content_type}</content_type>")
        if len(note) != 0:
            output_entries.insert(0, f"<note>{note}</note>")
    joined_output_entries: str = "\n".join(output_entries)
    return f'<pdf_document_read location_type="{arguments["location_type"]}" location="{arguments["location"]}">\n{joined_output_entries}\n</pdf_document_read>'
