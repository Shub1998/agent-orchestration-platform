from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ExecutionCreate(BaseModel):
    workflow_id: str
    trigger_type: str = "manual"
    trigger_payload: dict = {}


class ExecutionResponse(BaseModel):
    id: str
    workflow_id: str
    status: str
    trigger_type: str
    trigger_payload: dict
    final_output: Optional[str]
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    celery_task_id: Optional[str]
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost_usd: float = 0.0
    created_at: datetime

    model_config = {"from_attributes": True}


class ExecutionLogResponse(BaseModel):
    id: str
    execution_id: str
    node_id: Optional[str]
    agent_id: Optional[str]
    agent_name: Optional[str]
    level: str
    message: str
    metadata_: dict
    timestamp: datetime

    model_config = {"from_attributes": True}
