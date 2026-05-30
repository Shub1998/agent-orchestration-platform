import pytest
from httpx import AsyncClient

TOOL_PAYLOAD = {
    "name": "weather_api",
    "display_name": "Weather API",
    "description": "Fetch current weather for a location",
    "url": "https://api.example.com/weather",
    "method": "POST",
    "headers": {"Authorization": "Bearer test-token"},
    "body_template": '{"location": "{{input}}"}',
    "is_active": True,
}


@pytest.mark.asyncio
async def test_create_custom_tool(client: AsyncClient):
    resp = await client.post("/api/v1/custom-tools", json=TOOL_PAYLOAD)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "weather_api"
    assert data["display_name"] == "Weather API"
    assert data["method"] == "POST"
    assert data["is_active"] is True
    assert "id" in data


@pytest.mark.asyncio
async def test_list_custom_tools(client: AsyncClient):
    await client.post("/api/v1/custom-tools", json=TOOL_PAYLOAD)
    await client.post("/api/v1/custom-tools", json={**TOOL_PAYLOAD, "name": "news_api", "display_name": "News API"})
    resp = await client.get("/api/v1/custom-tools")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_duplicate_tool_name_rejected(client: AsyncClient):
    await client.post("/api/v1/custom-tools", json=TOOL_PAYLOAD)
    resp = await client.post("/api/v1/custom-tools", json=TOOL_PAYLOAD)
    assert resp.status_code == 400
    assert "already exists" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_update_custom_tool(client: AsyncClient):
    created = (await client.post("/api/v1/custom-tools", json=TOOL_PAYLOAD)).json()
    resp = await client.patch(f"/api/v1/custom-tools/{created['id']}", json={"display_name": "Updated Weather", "is_active": False})
    assert resp.status_code == 200
    data = resp.json()
    assert data["display_name"] == "Updated Weather"
    assert data["is_active"] is False


@pytest.mark.asyncio
async def test_delete_custom_tool(client: AsyncClient):
    created = (await client.post("/api/v1/custom-tools", json=TOOL_PAYLOAD)).json()
    resp = await client.delete(f"/api/v1/custom-tools/{created['id']}")
    assert resp.status_code == 204
    tools = (await client.get("/api/v1/custom-tools")).json()
    assert all(t["id"] != created["id"] for t in tools)


@pytest.mark.asyncio
async def test_invalid_tool_name_rejected(client: AsyncClient):
    resp = await client.post("/api/v1/custom-tools", json={**TOOL_PAYLOAD, "name": "Invalid Name!"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_invalid_method_rejected(client: AsyncClient):
    resp = await client.post("/api/v1/custom-tools", json={**TOOL_PAYLOAD, "name": "another_tool", "method": "CONNECT"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_tool_appears_in_available_tools(client: AsyncClient):
    await client.post("/api/v1/custom-tools", json=TOOL_PAYLOAD)
    resp = await client.get("/api/v1/tools")
    assert resp.status_code == 200
    names = [t["name"] for t in resp.json()]
    assert "weather_api" in names
