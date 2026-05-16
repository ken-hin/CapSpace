import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.websockets.manager import manager
from app.db.redis import redis_client

router = APIRouter()

@router.websocket("/ws/game/{game_id}")
async def game_websocket(websocket: WebSocket, game_id: int):
    await manager.connect(websocket, game_id)
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(f"game:{game_id}:events")

    async def listen_redis():
        async for message in pubsub.listen():
            if message["type"] == "message":
                data = json.loads(message["data"])
                await manager.broadcast_to_game(game_id, data)

    redis_task = asyncio.create_task(listen_redis())
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, game_id)
        redis_task.cancel()
        await pubsub.unsubscribe(f"game:{game_id}:events")
        await pubsub.close()
