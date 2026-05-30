import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.database import get_db
from app.models.agent import Agent
from app.models.memory import MemoryEntry
from app.schemas.agent import AgentCreate, AgentUpdate, AgentResponse, AgentTestRequest

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("", response_model=list[AgentResponse])
async def list_agents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Agent).order_by(Agent.created_at.desc()))
    return result.scalars().all()


@router.post("", response_model=AgentResponse, status_code=201)
async def create_agent(body: AgentCreate, db: AsyncSession = Depends(get_db)):
    agent_id = str(uuid.uuid4())
    agent = Agent(
        id=agent_id,
        memory_collection=f"agent_{agent_id.replace('-', '_')}",
        **body.model_dump(),
    )
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    return agent


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str, db: AsyncSession = Depends(get_db)):
    agent = await db.get(Agent, agent_id)
    if not agent:
        raise HTTPException(404, "Agent not found")
    return agent


@router.patch("/{agent_id}", response_model=AgentResponse)
async def update_agent(agent_id: str, body: AgentUpdate, db: AsyncSession = Depends(get_db)):
    agent = await db.get(Agent, agent_id)
    if not agent:
        raise HTTPException(404, "Agent not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(agent, field, value)
    agent.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(agent)
    return agent


@router.delete("/{agent_id}", status_code=204)
async def delete_agent(agent_id: str, db: AsyncSession = Depends(get_db)):
    agent = await db.get(Agent, agent_id)
    if not agent:
        raise HTTPException(404, "Agent not found")
    await db.execute(delete(MemoryEntry).where(MemoryEntry.agent_id == agent_id))
    await db.delete(agent)
    await db.commit()


@router.get("/{agent_id}/memory")
async def get_agent_memory(agent_id: str, db: AsyncSession = Depends(get_db)):
    agent = await db.get(Agent, agent_id)
    if not agent:
        raise HTTPException(404, "Agent not found")
    result = await db.execute(
        select(MemoryEntry).where(MemoryEntry.agent_id == agent_id).order_by(MemoryEntry.created_at.desc()).limit(50)
    )
    entries = result.scalars().all()
    return [{"id": e.id, "summary": e.summary, "created_at": e.created_at} for e in entries]


@router.delete("/{agent_id}/memory", status_code=204)
async def clear_agent_memory(agent_id: str, db: AsyncSession = Depends(get_db)):
    agent = await db.get(Agent, agent_id)
    if not agent:
        raise HTTPException(404, "Agent not found")
    from app.core.memory_manager import memory_manager
    memory_manager.clear(agent_id)
    await db.execute(delete(MemoryEntry).where(MemoryEntry.agent_id == agent_id))
    await db.commit()


@router.post("/{agent_id}/test")
async def test_agent(agent_id: str, body: AgentTestRequest, db: AsyncSession = Depends(get_db)):
    agent = await db.get(Agent, agent_id)
    if not agent:
        raise HTTPException(404, "Agent not found")
    from app.core.agent_builder import agent_builder
    from app.core.state import AgentFlowState
    from langchain_core.messages import HumanMessage

    agent_dict = {
        "id": agent.id, "name": agent.name, "role": agent.role,
        "system_prompt": agent.system_prompt, "model": agent.model,
        "provider": agent.provider, "temperature": agent.temperature,
        "max_iterations": min(agent.max_iterations, 5),
        "memory_enabled": False,
        "tools": agent.tools or [],
        "max_output_tokens": agent.max_output_tokens or 4096,
        "guardrail_keywords": agent.guardrail_keywords or [],
        "input_guardrail_keywords": agent.input_guardrail_keywords or [],
        "max_input_length": agent.max_input_length or 0,
        "response_format": agent.response_format or "text",
    }
    node_fn = agent_builder.build(agent_dict)
    test_execution_id = f"test_{str(uuid.uuid4())[:8]}"
    from langchain_core.messages import AIMessage
    history_messages = []
    for msg in body.history:
        if msg.role == "user":
            history_messages.append(HumanMessage(content=msg.content))
        else:
            history_messages.append(AIMessage(content=msg.content))
    history_messages.append(HumanMessage(content=body.prompt))
    state = AgentFlowState(
        messages=history_messages,
        current_agent="", execution_id=test_execution_id, workflow_id="test",
        input=body.prompt, output="", iteration=0, context={}, error=None, telegram_chat_id=None,
    )
    result = node_fn(state)
    return {"output": result.get("output", ""), "execution_id": test_execution_id}
