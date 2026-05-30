from langchain_core.tools import tool
from datetime import datetime, timezone


@tool
def get_current_datetime(timezone_str: str = "UTC") -> str:
    """Get the current date and time. Optionally specify a timezone like 'UTC', 'US/Eastern', 'Europe/London', 'Asia/Kolkata', 'Asia/Tokyo', etc. Uses IANA timezone names."""
    try:
        from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
        try:
            tz = ZoneInfo(timezone_str) if timezone_str and timezone_str.upper() != "UTC" else timezone.utc
        except ZoneInfoNotFoundError:
            tz = timezone.utc
            timezone_str = "UTC (fallback — unknown timezone specified)"
        now = datetime.now(tz)
        return f"Current datetime ({timezone_str}): {now.strftime('%Y-%m-%d %H:%M:%S %Z')}"
    except Exception as e:
        return f"Error getting datetime: {str(e)}"
