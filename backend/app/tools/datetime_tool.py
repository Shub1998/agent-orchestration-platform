from langchain_core.tools import tool
from datetime import datetime, timezone


@tool
def get_current_datetime(timezone_str: str = "UTC") -> str:
    """Get the current date and time. Optionally specify a timezone like 'UTC', 'US/Eastern', etc."""
    try:
        now = datetime.now(timezone.utc)
        return f"Current datetime (UTC): {now.strftime('%Y-%m-%d %H:%M:%S %Z')}"
    except Exception as e:
        return f"Error getting datetime: {str(e)}"
