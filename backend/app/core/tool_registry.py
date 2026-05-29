from langchain_core.tools import BaseTool
from app.tools.web_search import web_search
from app.tools.web_scraper import web_scraper
from app.tools.calculator import calculator
from app.tools.datetime_tool import get_current_datetime
from app.tools.send_telegram import send_telegram_message
from app.tools.http_request import http_request
from app.tools.text_tools import json_parser, text_summarizer

TOOL_REGISTRY: dict[str, BaseTool] = {
    "web_search": web_search,
    "web_scraper": web_scraper,
    "calculator": calculator,
    "get_current_datetime": get_current_datetime,
    "send_telegram_message": send_telegram_message,
    "http_request": http_request,
    "json_parser": json_parser,
    "text_summarizer": text_summarizer,
}

TOOL_DESCRIPTIONS = {
    "web_search": "Search the web using DuckDuckGo",
    "web_scraper": "Fetch and extract text from any URL",
    "calculator": "Evaluate mathematical expressions",
    "get_current_datetime": "Get the current date and time",
    "send_telegram_message": "Send a message to a Telegram chat",
    "http_request": "Make HTTP GET/POST/PUT/DELETE requests to any URL",
    "json_parser": "Parse JSON and extract values by dot-notation key path",
    "text_summarizer": "Extract key sentences from long text",
}


def get_tools(tool_names: list[str]) -> list[BaseTool]:
    return [TOOL_REGISTRY[name] for name in tool_names if name in TOOL_REGISTRY]


def list_available_tools() -> list[dict]:
    return [
        {"name": name, "description": desc}
        for name, desc in TOOL_DESCRIPTIONS.items()
    ]
