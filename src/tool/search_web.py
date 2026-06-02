from contextlib import suppress
from typing import Literal, NotRequired, Required, TypedDict

from ddgs import DDGS

from tool.common import BaseToolCall


class SearchWebArguments(TypedDict):
    query: Required[str]
    max_results_per_page: Required[int]
    results_page_number: NotRequired[int]


class SearchWebToolCall(BaseToolCall):
    tool_name: Required[Literal["search_web"]]
    arguments: Required[SearchWebArguments]


_TIMEOUT: int = 300
_SAFESEARCH: str = "off"


def get_search_web_message(arguments: SearchWebArguments) -> str:
    return f"Searching the web for **{arguments['query']}** (**{arguments['max_results_per_page']}** results - page **{arguments.get('results_page_number', 1)}**)"


def get_search_web_permission(arguments: SearchWebArguments) -> bool:
    return True


def search_web(arguments: SearchWebArguments) -> str:
    output_entries: list[str] = []
    results_page_number: int = arguments.get("results_page_number", 1)
    output_entries.append(f"<query>{arguments['query']}</query>")
    if arguments["max_results_per_page"] < 1:
        output_entries.append('<error>"max_results_per_page" must be greater than or equal to 1</error>')
    elif arguments["max_results_per_page"] > 10:
        output_entries.append('<error>"max_results_per_page" must be less than or equal to 10</error>')
    elif results_page_number < 1:
        output_entries.append('<error>"results_page_number" must be greater than or equal to 1</error>')
    else:
        raw_search_results = []
        with suppress(Exception):
            raw_search_results = list(
                DDGS(timeout=_TIMEOUT).text(
                    query=arguments["query"],
                    safesearch=_SAFESEARCH,
                    max_results=arguments["max_results_per_page"],
                    page=results_page_number,
                )
            )
        if len(raw_search_results) == 0:
            output_entries.append("<error>No search results found</error>")
        else:
            for page_result_number, search_result_data in enumerate(raw_search_results, 1):
                search_result_number: int = (
                    (results_page_number - 1) * arguments["max_results_per_page"]
                ) + page_result_number
                output_entries.append(
                    f'<search_result result_number="{search_result_number}">\n<title>{str(search_result_data["title"]).strip()}</title>\n<href>{str(search_result_data["href"]).strip()}</href>\n<snippet>\n{str(search_result_data["body"]).strip()}\n</snippet>\n</search_result>'
                )
    joined_output_entries: str = "\n".join(output_entries)
    return f'<web_search max_results_per_page="{arguments["max_results_per_page"]}" results_page_number="{results_page_number}">\n{joined_output_entries}\n</web_search>'
