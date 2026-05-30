import re
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.custom_tool import CustomTool

router = APIRouter(prefix="/custom-tools", tags=["custom-tools"])

_NAME_RE = re.compile(r"^[a-z][a-z0-9_]{1,63}$")


class CustomToolCreate(BaseModel):
    name: str
    display_name: str
    description: str
    url: str
    method: str = "POST"
    headers: dict = {}
    body_template: str = ""
    is_active: bool = True

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not _NAME_RE.match(v):
            raise ValueError("name must be lowercase letters/numbers/underscores, start with a letter, 2-64 chars")
        return v

    @field_validator("method")
    @classmethod
    def validate_method(cls, v: str) -> str:
        if v.upper() not in ("GET", "POST", "PUT", "DELETE", "PATCH"):
            raise ValueError("method must be GET, POST, PUT, DELETE, or PATCH")
        return v.upper()


class CustomToolUpdate(BaseModel):
    display_name: str | None = None
    description: str | None = None
    url: str | None = None
    method: str | None = None
    headers: dict | None = None
    body_template: str | None = None
    is_active: bool | None = None


def _serialize(t: CustomTool) -> dict:
    return {
        "id": t.id,
        "name": t.name,
        "display_name": t.display_name,
        "description": t.description,
        "url": t.url,
        "method": t.method,
        "headers": t.headers or {},
        "body_template": t.body_template or "",
        "is_active": t.is_active,
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "updated_at": t.updated_at.isoformat() if t.updated_at else None,
    }


@router.get("")
async def list_custom_tools(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CustomTool).order_by(CustomTool.created_at))
    return [_serialize(t) for t in result.scalars().all()]


@router.post("", status_code=201)
async def create_custom_tool(body: CustomToolCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(CustomTool).where(CustomTool.name == body.name))
    if existing.scalar_one_or_none():
        raise HTTPException(400, f"A tool named '{body.name}' already exists")
    tool = CustomTool(id=str(uuid.uuid4()), **body.model_dump())
    db.add(tool)
    await db.commit()
    await db.refresh(tool)
    return _serialize(tool)


@router.patch("/{tool_id}")
async def update_custom_tool(tool_id: str, body: CustomToolUpdate, db: AsyncSession = Depends(get_db)):
    tool = await db.get(CustomTool, tool_id)
    if not tool:
        raise HTTPException(404, "Tool not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(tool, field, value)
    tool.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(tool)
    return _serialize(tool)


@router.delete("/{tool_id}", status_code=204)
async def delete_custom_tool(tool_id: str, db: AsyncSession = Depends(get_db)):
    tool = await db.get(CustomTool, tool_id)
    if not tool:
        raise HTTPException(404, "Tool not found")
    await db.delete(tool)
    await db.commit()
