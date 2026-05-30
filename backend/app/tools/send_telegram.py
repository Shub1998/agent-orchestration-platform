from langchain_core.tools import tool
import asyncio
import httpx
from app.config import settings


@tool
def send_telegram_message(chat_id: str, message: str) -> str:
    """Send a message to a specific Telegram chat. chat_id is the numeric Telegram chat ID (e.g. '123456789'). Use this to communicate results back to the user."""
    if not settings.TELEGRAM_BOT_TOKEN:
        return "Telegram not configured"
    try:
        url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": int(chat_id), "text": message, "parse_mode": "Markdown"}
        with httpx.Client(timeout=10) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
        return f"Message sent to chat {chat_id}"
    except Exception as e:
        return f"Failed to send Telegram message: {str(e)}"
