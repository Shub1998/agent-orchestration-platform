import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_templates(client: AsyncClient):
    resp = await client.get("/api/v1/templates")
    assert resp.status_code == 200
    templates = resp.json()
    slugs = [t["slug"] for t in templates]
    assert "research-pipeline" in slugs
    assert "customer-support" in slugs


@pytest.mark.asyncio
async def test_instantiate_research_pipeline(client: AsyncClient):
    resp = await client.post("/api/v1/templates/research-pipeline/instantiate")
    assert resp.status_code == 200
    data = resp.json()
    assert "workflow_id" in data
    assert len(data["agents"]) == 2

    # Verify the workflow was actually created with nodes
    wf_resp = await client.get(f"/api/v1/workflows/{data['workflow_id']}")
    assert wf_resp.status_code == 200
    wf = wf_resp.json()
    assert len(wf["nodes"]) >= 4  # start, researcher, summarizer, end
    agent_nodes = [n for n in wf["nodes"] if n["node_type"] == "agent"]
    assert len(agent_nodes) == 2


@pytest.mark.asyncio
async def test_instantiate_customer_support(client: AsyncClient):
    resp = await client.post("/api/v1/templates/customer-support/instantiate")
    assert resp.status_code == 200
    data = resp.json()
    assert "workflow_id" in data
    assert len(data["agents"]) == 4

    wf_resp = await client.get(f"/api/v1/workflows/{data['workflow_id']}")
    wf = wf_resp.json()
    agent_nodes = [n for n in wf["nodes"] if n["node_type"] == "agent"]
    assert len(agent_nodes) == 4
    # Should have conditional edges
    conditional_edges = [e for e in wf["edges"] if e.get("condition")]
    assert len(conditional_edges) == 3  # billing, technical, general


@pytest.mark.asyncio
async def test_instantiate_unknown_template(client: AsyncClient):
    resp = await client.post("/api/v1/templates/does-not-exist/instantiate")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_cost_calculator():
    from app.core.cost_calculator import calculate_cost, extract_token_usage

    cost = calculate_cost("gpt-4o-mini", 1000, 500)
    assert cost > 0
    assert cost < 0.01  # gpt-4o-mini is cheap

    cost_gpt4 = calculate_cost("gpt-4o", 1000, 500)
    assert cost_gpt4 > cost  # gpt-4o costs more


@pytest.mark.asyncio
async def test_guardrail_keyword_blocking():
    from unittest.mock import patch, MagicMock
    from app.core.agent_builder import AgentBuilder
    from app.core.state import AgentFlowState
    from langchain_core.messages import HumanMessage, AIMessage

    builder = AgentBuilder()
    agent_data = {
        "id": "test-guard", "name": "GuardAgent", "role": "assistant",
        "system_prompt": "You are a test agent.", "model": "gpt-4o-mini",
        "provider": "openai", "temperature": 0.7, "max_iterations": 3,
        "memory_enabled": False, "tools": [], "max_output_tokens": 1024,
        "guardrail_keywords": ["secret"],
    }

    with patch("app.core.agent_builder.ChatOpenAI") as mock_llm_cls, \
         patch("app.core.log_emitter.log_emitter.emit"):
        mock_llm = MagicMock()
        mock_response = AIMessage(content="This is a secret message")
        mock_response.tool_calls = []
        mock_response.usage_metadata = {"input_tokens": 10, "output_tokens": 5}
        mock_llm.bind_tools.return_value = mock_llm
        mock_llm.invoke.return_value = mock_response
        mock_llm_cls.return_value = mock_llm

        node_fn = builder.build(agent_data)
        state = AgentFlowState(
            messages=[HumanMessage(content="test")],
            current_agent="", execution_id="g1", workflow_id="wf1",
            input="test", output="", iteration=0, context={}, error=None, telegram_chat_id=None,
        )
        result = node_fn(state)
        assert "blocked" in result["output"].lower()
