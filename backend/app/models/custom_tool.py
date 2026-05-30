import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, JSON, DateTime, Text
from app.database import Base


class CustomTool(Base):
    __tablename__ = "custom_tools"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, unique=True, nullable=False)        # tool identifier (alphanum + _)
    display_name = Column(String, nullable=False)
    description = Column(Text, nullable=False)                # shown to the LLM
    url = Column(String, nullable=False)
    method = Column(String, default="POST")                   # GET/POST/PUT/DELETE
    headers = Column(JSON, default=dict)
    body_template = Column(Text, default="")                  # {{input}} placeholder
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
