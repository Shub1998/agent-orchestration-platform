import uuid
from datetime import datetime
from sqlalchemy import String, Text, Boolean, DateTime, JSON, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Workflow(Base):
    __tablename__ = "workflows"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    trigger_type: Mapped[str] = mapped_column(String(50), nullable=False, default="manual")
    trigger_config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    template_slug: Mapped[str] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    nodes: Mapped[list["WorkflowNode"]] = relationship("WorkflowNode", back_populates="workflow", cascade="all, delete-orphan")
    edges: Mapped[list["WorkflowEdge"]] = relationship("WorkflowEdge", back_populates="workflow", cascade="all, delete-orphan")


class WorkflowNode(Base):
    __tablename__ = "workflow_nodes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workflow_id: Mapped[str] = mapped_column(String(36), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False)
    agent_id: Mapped[str] = mapped_column(String(36), ForeignKey("agents.id", ondelete="SET NULL"), nullable=True)
    node_type: Mapped[str] = mapped_column(String(50), nullable=False, default="agent")
    label: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    position_x: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    position_y: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    workflow: Mapped["Workflow"] = relationship("Workflow", back_populates="nodes")


class WorkflowEdge(Base):
    __tablename__ = "workflow_edges"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workflow_id: Mapped[str] = mapped_column(String(36), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False)
    source_node_id: Mapped[str] = mapped_column(String(36), nullable=False)
    target_node_id: Mapped[str] = mapped_column(String(36), nullable=False)
    condition: Mapped[str] = mapped_column(Text, nullable=True)
    label: Mapped[str] = mapped_column(String(255), nullable=False, default="")

    workflow: Mapped["Workflow"] = relationship("Workflow", back_populates="edges")
