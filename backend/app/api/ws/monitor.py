import json
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import redis.asyncio as aioredis
from app.config import settings

router = APIRouter()


@router.websocket("/ws/executions/{execution_id}/logs")
async def log_stream(websocket: WebSocket, execution_id: str):
    await websocket.accept()
    redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(f"execution:{execution_id}:logs")

    try:
        await websocket.send_text(json.dumps({"type": "connected", "execution_id": execution_id}))

        async def listen():
            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = message["data"]
                    await websocket.send_text(data)
                    parsed = json.loads(data)
                    if parsed.get("type") == "execution_complete":
                        break

        await asyncio.wait_for(listen(), timeout=600)

    except (WebSocketDisconnect, asyncio.TimeoutError):
        pass
    except Exception:
        pass
    finally:
        await pubsub.unsubscribe(f"execution:{execution_id}:logs")
        await redis_client.aclose()
