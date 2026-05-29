from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
import redis.asyncio as aioredis
from app.config import settings
from functools import lru_cache


async def get_session(db: AsyncSession = Depends(get_db)) -> AsyncSession:
    return db


_redis_client = None


async def get_redis() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis_client
