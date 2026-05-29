import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class MemoryEntry(Base):
    __tablename__ = "memory_entries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id: Mapped[str] = mapped_column(String(36), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    chroma_doc_id: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    source_execution_id: Mapped[str] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
