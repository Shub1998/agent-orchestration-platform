import pytest
from httpx import AsyncClient

WORKFLOW_PAYLOAD = {
    "name": "Test Pipeline",
    "description": "A test workflow",
    "trigger_type": "manual",
}

AGENT_PAYLOAD = {
    "name": "Test Agent",
    "role": "assistant",
    "system_prompt": "You are a helpful assistant.",
    "model": "gpt-4o-mini",
    "provider": "openai",
}


@pytest.mark.asyncio
async def test_create_workflow(client: AsyncClient):
    resp = await client.post("/api/v1/workflows", json=WORKFLOW_PAYLOAD)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Test Pipeline"
    assert data["trigger_type"] == "manual"
    assert "id" in data
    # Auto-creates start and end nodes
    assert any(n["node_type"] == "start" for n in data["nodes"])
    assert any(n["node_type"] == "end" for n in data["nodes"])


@pytest.mark.asyncio
async def test_list_workflows(client: AsyncClient):
    await client.post("/api/v1/workflows", json=WORKFLOW_PAYLOAD)
    await client.post("/api/v1/workflows", json={**WORKFLOW_PAYLOAD, "name": "Workflow 2"})
    resp = await client.get("/api/v1/workflows")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_get_workflow_with_graph(client: AsyncClient):
    created = (await client.post("/api/v1/workflows", json=WORKFLOW_PAYLOAD)).json()
    resp = await client.get(f"/api/v1/workflows/{created['id']}")
    assert resp.status_code == 200
    data = resp.json()
    assert "nodes" in data
    assert "edges" in data


@pytest.mark.asyncio
async def test_update_workflow(client: AsyncClient):
    created = (await client.post("/api/v1/workflows", json=WORKFLOW_PAYLOAD)).json()
    resp = await client.patch(f"/api/v1/workflows/{created['id']}",
                              json={"name": "Renamed", "trigger_type": "schedule",
                                    "trigger_config": {"cron": "0 9 * * *"}})
    assert resp.status_code == 200
    assert resp.json()["name"] == "Renamed"
    assert resp.json()["trigger_type"] == "schedule"


@pytest.mark.asyncio
async def test_delete_workflow(client: AsyncClient):
    created = (await client.post("/api/v1/workflows", json=WORKFLOW_PAYLOAD)).json()
    resp = await client.delete(f"/api/v1/workflows/{created['id']}")
    assert resp.status_code == 204
    resp2 = await client.get(f"/api/v1/workflows/{created['id']}")
    assert resp2.status_code == 404


@pytest.mark.asyncio
async def test_save_workflow_graph(client: AsyncClient):
    agent = (await client.post("/api/v1/agents", json=AGENT_PAYLOAD)).json()
    wf = (await client.post("/api/v1/workflows", json=WORKFLOW_PAYLOAD)).json()

    nodes = [
        {"node_type": "start", "label": "Start", "position_x": 100, "position_y": 200, "config": {}},
        {"node_type": "agent", "agent_id": agent["id"], "label": "My Agent",
         "position_x": 400, "position_y": 200, "config": {}},
        {"node_type": "end", "label": "End", "position_x": 700, "position_y": 200, "config": {}},
    ]

    resp = await client.post(f"/api/v1/workflows/{wf['id']}/graph", json={"nodes": nodes, "edges": []})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["nodes"]) == 3
    assert any(n["node_type"] == "agent" for n in data["nodes"])


@pytest.mark.asyncio
async def test_trigger_workflow_creates_execution(client: AsyncClient):
    wf = (await client.post("/api/v1/workflows", json=WORKFLOW_PAYLOAD)).json()
    resp = await client.post(f"/api/v1/workflows/{wf['id']}/trigger",
                             json={"prompt": "test prompt"})
    assert resp.status_code == 202
    data = resp.json()
    assert data["status"] == "pending"
    assert data["workflow_id"] == wf["id"]
    assert "id" in data
