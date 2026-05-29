import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    execution_id: Mapped[str] = mapped_column(String(36), ForeignKey("executions.id", ondelete="CASCADE"), nullable=True)
    agent_id: Mapped[str] = mapped_column(String(36), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tool_name: Mapped[str] = mapped_column(String(255), nullable=True)
    tool_call_id: Mapped[str] = mapped_column(String(255), nullable=True)
    telegram_chat_id: Mapped[int] = mapped_column(Integer, nullable=True)
    telegram_message_id: Mapped[int] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
