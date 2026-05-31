"""WebSocket connection registry.

Defines :class:`ConnectionManager`, which tracks the set of active WebSocket
clients per game and fans out messages to them, plus the module-level singleton
``manager`` shared across the application.
"""

import json
from fastapi import WebSocket

class ConnectionManager:
    """Tracks active WebSocket connections grouped by game and broadcasts to them.

    Connections are stored as ``{game_id: {WebSocket, ...}}`` so a live update
    for a game can be pushed only to the clients watching that game.
    """

    def __init__(self):
        """Initialize an empty game-id → connection-set registry."""
        self.active_connections: dict[int, set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, game_id: int):
        """Accept a WebSocket and register it under the given game.

        Args:
            websocket: The incoming client WebSocket to accept and track.
            game_id: The game the client wants live updates for.
        """
        await websocket.accept()
        if game_id not in self.active_connections:
            self.active_connections[game_id] = set()
        self.active_connections[game_id].add(websocket)

    def disconnect(self, websocket: WebSocket, game_id: int):
        """Remove a WebSocket from a game's set, pruning the game if now empty.

        Args:
            websocket: The connection to remove.
            game_id: The game the connection was registered under.
        """
        if game_id in self.active_connections:
            self.active_connections[game_id].discard(websocket)
            if not self.active_connections[game_id]:
                del self.active_connections[game_id]

    async def broadcast_to_game(self, game_id: int, data: dict):
        """Send a JSON message to every client connected to a game.

        Connections that raise while sending are collected and disconnected
        afterward so a single dead client doesn't interrupt the broadcast.

        Args:
            game_id: The game whose subscribers should receive the message.
            data: JSON-serializable payload to deliver.
        """
        if game_id not in self.active_connections:
            return
        message = json.dumps(data)
        disconnected = set()
        for conn in self.active_connections[game_id]:
            try:
                await conn.send_text(message)
            except Exception:
                # Mark unreachable clients for cleanup after iterating.
                disconnected.add(conn)
        for conn in disconnected:
            self.disconnect(conn, game_id)

# Application-wide singleton used by the WebSocket endpoint(s).
manager = ConnectionManager()
