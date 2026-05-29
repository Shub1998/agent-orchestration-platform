"""
Mock LLM for demo mode. Returns realistic pre-scripted responses by agent role.
Used when provider="demo" — no API key required.
"""
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from typing import Any, List, Optional


DEMO_RESPONSES = {
    "researcher": """## Research Findings: {topic}

**Key Facts:**
- LangGraph is an open-source library by LangChain for building stateful, multi-actor applications with LLMs
- It models agent workflows as directed graphs where nodes are computation steps and edges are transitions
- Released in 2024, it supports cycles, conditional branching, and human-in-the-loop interrupts
- Built on top of LangChain, it integrates natively with all LangChain tools and LLM providers
- The StateGraph primitive persists state across nodes using a TypedDict schema

**Recent Developments (2024–2025):**
- LangGraph Cloud launched for hosted execution with built-in persistence
- Added support for streaming token output mid-graph
- Introduced multi-agent supervisor pattern for coordinating agent teams
- Native integration with LangSmith for tracing and debugging

**Sources:**
- LangChain blog: "Introducing LangGraph" (Jan 2024)
- GitHub: langchain-ai/langgraph — 8.2k stars
- LangChain documentation: python.langchain.com/docs/langgraph
""",

    "summarizer": """## Executive Summary

**Core Insight:** LangGraph transforms complex multi-agent AI workflows into reliable, production-ready systems by modeling them as directed graphs with persistent state.

**Key Takeaways:**
1. **Graph-based execution** — agents become nodes; control flow becomes edges; cycles enable retry logic
2. **State persistence** — built-in SQLite/PostgreSQL checkpointing means workflows survive crashes
3. **Production-ready** — native streaming, human-in-the-loop, and LangSmith tracing out of the box

**Bottom Line:** For teams building multi-agent AI systems, LangGraph is the current best-in-class framework — it solves state management, conditional routing, and observability that custom runtimes would take weeks to rebuild.
""",

    "triage": '{"category": "billing", "priority": "high", "summary": "Customer reports incorrect charge on invoice — routing to billing specialist"}',

    "billing_support": """Thank you for reaching out about the billing issue. I've reviewed your concern.

**What I found:**
- Your account shows a charge that may be a duplicate transaction
- This sometimes occurs when a payment is retried during a brief network timeout

**Next steps:**
1. I've flagged your account for a billing review — this will be completed within 1 business day
2. If confirmed as a duplicate, a full refund will be issued to your original payment method within 3–5 business days
3. You'll receive a confirmation email at the address on file

Is there anything else I can help you with today?
""",

    "technical_support": """I can help you troubleshoot this issue. Let me walk you through the diagnostic steps.

**Initial diagnosis:**
Based on your description, this appears to be a configuration issue rather than a bug.

**Troubleshooting steps:**
1. Clear your browser cache and hard-refresh (Ctrl+Shift+R / Cmd+Shift+R)
2. Check that your API key has the correct permissions in your account dashboard
3. Verify the request format matches the latest API spec (v2 introduced breaking changes in auth headers)
4. If using SDK, update to the latest version: `pip install --upgrade agentflow-sdk`

**If the issue persists:**
Please share the full error message and request ID — I can escalate to our engineering team with that information.
""",

    "general_support": """Great question! Here's a quick overview of how this feature works.

**How it works:**
The workflow builder lets you visually connect AI agents into pipelines. Each agent handles a specific task, and you draw arrows (edges) to define the order and routing logic.

**Getting started:**
1. Go to **Agents** and create your agents with custom system prompts
2. Go to **Workflows** → **New Workflow** or use a template
3. Drag agents onto the canvas and connect them
4. Click **Run Workflow** and enter your prompt

**Pro tip:** Use the Customer Support Triage template as a starting point — it shows conditional routing in action.

Let me know if you'd like a walkthrough of any specific feature!
""",

    "assistant": """I've processed your request and here's my response:

Based on the information provided, I can offer the following analysis:

The question touches on several important aspects that are worth examining carefully. Let me break this down:

**Analysis:**
- The core issue involves multiple interconnected factors
- Current best practices suggest a systematic approach
- Recent developments in this space have opened new possibilities

**Recommendation:**
Taking everything into account, the most effective approach would be to start with the foundational elements and build incrementally, validating each step before proceeding.

Is there a specific aspect you'd like me to explore in more depth?
""",
}


def _get_demo_response(agent_role: str, prompt: str) -> str:
    role = agent_role.lower().replace(" ", "_").replace("-", "_")
    for key in DEMO_RESPONSES:
        if key in role or role in key:
            response = DEMO_RESPONSES[key]
            topic = prompt[:50] if len(prompt) > 10 else "the requested topic"
            return response.replace("{topic}", topic)
    return DEMO_RESPONSES["assistant"]


class DemoLLM(BaseChatModel):
    """Mock LLM for demo mode — returns role-appropriate responses instantly."""
    agent_role: str = "assistant"

    @property
    def _llm_type(self) -> str:
        return "demo"

    def _generate(self, messages: List[BaseMessage], stop: Optional[List[str]] = None, **kwargs) -> ChatResult:
        prompt = messages[-1].content if messages else ""
        response_text = _get_demo_response(self.agent_role, str(prompt))
        msg = AIMessage(
            content=response_text,
            usage_metadata={"input_tokens": 150, "output_tokens": 200, "total_tokens": 350},
        )
        return ChatResult(generations=[ChatGeneration(message=msg)])

    async def _agenerate(self, messages: List[BaseMessage], stop: Optional[List[str]] = None, **kwargs) -> ChatResult:
        return self._generate(messages, stop, **kwargs)
