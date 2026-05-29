from typing import TypedDict, Annotated, Optional
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class AgentFlowState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    current_agent: str
    execution_id: str
    workflow_id: str
    input: str
    output: str
    iteration: int
    context: dict
    error: Optional[str]
    telegram_chat_id: Optional[int]
    approval_decision: Optional[str]   # "approved" | "rejected"
    rejection_comment: Optional[str]   # reviewer feedback on rejection
