from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.execution import Execution, ExecutionLog
from app.schemas.execution import ExecutionResponse, ExecutionLogResponse

router = APIRouter(prefix="/executions", tags=["executions"])


@router.get("", response_model=list[ExecutionResponse])
async def list_executions(
    workflow_id: str = Query(None),
    status: str = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    q = select(Execution).order_by(Execution.created_at.desc()).limit(limit)
    if workflow_id:
        q = q.where(Execution.workflow_id == workflow_id)
    if status:
        q = q.where(Execution.status == status)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/{execution_id}", response_model=ExecutionResponse)
async def get_execution(execution_id: str, db: AsyncSession = Depends(get_db)):
    execution = await db.get(Execution, execution_id)
    if not execution:
        raise HTTPException(404, "Execution not found")
    return execution


@router.delete("/{execution_id}", status_code=204)
async def delete_execution(execution_id: str, db: AsyncSession = Depends(get_db)):
    execution = await db.get(Execution, execution_id)
    if not execution:
        raise HTTPException(404, "Execution not found")
    if execution.celery_task_id and execution.status in ("running", "pending", "awaiting_approval"):
        try:
            from app.workers.celery_app import celery_app
            celery_app.control.revoke(execution.celery_task_id, terminate=True)
        except Exception:
            pass
    await db.delete(execution)
    await db.commit()


class ApproveRequest(BaseModel):
    decision: str  # "approve" or "reject"
    comment: str = ""


@router.post("/{execution_id}/approve")
async def approve_execution(execution_id: str, body: ApproveRequest, db: AsyncSession = Depends(get_db)):
    if body.decision not in ("approve", "reject"):
        raise HTTPException(400, "decision must be 'approve' or 'reject'")
    execution = await db.get(Execution, execution_id)
    if not execution:
        raise HTTPException(404, "Execution not found")
    if execution.status != "awaiting_approval":
        raise HTTPException(400, f"Execution is not awaiting approval (status: {execution.status})")

    from app.workers.execution_tasks import resume_workflow_task
    resume_workflow_task.delay(
        execution.workflow_id,
        execution_id,
        body.decision,
        body.comment,
    )

    return {"status": "ok", "decision": body.decision, "execution_id": execution_id}


@router.get("/{execution_id}/logs")
async def get_execution_logs(execution_id: str, db: AsyncSession = Depends(get_db)):
    execution = await db.get(Execution, execution_id)
    if not execution:
        raise HTTPException(404, "Execution not found")
    result = await db.execute(
        select(ExecutionLog).where(ExecutionLog.execution_id == execution_id).order_by(ExecutionLog.timestamp)
    )
    logs = result.scalars().all()
    return [
        {
            "id": log.id, "execution_id": log.execution_id, "node_id": log.node_id,
            "agent_id": log.agent_id, "agent_name": log.agent_name,
            "level": log.level, "message": log.message,
            "metadata": log.metadata_, "timestamp": log.timestamp.isoformat(),
        }
        for log in logs
    ]
