import uuid
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.workflow_template import WorkflowTemplate

router = APIRouter(prefix="/templates", tags=["templates"])

# ── Built-in (hardcoded) templates ────────────────────────────────────────────

BUILTIN_TEMPLATES = {
    "research-pipeline": {
        "slug": "research-pipeline",
        "name": "Research + Summarizer",
        "description": "A Researcher agent gathers information from the web, then a Summarizer agent produces a concise executive summary.",
        "icon": "search",
        "category": "productivity",
        "agent_count": 2,
        "is_custom": False,
        "difficulty": "beginner",
        "tags": ["research", "summarization", "web-search"],
        "use_cases": ["Market research briefs", "Topic deep-dives", "Competitive analysis"],
        "agents_preview": [
            {"name": "Researcher", "role": "researcher", "color": "#3b82f6"},
            {"name": "Summarizer", "role": "summarizer", "color": "#10b981"},
        ],
    },
    "customer-support": {
        "slug": "customer-support",
        "name": "Customer Support Triage",
        "description": "A Triage agent classifies incoming issues and routes them to specialized support agents (Billing, Technical, or General).",
        "icon": "headphones",
        "category": "support",
        "agent_count": 4,
        "is_custom": False,
        "difficulty": "intermediate",
        "tags": ["customer-support", "routing", "HITL"],
        "use_cases": ["Helpdesk ticket routing", "Multi-tier support queues", "SLA prioritization"],
        "agents_preview": [
            {"name": "Triage", "role": "triage", "color": "#6366f1"},
            {"name": "Billing", "role": "billing", "color": "#f59e0b"},
            {"name": "Technical", "role": "technical", "color": "#06b6d4"},
            {"name": "General", "role": "general", "color": "#8b5cf6"},
        ],
    },
    "content-pipeline": {
        "slug": "content-pipeline",
        "name": "Content Marketing Pipeline",
        "description": "Researcher gathers source material from the web, Writer drafts engaging content, and Senior Editor polishes it for publication.",
        "icon": "pen",
        "category": "marketing",
        "agent_count": 3,
        "is_custom": False,
        "difficulty": "beginner",
        "tags": ["content", "writing", "SEO", "web-search"],
        "use_cases": ["Blog posts & articles", "Newsletter copy", "Social media content"],
        "agents_preview": [
            {"name": "Topic Researcher", "role": "researcher", "color": "#3b82f6"},
            {"name": "Content Writer", "role": "writer", "color": "#10b981"},
            {"name": "Senior Editor", "role": "editor", "color": "#f59e0b"},
        ],
    },
    "data-intelligence": {
        "slug": "data-intelligence",
        "name": "Data Intelligence Report",
        "description": "Data Collector gathers raw data from the web, Data Analyst identifies trends and patterns, Report Generator produces an executive-ready intelligence brief.",
        "icon": "bar-chart",
        "category": "analytics",
        "agent_count": 3,
        "is_custom": False,
        "difficulty": "intermediate",
        "tags": ["analytics", "research", "reporting", "web-search"],
        "use_cases": ["Market intelligence reports", "Competitor benchmarking", "Industry trend analysis"],
        "agents_preview": [
            {"name": "Data Collector", "role": "data_collector", "color": "#06b6d4"},
            {"name": "Data Analyst", "role": "analyst", "color": "#8b5cf6"},
            {"name": "Report Generator", "role": "reporter", "color": "#f59e0b"},
        ],
    },
    "hitl-content-approval": {
        "slug": "hitl-content-approval",
        "name": "Content with Human Approval",
        "description": "Researcher prepares a brief, Writer drafts content, a Human reviewer approves or rejects with feedback, Publisher finalizes and publishes.",
        "icon": "user-check",
        "category": "marketing",
        "agent_count": 3,
        "is_custom": False,
        "difficulty": "advanced",
        "tags": ["HITL", "content", "approval", "human-in-the-loop"],
        "use_cases": ["Brand-sensitive publications", "Compliance-reviewed content", "Editorial workflows"],
        "agents_preview": [
            {"name": "Brief Researcher", "role": "researcher", "color": "#3b82f6"},
            {"name": "Content Drafter", "role": "writer", "color": "#10b981"},
            {"name": "Human Review", "role": "approval", "color": "#ef4444"},
            {"name": "Publisher", "role": "publisher", "color": "#8b5cf6"},
        ],
    },
}


# ── Schemas ────────────────────────────────────────────────────────────────────

class CreateTemplateRequest(BaseModel):
    workflow_id: str
    name: str
    description: str
    category: str = "productivity"
    icon: str = "zap"


# ── Helpers ────────────────────────────────────────────────────────────────────

def _template_record(t: WorkflowTemplate) -> dict:
    agent_count = len(t.workflow_snapshot.get("agents", {}))
    return {
        "slug": t.slug,
        "name": t.name,
        "description": t.description,
        "icon": t.icon,
        "category": t.category,
        "agent_count": agent_count,
        "is_custom": t.is_custom,
        "created_at": t.created_at.isoformat(),
    }


async def _snapshot_workflow(workflow_id: str, db: AsyncSession) -> dict:
    from app.models.workflow import Workflow, WorkflowNode, WorkflowEdge
    from app.models.agent import Agent
    from sqlalchemy import select

    workflow = await db.get(Workflow, workflow_id)
    if not workflow:
        raise HTTPException(404, f"Workflow '{workflow_id}' not found")

    nodes_result = await db.execute(
        select(WorkflowNode).where(WorkflowNode.workflow_id == workflow_id)
    )
    nodes = nodes_result.scalars().all()

    edges_result = await db.execute(
        select(WorkflowEdge).where(WorkflowEdge.workflow_id == workflow_id)
    )
    edges = edges_result.scalars().all()

    # Collect unique agent IDs
    agent_ids = {n.agent_id for n in nodes if n.agent_id}
    agents_data: dict[str, dict] = {}
    for aid in agent_ids:
        agent = await db.get(Agent, aid)
        if agent:
            agents_data[aid] = {
                "name": agent.name,
                "role": agent.role,
                "description": agent.description,
                "system_prompt": agent.system_prompt,
                "model": agent.model,
                "provider": agent.provider,
                "temperature": agent.temperature,
                "max_iterations": agent.max_iterations,
                "memory_enabled": agent.memory_enabled,
                "tools": agent.tools,
                "avatar_color": agent.avatar_color,
                "max_output_tokens": agent.max_output_tokens,
                "guardrail_keywords": agent.guardrail_keywords,
            }

    nodes_snapshot = [
        {
            "ref": n.id,
            "node_type": n.node_type,
            "label": n.label,
            "position_x": n.position_x,
            "position_y": n.position_y,
            "agent_ref": n.agent_id,
            "config": n.config or {},
        }
        for n in nodes
    ]

    edges_snapshot = [
        {
            "source_ref": e.source_node_id,
            "target_ref": e.target_node_id,
            "label": e.label or "",
            "condition": e.condition,
        }
        for e in edges
    ]

    return {
        "workflow_name": workflow.name,
        "workflow_description": workflow.description,
        "workflow_trigger_type": workflow.trigger_type,
        "agents": agents_data,
        "nodes": nodes_snapshot,
        "edges": edges_snapshot,
    }


async def _instantiate_snapshot(snapshot: dict, db: AsyncSession) -> dict:
    from app.models.agent import Agent
    from app.models.workflow import Workflow, WorkflowNode, WorkflowEdge

    # Map old agent IDs → new agent IDs
    agent_id_map: dict[str, str] = {}
    for old_id, agent_data in snapshot.get("agents", {}).items():
        new_id = str(uuid.uuid4())
        agent_id_map[old_id] = new_id
        agent = Agent(
            id=new_id,
            name=agent_data["name"],
            role=agent_data["role"],
            description=agent_data["description"],
            system_prompt=agent_data["system_prompt"],
            model=agent_data["model"],
            provider=agent_data["provider"],
            temperature=agent_data["temperature"],
            max_iterations=agent_data["max_iterations"],
            memory_enabled=agent_data["memory_enabled"],
            tools=agent_data["tools"],
            avatar_color=agent_data["avatar_color"],
            max_output_tokens=agent_data.get("max_output_tokens", 4096),
            guardrail_keywords=agent_data.get("guardrail_keywords", []),
            memory_collection=f"agent_{new_id.replace('-', '_')}",
        )
        db.add(agent)

    await db.flush()

    # Create workflow
    workflow_id = str(uuid.uuid4())
    workflow = Workflow(
        id=workflow_id,
        name=snapshot["workflow_name"],
        description=snapshot["workflow_description"],
        trigger_type=snapshot.get("workflow_trigger_type", "manual"),
    )
    db.add(workflow)
    await db.flush()

    # Map old node refs → new node IDs
    node_id_map: dict[str, str] = {}
    for node_data in snapshot.get("nodes", []):
        new_node_id = str(uuid.uuid4())
        node_id_map[node_data["ref"]] = new_node_id
        new_agent_id = agent_id_map.get(node_data.get("agent_ref") or "") or None
        node = WorkflowNode(
            id=new_node_id,
            workflow_id=workflow_id,
            node_type=node_data["node_type"],
            label=node_data["label"],
            position_x=node_data["position_x"],
            position_y=node_data["position_y"],
            agent_id=new_agent_id,
            config=node_data.get("config", {}),
        )
        db.add(node)

    for edge_data in snapshot.get("edges", []):
        src = node_id_map.get(edge_data["source_ref"])
        tgt = node_id_map.get(edge_data["target_ref"])
        if src and tgt:
            db.add(WorkflowEdge(
                id=str(uuid.uuid4()),
                workflow_id=workflow_id,
                source_node_id=src,
                target_node_id=tgt,
                label=edge_data.get("label", ""),
                condition=edge_data.get("condition"),
            ))

    await db.commit()

    return {
        "workflow_id": workflow_id,
        "workflow_name": workflow.name,
        "agents": list(agent_id_map.values()),
        "message": f"Template '{snapshot['workflow_name']}' instantiated successfully",
    }


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.get("")
async def list_templates(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(WorkflowTemplate).order_by(WorkflowTemplate.created_at))
    custom = [_template_record(t) for t in result.scalars().all()]
    return list(BUILTIN_TEMPLATES.values()) + custom


@router.post("")
async def create_template(body: CreateTemplateRequest, db: AsyncSession = Depends(get_db)):
    slug = f"custom-{uuid.uuid4().hex[:8]}"
    snapshot = await _snapshot_workflow(body.workflow_id, db)
    tmpl = WorkflowTemplate(
        id=str(uuid.uuid4()),
        slug=slug,
        name=body.name,
        description=body.description,
        icon=body.icon,
        category=body.category,
        is_custom=True,
        workflow_snapshot=snapshot,
    )
    db.add(tmpl)
    await db.commit()
    return _template_record(tmpl)


@router.delete("/{slug}", status_code=204)
async def delete_template(slug: str, db: AsyncSession = Depends(get_db)):
    if slug in BUILTIN_TEMPLATES:
        raise HTTPException(400, "Built-in templates cannot be deleted")
    result = await db.execute(select(WorkflowTemplate).where(WorkflowTemplate.slug == slug))
    tmpl = result.scalar_one_or_none()
    if not tmpl:
        raise HTTPException(404, f"Template '{slug}' not found")
    await db.delete(tmpl)
    await db.commit()


@router.post("/{slug}/instantiate")
async def instantiate_template(slug: str, db: AsyncSession = Depends(get_db)):
    # Built-in templates
    if slug == "research-pipeline":
        from app.templates.research_pipeline import create_research_pipeline
        return await create_research_pipeline(db)
    if slug == "customer-support":
        from app.templates.customer_support import create_customer_support
        return await create_customer_support(db)
    if slug == "content-pipeline":
        from app.templates.content_pipeline import create_content_pipeline
        return await create_content_pipeline(db)
    if slug == "data-intelligence":
        from app.templates.data_intelligence import create_data_intelligence
        return await create_data_intelligence(db)
    if slug == "hitl-content-approval":
        from app.templates.hitl_content_approval import create_hitl_content_approval
        return await create_hitl_content_approval(db)

    # Custom (DB-stored) templates
    result = await db.execute(select(WorkflowTemplate).where(WorkflowTemplate.slug == slug))
    tmpl = result.scalar_one_or_none()
    if not tmpl:
        raise HTTPException(404, f"Template '{slug}' not found")
    return await _instantiate_snapshot(tmpl.workflow_snapshot, db)
