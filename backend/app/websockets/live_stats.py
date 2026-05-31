"""Live-stats WebSocket endpoint.

Exposes the ``/ws/game/{game_id}`` WebSocket that streams live updates to
clients. It subscribes to the game's Redis pub/sub channel (where the ingestion
pipeline publishes events) and relays each event to all connected clients via the
shared :data:`~app.websockets.manager.manager`.
"""

import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.websockets.manager import manager
from app.db.redis import redis_client

router = APIRouter()

@router.websocket("/ws/game/{game_id}")
async def game_websocket(websocket: WebSocket, game_id: int):
    """Stream live events for a game to a connected client.

    Registers the client, subscribes to the game's Redis channel, and forwards
    published events until the client disconnects, at which point it tears down
    the subscription and background listener.

    Args:
        websocket: The client WebSocket connection.
        game_id: Path parameter identifying the game to stream.
    """
    await manager.connect(websocket, game_id)
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(f"game:{game_id}:events")

    async def listen_redis():
        """Relay messages from the game's Redis channel to all game subscribers."""
        async for message in pubsub.listen():
            if message["type"] == "message":
                data = json.loads(message["data"])
                await manager.broadcast_to_game(game_id, data)

    # Run the Redis listener concurrently while we block on the client socket.
    redis_task = asyncio.create_task(listen_redis())
    try:
        # Keep the connection open; inbound frames are ignored (server-push only).
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        # Client went away: deregister and clean up the Redis subscription/task.
        manager.disconnect(websocket, game_id)
        redis_task.cancel()
        await pubsub.unsubscribe(f"game:{game_id}:events")
        await pubsub.close()
