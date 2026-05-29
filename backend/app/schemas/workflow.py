from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class WorkflowNodeCreate(BaseModel):
    id: Optional[str] = None          # client may supply stable ID; server generates if absent
    agent_id: Optional[str] = None
    node_type: str = Field(default="agent")
    label: str = Field(default="")
    position_x: float = Field(default=0.0)
    position_y: float = Field(default=0.0)
    config: dict = Field(default_factory=dict)


class WorkflowNodeUpdate(BaseModel):
    agent_id: Optional[str] = None
    node_type: Optional[str] = None
    label: Optional[str] = None
    position_x: Optional[float] = None
    position_y: Optional[float] = None
    config: Optional[dict] = None


class WorkflowNodeResponse(BaseModel):
    id: str
    workflow_id: str
    agent_id: Optional[str]
    node_type: str
    label: str
    position_x: float
    position_y: float
    config: dict

    model_config = {"from_attributes": True}


class WorkflowEdgeCreate(BaseModel):
    source_node_id: str
    target_node_id: str
    condition: Optional[str] = None
    label: str = Field(default="")


class WorkflowEdgeResponse(BaseModel):
    id: str
    workflow_id: str
    source_node_id: str
    target_node_id: str
    condition: Optional[str]
    label: str

    model_config = {"from_attributes": True}


class WorkflowCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(default="")
    trigger_type: str = Field(default="manual")
    trigger_config: dict = Field(default_factory=dict)
    nodes: list[WorkflowNodeCreate] = Field(default_factory=list)
    edges: list[WorkflowEdgeCreate] = Field(default_factory=list)


class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    trigger_type: Optional[str] = None
    trigger_config: Optional[dict] = None


class WorkflowResponse(BaseModel):
    id: str
    name: str
    description: str
    is_active: bool
    trigger_type: str
    trigger_config: dict
    template_slug: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WorkflowWithGraph(WorkflowResponse):
    nodes: list[WorkflowNodeResponse]
    edges: list[WorkflowEdgeResponse]


class WorkflowSaveGraph(BaseModel):
    nodes: list[WorkflowNodeCreate]
    edges: list[WorkflowEdgeCreate]


class TriggerRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    context: dict = Field(default_factory=dict)
