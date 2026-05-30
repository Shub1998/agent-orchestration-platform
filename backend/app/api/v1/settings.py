from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from app.database import get_db
from app.models.platform_setting import PlatformSetting

router = APIRouter(prefix="/settings", tags=["settings"])

# Keys that are masked in GET responses (tokens/secrets)
_SECRET_KEYS = {
    "telegram_bot_token",
    "slack_bot_token",
    "discord_bot_token",
    "openai_api_key",
    "anthropic_api_key",
}


class SettingUpdate(BaseModel):
    value: str


def _mask(key: str, value: str) -> str:
    if key in _SECRET_KEYS and len(value) > 8:
        return value[:4] + "****" + value[-4:]
    return value


@router.get("")
async def get_settings(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PlatformSetting))
    rows = result.scalars().all()
    return {r.key: {"value": _mask(r.key, r.value), "is_set": bool(r.value)} for r in rows}


@router.put("/{key}")
async def upsert_setting(key: str, body: SettingUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PlatformSetting).where(PlatformSetting.key == key))
    row = result.scalar_one_or_none()
    if row:
        row.value = body.value
    else:
        db.add(PlatformSetting(key=key, value=body.value))
    await db.commit()
    return {"key": key, "is_set": bool(body.value)}


@router.delete("/{key}")
async def clear_setting(key: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PlatformSetting).where(PlatformSetting.key == key))
    row = result.scalar_one_or_none()
    if row:
        row.value = ""
        await db.commit()
    return {"key": key, "is_set": False}
