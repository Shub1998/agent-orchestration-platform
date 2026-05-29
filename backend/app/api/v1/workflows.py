import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.workflow import Workflow, WorkflowNode, WorkflowEdge
from app.models.execution import Execution
from app.schemas.workflow import (
    WorkflowCreate, WorkflowUpdate, WorkflowResponse, WorkflowWithGraph,
    WorkflowNodeCreate, WorkflowNodeUpdate, WorkflowNodeResponse,
    WorkflowEdgeCreate, WorkflowEdgeResponse, WorkflowSaveGraph, TriggerRequest,
)
from app.schemas.execution import ExecutionResponse

router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.get("", response_model=list[WorkflowResponse])
async def list_workflows(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Workflow).order_by(Workflow.created_at.desc()))
    return result.scalars().all()


@router.post("", response_model=WorkflowWithGraph, status_code=201)
async def create_workflow(body: WorkflowCreate, db: AsyncSession = Depends(get_db)):
    workflow = Workflow(
        id=str(uuid.uuid4()),
        name=body.name,
        description=body.description,
        trigger_type=body.trigger_type,
        trigger_config=body.trigger_config,
    )
    db.add(workflow)
    await db.flush()

    nodes = []
    start_node = WorkflowNode(id=str(uuid.uuid4()), workflow_id=workflow.id, node_type="start", label="Start", position_x=100, position_y=100)
    end_node = WorkflowNode(id=str(uuid.uuid4()), workflow_id=workflow.id, node_type="end", label="End", position_x=900, position_y=100)
    db.add(start_node)
    db.add(end_node)
    nodes.extend([start_node, end_node])

    for node_data in body.nodes:
        data = node_data.model_dump()
        node_id = data.pop("id", None) or str(uuid.uuid4())
        node = WorkflowNode(id=node_id, workflow_id=workflow.id, **data)
        db.add(node)
        nodes.append(node)

    edges = []
    for edge_data in body.edges:
        edge = WorkflowEdge(id=str(uuid.uuid4()), workflow_id=workflow.id, **edge_data.model_dump())
        db.add(edge)
        edges.append(edge)

    await db.commit()
    await db.refresh(workflow)

    result_nodes = await db.execute(select(WorkflowNode).where(WorkflowNode.workflow_id == workflow.id))
    result_edges = await db.execute(select(WorkflowEdge).where(WorkflowEdge.workflow_id == workflow.id))

    return WorkflowWithGraph(
        **WorkflowResponse.model_validate(workflow).model_dump(),
        nodes=[WorkflowNodeResponse.model_validate(n) for n in result_nodes.scalars().all()],
        edges=[WorkflowEdgeResponse.model_validate(e) for e in result_edges.scalars().all()],
    )


@router.get("/{workflow_id}", response_model=WorkflowWithGraph)
async def get_workflow(workflow_id: str, db: AsyncSession = Depends(get_db)):
    workflow = await db.get(Workflow, workflow_id)
    if not workflow:
        raise HTTPException(404, "Workflow not found")
    result_nodes = await db.execute(select(WorkflowNode).where(WorkflowNode.workflow_id == workflow_id))
    result_edges = await db.execute(select(WorkflowEdge).where(WorkflowEdge.workflow_id == workflow_id))
    return WorkflowWithGraph(
        **WorkflowResponse.model_validate(workflow).model_dump(),
        nodes=[WorkflowNodeResponse.model_validate(n) for n in result_nodes.scalars().all()],
        edges=[WorkflowEdgeResponse.model_validate(e) for e in result_edges.scalars().all()],
    )


@router.patch("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(workflow_id: str, body: WorkflowUpdate, db: AsyncSession = Depends(get_db)):
    workflow = await db.get(Workflow, workflow_id)
    if not workflow:
        raise HTTPException(404, "Workflow not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(workflow, field, value)
    workflow.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(workflow)
    return workflow


@router.delete("/{workflow_id}", status_code=204)
async def delete_workflow(workflow_id: str, db: AsyncSession = Depends(get_db)):
    workflow = await db.get(Workflow, workflow_id)
    if not workflow:
        raise HTTPException(404, "Workflow not found")
    await db.delete(workflow)
    await db.commit()


@router.post("/{workflow_id}/graph", response_model=WorkflowWithGraph)
async def save_workflow_graph(workflow_id: str, body: WorkflowSaveGraph, db: AsyncSession = Depends(get_db)):
    workflow = await db.get(Workflow, workflow_id)
    if not workflow:
        raise HTTPException(404, "Workflow not found")

    existing_nodes = await db.execute(select(WorkflowNode).where(WorkflowNode.workflow_id == workflow_id))
    for node in existing_nodes.scalars().all():
        await db.delete(node)
    existing_edges = await db.execute(select(WorkflowEdge).where(WorkflowEdge.workflow_id == workflow_id))
    for edge in existing_edges.scalars().all():
        await db.delete(edge)

    for node_data in body.nodes:
        data = node_data.model_dump()
        node_id = data.pop("id", None) or str(uuid.uuid4())
        node = WorkflowNode(id=node_id, workflow_id=workflow_id, **data)
        db.add(node)
    for edge_data in body.edges:
        edge = WorkflowEdge(id=str(uuid.uuid4()), workflow_id=workflow_id, **edge_data.model_dump())
        db.add(edge)

    workflow.updated_at = datetime.utcnow()
    await db.commit()

    result_nodes = await db.execute(select(WorkflowNode).where(WorkflowNode.workflow_id == workflow_id))
    result_edges = await db.execute(select(WorkflowEdge).where(WorkflowEdge.workflow_id == workflow_id))
    return WorkflowWithGraph(
        **WorkflowResponse.model_validate(workflow).model_dump(),
        nodes=[WorkflowNodeResponse.model_validate(n) for n in result_nodes.scalars().all()],
        edges=[WorkflowEdgeResponse.model_validate(e) for e in result_edges.scalars().all()],
    )


@router.post("/{workflow_id}/trigger", response_model=ExecutionResponse, status_code=202)
async def trigger_workflow(workflow_id: str, body: TriggerRequest, db: AsyncSession = Depends(get_db)):
    workflow = await db.get(Workflow, workflow_id)
    if not workflow:
        raise HTTPException(404, "Workflow not found")

    execution = Execution(
        id=str(uuid.uuid4()),
        workflow_id=workflow_id,
        status="pending",
        trigger_type="manual",
        trigger_payload={"prompt": body.prompt, "context": body.context},
    )
    db.add(execution)
    await db.commit()
    await db.refresh(execution)

    from app.workers.execution_tasks import run_workflow_task
    task = run_workflow_task.delay(workflow_id, execution.id, {"prompt": body.prompt, "context": body.context})
    execution.celery_task_id = task.id
    await db.commit()
    await db.refresh(execution)

    return execution
