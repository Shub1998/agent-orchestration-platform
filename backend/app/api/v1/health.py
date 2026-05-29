from fastapi import APIRouter
from app.config import settings
import redis as sync_redis

router = APIRouter()


@router.get("/health")
async def health():
    redis_ok = False
    try:
        r = sync_redis.from_url(settings.REDIS_URL)
        r.ping()
        redis_ok = True
    except Exception:
        pass
    return {
        "status": "ok",
        "redis": "ok" if redis_ok else "unavailable",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@router.get("/tools")
async def list_tools():
    from app.core.tool_registry import list_available_tools
    return list_available_tools()
