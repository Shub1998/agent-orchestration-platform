"""Tests for the execution API endpoints."""
import pytest
from httpx import AsyncClient


AGENT_PAYLOAD = {
    "name": "Exec Test Agent",
    "role": "assistant",
    "system_prompt": "You help with tests.",
    "model": "gpt-4o-mini",
    "provider": "openai",
}

WORKFLOW_PAYLOAD = {"name": "Test Workflow", "description": ""}


async def _create_workflow_with_agent(client: AsyncClient) -> tuple[str, str]:
    agent = (await client.post("/api/v1/agents", json=AGENT_PAYLOAD)).json()
    wf = (await client.post("/api/v1/workflows", json=WORKFLOW_PAYLOAD)).json()

    graph = {
        "nodes": [
            {"id": "start", "node_type": "start", "label": "Start", "agent_id": None, "position_x": 0, "position_y": 0, "config": {}},
            {"id": "n1", "node_type": "agent", "label": "Agent", "agent_id": agent["id"], "position_x": 200, "position_y": 0, "config": {}},
            {"id": "end", "node_type": "end", "label": "End", "agent_id": None, "position_x": 400, "position_y": 0, "config": {}},
        ],
        "edges": [
            {"id": "e1", "source_node_id": "start", "target_node_id": "n1", "condition": None, "label": ""},
            {"id": "e2", "source_node_id": "n1", "target_node_id": "end", "condition": None, "label": ""},
        ],
    }
    await client.post(f"/api/v1/workflows/{wf['id']}/graph", json=graph)
    return wf["id"], agent["id"]


@pytest.mark.asyncio
async def test_list_executions_empty(client: AsyncClient):
    resp = await client.get("/api/v1/executions")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_trigger_workflow_creates_execution(client: AsyncClient):
    from unittest.mock import patch
    wf_id, _ = await _create_workflow_with_agent(client)

    with patch("app.workers.execution_tasks.run_workflow_task.delay") as mock_delay:
        resp = await client.post(f"/api/v1/workflows/{wf_id}/trigger", json={"prompt": "hello"})
        assert resp.status_code == 202
        data = resp.json()
        assert data["workflow_id"] == wf_id
        assert data["status"] == "pending"
        assert mock_delay.called


@pytest.mark.asyncio
async def test_get_execution(client: AsyncClient):
    from unittest.mock import patch
    wf_id, _ = await _create_workflow_with_agent(client)

    with patch("app.workers.execution_tasks.run_workflow_task.delay"):
        created = (await client.post(f"/api/v1/workflows/{wf_id}/trigger", json={"prompt": "hi"})).json()

    resp = await client.get(f"/api/v1/executions/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == created["id"]


@pytest.mark.asyncio
async def test_get_nonexistent_execution(client: AsyncClient):
    resp = await client.get("/api/v1/executions/does-not-exist")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_execution_logs_empty(client: AsyncClient):
    from unittest.mock import patch
    wf_id, _ = await _create_workflow_with_agent(client)

    with patch("app.workers.execution_tasks.run_workflow_task.delay"):
        created = (await client.post(f"/api/v1/workflows/{wf_id}/trigger", json={"prompt": "hi"})).json()

    resp = await client.get(f"/api/v1/executions/{created['id']}/logs")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_cancel_pending_execution(client: AsyncClient):
    from unittest.mock import patch
    wf_id, _ = await _create_workflow_with_agent(client)

    with patch("app.workers.execution_tasks.run_workflow_task.delay"):
        created = (await client.post(f"/api/v1/workflows/{wf_id}/trigger", json={"prompt": "hi"})).json()

    resp = await client.delete(f"/api/v1/executions/{created['id']}")
    assert resp.status_code == 204

    detail = (await client.get(f"/api/v1/executions/{created['id']}")).json()
    assert detail["status"] == "cancelled"


@pytest.mark.asyncio
async def test_approve_non_awaiting_execution_rejected(client: AsyncClient):
    from unittest.mock import patch
    wf_id, _ = await _create_workflow_with_agent(client)

    with patch("app.workers.execution_tasks.run_workflow_task.delay"):
        created = (await client.post(f"/api/v1/workflows/{wf_id}/trigger", json={"prompt": "hi"})).json()

    # Execution is 'pending', not 'awaiting_approval'
    resp = await client.post(
        f"/api/v1/executions/{created['id']}/approve",
        json={"decision": "approve", "comment": ""},
    )
    assert resp.status_code == 400
    assert "awaiting approval" in resp.json()["detail"].lower()
