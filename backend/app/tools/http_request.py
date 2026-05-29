import json
import requests
from langchain_core.tools import tool


@tool
def http_request(url: str, method: str = "GET", headers: str = "{}", body: str = "") -> str:
    """Make an HTTP request to any URL. Args: url (required), method (GET/POST/PUT/DELETE, default GET), headers (JSON string, default {}), body (request body string, default empty)."""
    try:
        parsed_headers = json.loads(headers) if headers.strip() else {}
        parsed_headers.setdefault("User-Agent", "AgentFlow/1.0")
        resp = requests.request(
            method.upper(),
            url,
            headers=parsed_headers,
            data=body or None,
            timeout=15,
        )
        content_type = resp.headers.get("Content-Type", "")
        text = resp.text[:4000]
        return f"Status: {resp.status_code}\nContent-Type: {content_type}\n\n{text}"
    except Exception as e:
        return f"HTTP request failed: {str(e)}"
