import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, JSON, ForeignKey, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class Execution(Base):
    __tablename__ = "executions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workflow_id: Mapped[str] = mapped_column(String(36), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    trigger_type: Mapped[str] = mapped_column(String(50), nullable=False, default="manual")
    trigger_payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    final_output: Mapped[str] = mapped_column(Text, nullable=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    celery_task_id: Mapped[str] = mapped_column(String(255), nullable=True)
    total_input_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_output_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_cost_usd: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class ExecutionLog(Base):
    __tablename__ = "execution_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    execution_id: Mapped[str] = mapped_column(String(36), ForeignKey("executions.id", ondelete="CASCADE"), nullable=False)
    node_id: Mapped[str] = mapped_column(String(36), nullable=True)
    agent_id: Mapped[str] = mapped_column(String(36), nullable=True)
    agent_name: Mapped[str] = mapped_column(String(255), nullable=True)
    level: Mapped[str] = mapped_column(String(50), nullable=False, default="info")
    message: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
