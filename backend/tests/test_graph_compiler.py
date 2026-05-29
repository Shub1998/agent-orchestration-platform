import pytest
from unittest.mock import patch, MagicMock
from app.core.graph_compiler import GraphCompiler
from app.core.state import AgentFlowState
from langchain_core.messages import HumanMessage, AIMessage


MOCK_AGENT = {
    "id": "agent-1",
    "name": "Mock Agent",
    "role": "assistant",
    "system_prompt": "You are a helpful assistant.",
    "model": "gpt-4o-mini",
    "provider": "openai",
    "temperature": 0.7,
    "max_iterations": 3,
    "memory_enabled": False,
    "tools": [],
    "max_output_tokens": 1024,
    "guardrail_keywords": [],
}

MOCK_WORKFLOW = {"id": "wf-1", "name": "Test", "description": "", "trigger_type": "manual"}

START_NODE = {"id": "start", "node_type": "start", "label": "Start", "agent_id": None, "position_x": 0, "position_y": 0, "config": {}}
AGENT_NODE = {"id": "node1", "node_type": "agent", "label": "Mock Agent", "agent_id": "agent-1", "position_x": 200, "position_y": 0, "config": {}}
END_NODE = {"id": "end", "node_type": "end", "label": "End", "agent_id": None, "position_x": 400, "position_y": 0, "config": {}}

EDGES = [
    {"id": "e1", "source_node_id": "start", "target_node_id": "node1", "condition": None, "label": ""},
    {"id": "e2", "source_node_id": "node1", "target_node_id": "end", "condition": None, "label": ""},
]


def test_graph_compiler_builds_compiled_graph():
    compiler = GraphCompiler()
    with patch("app.core.agent_builder.ChatOpenAI") as mock_llm_cls, \
         patch("app.core.log_emitter.log_emitter.emit"), \
         patch("app.core.memory_manager.memory_manager.retrieve", return_value=""), \
         patch("app.core.memory_manager.memory_manager.store"):

        mock_llm = MagicMock()
        mock_response = AIMessage(content="Test output")
        mock_response.tool_calls = []
        mock_llm.bind_tools.return_value = mock_llm
        mock_llm.invoke.return_value = mock_response
        mock_llm_cls.return_value = mock_llm

        graph = compiler.compile(MOCK_WORKFLOW, [START_NODE, AGENT_NODE, END_NODE], EDGES, {"agent-1": MOCK_AGENT})
        assert graph is not None


def test_graph_execution_runs_agent():
    compiler = GraphCompiler()
    with patch("app.core.agent_builder.ChatOpenAI") as mock_llm_cls, \
         patch("app.core.log_emitter.log_emitter.emit"), \
         patch("app.core.log_emitter.log_emitter.emit_completion"), \
         patch("app.core.memory_manager.memory_manager.retrieve", return_value=""), \
         patch("app.core.memory_manager.memory_manager.store"):

        mock_llm = MagicMock()
        mock_response = AIMessage(content="Agent output here")
        mock_response.tool_calls = []
        mock_response.usage_metadata = {"input_tokens": 100, "output_tokens": 50}
        mock_llm.bind_tools.return_value = mock_llm
        mock_llm.invoke.return_value = mock_response
        mock_llm_cls.return_value = mock_llm

        graph = compiler.compile(MOCK_WORKFLOW, [START_NODE, AGENT_NODE, END_NODE], EDGES, {"agent-1": MOCK_AGENT})

        initial_state = AgentFlowState(
            messages=[HumanMessage(content="What is 2+2?")],
            current_agent="", execution_id="test-exec", workflow_id="wf-1",
            input="What is 2+2?", output="", iteration=0, context={}, error=None,
            telegram_chat_id=None,
        )
        config = {"configurable": {"thread_id": "test-exec"}}
        result = graph.invoke(initial_state, config=config)
        assert result["output"] == "Agent output here"
        assert result["current_agent"] == "Mock Agent"


def test_conditional_routing():
    """Test that conditional edges route based on output content."""
    compiler = GraphCompiler()

    billing_node = {"id": "billing", "node_type": "agent", "label": "Billing", "agent_id": "agent-1", "position_x": 400, "position_y": 100, "config": {}}
    tech_node = {"id": "tech", "node_type": "agent", "label": "Tech", "agent_id": "agent-1", "position_x": 400, "position_y": 300, "config": {}}
    end_b = {"id": "end_b", "node_type": "end", "label": "End", "agent_id": None, "position_x": 600, "position_y": 100, "config": {}}
    end_t = {"id": "end_t", "node_type": "end", "label": "End", "agent_id": None, "position_x": 600, "position_y": 300, "config": {}}
    triage_node = {"id": "triage", "node_type": "agent", "label": "Triage", "agent_id": "agent-1", "position_x": 200, "position_y": 200, "config": {}}

    nodes = [START_NODE, triage_node, billing_node, tech_node, end_b, end_t]
    edges = [
        {"id": "e0", "source_node_id": "start", "target_node_id": "triage", "condition": None, "label": ""},
        {"id": "e1", "source_node_id": "triage", "target_node_id": "billing", "condition": "billing", "label": "billing"},
        {"id": "e2", "source_node_id": "triage", "target_node_id": "tech", "condition": "technical", "label": "technical"},
        {"id": "e3", "source_node_id": "billing", "target_node_id": "end_b", "condition": None, "label": ""},
        {"id": "e4", "source_node_id": "tech", "target_node_id": "end_t", "condition": None, "label": ""},
    ]

    with patch("app.core.agent_builder.ChatOpenAI") as mock_llm_cls, \
         patch("app.core.log_emitter.log_emitter.emit"), \
         patch("app.core.log_emitter.log_emitter.emit_completion"), \
         patch("app.core.memory_manager.memory_manager.retrieve", return_value=""), \
         patch("app.core.memory_manager.memory_manager.store"):

        call_count = [0]

        def side_effect(messages):
            call_count[0] += 1
            if call_count[0] == 1:
                # Triage response
                r = AIMessage(content='{"category": "billing", "summary": "invoice issue"}')
            else:
                r = AIMessage(content="Your billing issue is resolved.")
            r.tool_calls = []
            r.usage_metadata = {"input_tokens": 50, "output_tokens": 20}
            return r

        mock_llm = MagicMock()
        mock_llm.bind_tools.return_value = mock_llm
        mock_llm.invoke.side_effect = side_effect
        mock_llm_cls.return_value = mock_llm

        graph = compiler.compile(MOCK_WORKFLOW, nodes, edges, {"agent-1": MOCK_AGENT})
        initial_state = AgentFlowState(
            messages=[HumanMessage(content="I was charged twice")],
            current_agent="", execution_id="test-2", workflow_id="wf-1",
            input="I was charged twice", output="", iteration=0, context={}, error=None,
            telegram_chat_id=None,
        )
        result = graph.invoke(initial_state, config={"configurable": {"thread_id": "test-2"}})
        assert "billing" in result["output"].lower() or "resolved" in result["output"].lower()
