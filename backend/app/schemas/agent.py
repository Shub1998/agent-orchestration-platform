from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class AgentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    role: str = Field(default="assistant", max_length=100)
    description: str = Field(default="")
    system_prompt: str = Field(..., min_length=1)
    model: str = Field(default="gpt-4o-mini")
    provider: str = Field(default="openai")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_iterations: int = Field(default=10, ge=1, le=50)
    memory_enabled: bool = Field(default=True)
    tools: list[str] = Field(default_factory=list)
    telegram_enabled: bool = Field(default=False)
    telegram_chat_ids: list[int] = Field(default_factory=list)
    avatar_color: str = Field(default="#6366f1")
    max_output_tokens: int = Field(default=4096, ge=256, le=32000)
    guardrail_keywords: list[str] = Field(default_factory=list)


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    model: Optional[str] = None
    provider: Optional[str] = None
    temperature: Optional[float] = None
    max_iterations: Optional[int] = None
    memory_enabled: Optional[bool] = None
    tools: Optional[list[str]] = None
    telegram_enabled: Optional[bool] = None
    telegram_chat_ids: Optional[list[int]] = None
    avatar_color: Optional[str] = None
    max_output_tokens: Optional[int] = None
    guardrail_keywords: Optional[list[str]] = None


class AgentResponse(BaseModel):
    id: str
    name: str
    role: str
    description: str
    system_prompt: str
    model: str
    provider: str
    temperature: float
    max_iterations: int
    memory_enabled: bool
    memory_collection: Optional[str]
    tools: list[str]
    telegram_enabled: bool
    telegram_chat_ids: list[int]
    avatar_color: str
    max_output_tokens: int
    guardrail_keywords: list[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AgentTestRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
