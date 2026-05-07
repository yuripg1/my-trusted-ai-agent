from typing import Any, Dict

DEEPSEEK_API_TOOLS: list[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "run_bash_command",
            "description": "Run any bash command",
            "parameters": {
                "type": "object",
                "properties": {"command": {"type": "string", "description": "The bash command to run"}},
                "required": ["command"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_random_integer",
            "description": "Return a random integer",
            "parameters": {
                "type": "object",
                "properties": {
                    "min": {"type": "integer", "description": "The minimum integer (inclusive)"},
                    "max": {"type": "integer", "description": "The maximum integer (inclusive)"},
                },
                "required": ["min", "max"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Search the web and return results with title, href, and body",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results per page",
                        "minimum": 1,
                        "maximum": 10,
                    },
                    "page": {"type": "integer", "description": "Page number of the search results", "minimum": 1},
                },
                "required": ["query", "max_results", "page"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_pdf_document",
            "description": "Fetch and extract the main text content from a PDF document (from the web or local)",
            "parameters": {
                "type": "object",
                "properties": {
                    "source_type": {"type": "string", "description": 'Type of the source ("remote" or "local")'},
                    "source": {"type": "string", "description": "Source of the PDF file (remote URL or local path)"},
                },
                "required": ["source", "source_type"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_web_page",
            "description": "Fetch and extract the main text content from a web page",
            "parameters": {
                "type": "object",
                "properties": {"url": {"type": "string", "description": "The URL of the web page to fetch and read"}},
                "required": ["url"],
                "additionalProperties": False,
            },
        },
    },
]
