import uuid
from datetime import datetime
from sqlalchemy import String, Text, Float, Integer, Boolean, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(100), nullable=False, default="assistant")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False, default="gpt-4o-mini")
    provider: Mapped[str] = mapped_column(String(50), nullable=False, default="openai")
    temperature: Mapped[float] = mapped_column(Float, nullable=False, default=0.7)
    max_iterations: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    memory_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    memory_collection: Mapped[str] = mapped_column(String(255), nullable=True)
    tools: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    telegram_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    telegram_chat_ids: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    avatar_color: Mapped[str] = mapped_column(String(20), nullable=False, default="#6366f1")
    # Guardrails
    max_output_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=4096)
    guardrail_keywords: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
