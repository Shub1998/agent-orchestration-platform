import json
import sqlite3
from langchain_core.tools import BaseTool, StructuredTool
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
    "get_current_datetime": "Get the current date and time in any timezone",
    "send_telegram_message": "Send a message to a Telegram chat",
    "http_request": "Make HTTP GET/POST/PUT/DELETE requests to any URL",
    "json_parser": "Parse JSON and extract values by dot-notation key path",
    "text_summarizer": "Extract key sentences from long text",
}


def _make_webhook_tool(name: str, description: str, url: str, method: str, headers: dict, body_template: str) -> BaseTool:
    import requests as _requests

    def _run(input: str) -> str:
        try:
            body = body_template.replace("{{input}}", input) if body_template else input
            h = dict(headers) if headers else {}
            h.setdefault("Content-Type", "application/json")
            resp = _requests.request(method, url, headers=h, data=body, timeout=15)
            return f"Status: {resp.status_code}\n{resp.text[:2000]}"
        except Exception as e:
            return f"Webhook call failed: {str(e)}"

    return StructuredTool.from_function(func=_run, name=name, description=description)


def load_custom_tools_sync(db_path: str) -> list[BaseTool]:
    """Load active custom webhook tools from SQLite (sync, for Celery workers)."""
    tools: list[BaseTool] = []
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute(
            "SELECT name, description, url, method, headers, body_template "
            "FROM custom_tools WHERE is_active=1"
        )
        rows = cur.fetchall()
        conn.close()
        for name, description, url, method, headers_json, body_template in rows:
            headers = json.loads(headers_json) if headers_json else {}
            tools.append(_make_webhook_tool(name, description, url, method, headers, body_template or ""))
    except Exception:
        pass
    return tools


async def load_custom_tools_async(db) -> list[BaseTool]:
    """Load active custom webhook tools from async DB session (for FastAPI)."""
    from sqlalchemy import select
    from app.models.custom_tool import CustomTool
    tools: list[BaseTool] = []
    try:
        result = await db.execute(select(CustomTool).where(CustomTool.is_active == True))  # noqa: E712
        for ct in result.scalars().all():
            tools.append(_make_webhook_tool(
                ct.name, ct.description, ct.url, ct.method,
                ct.headers or {}, ct.body_template or "",
            ))
    except Exception:
        pass
    return tools


def get_tools(tool_names: list[str]) -> list[BaseTool]:
    return [TOOL_REGISTRY[name] for name in tool_names if name in TOOL_REGISTRY]


def list_available_tools() -> list[dict]:
    return [
        {"name": name, "description": desc}
        for name, desc in TOOL_DESCRIPTIONS.items()
    ]
