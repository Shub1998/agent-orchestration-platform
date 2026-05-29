import pytest
from httpx import AsyncClient

AGENT_PAYLOAD = {
    "name": "Test Researcher",
    "role": "researcher",
    "system_prompt": "You are a test researcher agent.",
    "model": "gpt-4o-mini",
    "provider": "openai",
    "temperature": 0.5,
    "tools": ["web_search"],
    "memory_enabled": True,
    "max_output_tokens": 2048,
    "guardrail_keywords": ["confidential"],
}


@pytest.mark.asyncio
async def test_create_agent(client: AsyncClient):
    resp = await client.post("/api/v1/agents", json=AGENT_PAYLOAD)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Test Researcher"
    assert data["role"] == "researcher"
    assert data["tools"] == ["web_search"]
    assert data["max_output_tokens"] == 2048
    assert data["guardrail_keywords"] == ["confidential"]
    assert "id" in data


@pytest.mark.asyncio
async def test_list_agents(client: AsyncClient):
    await client.post("/api/v1/agents", json=AGENT_PAYLOAD)
    await client.post("/api/v1/agents", json={**AGENT_PAYLOAD, "name": "Agent 2"})
    resp = await client.get("/api/v1/agents")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_get_agent(client: AsyncClient):
    created = (await client.post("/api/v1/agents", json=AGENT_PAYLOAD)).json()
    resp = await client.get(f"/api/v1/agents/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == created["id"]


@pytest.mark.asyncio
async def test_update_agent(client: AsyncClient):
    created = (await client.post("/api/v1/agents", json=AGENT_PAYLOAD)).json()
    resp = await client.patch(f"/api/v1/agents/{created['id']}", json={"name": "Updated Name", "temperature": 0.9})
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated Name"
    assert resp.json()["temperature"] == 0.9


@pytest.mark.asyncio
async def test_delete_agent(client: AsyncClient):
    created = (await client.post("/api/v1/agents", json=AGENT_PAYLOAD)).json()
    resp = await client.delete(f"/api/v1/agents/{created['id']}")
    assert resp.status_code == 204
    resp2 = await client.get(f"/api/v1/agents/{created['id']}")
    assert resp2.status_code == 404


@pytest.mark.asyncio
async def test_get_nonexistent_agent(client: AsyncClient):
    resp = await client.get("/api/v1/agents/nonexistent-id")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_create_agent_missing_required_fields(client: AsyncClient):
    resp = await client.post("/api/v1/agents", json={"name": "No prompt"})
    assert resp.status_code == 422
