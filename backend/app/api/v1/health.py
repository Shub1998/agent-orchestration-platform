from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.database import get_db
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
async def list_tools(db: AsyncSession = Depends(get_db)):
    from app.core.tool_registry import list_available_tools, load_custom_tools_async
    builtin = list_available_tools()
    custom_tools = await load_custom_tools_async(db)
    custom_entries = [
        {"name": t.name, "description": t.description, "is_custom": True}
        for t in custom_tools
    ]
    return builtin + custom_entries
