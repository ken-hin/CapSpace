import json
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, game_id: int):
        await websocket.accept()
        if game_id not in self.active_connections:
            self.active_connections[game_id] = set()
        self.active_connections[game_id].add(websocket)

    def disconnect(self, websocket: WebSocket, game_id: int):
        if game_id in self.active_connections:
            self.active_connections[game_id].discard(websocket)
            if not self.active_connections[game_id]:
                del self.active_connections[game_id]

    async def broadcast_to_game(self, game_id: int, data: dict):
        if game_id not in self.active_connections:
            return
        message = json.dumps(data)
        disconnected = set()
        for conn in self.active_connections[game_id]:
            try:
                await conn.send_text(message)
            except Exception:
                disconnected.add(conn)
        for conn in disconnected:
            self.disconnect(conn, game_id)

manager = ConnectionManager()
