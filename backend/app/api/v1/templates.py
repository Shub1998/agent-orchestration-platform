from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db

router = APIRouter(prefix="/templates", tags=["templates"])

TEMPLATES = {
    "research-pipeline": {
        "slug": "research-pipeline",
        "name": "Research + Summarizer",
        "description": "A Researcher agent gathers information from the web, then a Summarizer agent produces a concise executive summary.",
        "icon": "search",
        "category": "productivity",
        "agent_count": 2,
    },
    "customer-support": {
        "slug": "customer-support",
        "name": "Customer Support Triage",
        "description": "A Triage agent classifies incoming issues and routes them to specialized support agents (Billing, Technical, or General).",
        "icon": "headphones",
        "category": "support",
        "agent_count": 4,
    },
}


@router.get("")
async def list_templates():
    return list(TEMPLATES.values())


@router.post("/{slug}/instantiate")
async def instantiate_template(slug: str, db: AsyncSession = Depends(get_db)):
    if slug not in TEMPLATES:
        raise HTTPException(404, f"Template '{slug}' not found")

    if slug == "research-pipeline":
        from app.templates.research_pipeline import create_research_pipeline
        result = await create_research_pipeline(db)
    elif slug == "customer-support":
        from app.templates.customer_support import create_customer_support
        result = await create_customer_support(db)
    else:
        raise HTTPException(400, "Unknown template")

    return result
