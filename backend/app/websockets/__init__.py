"""WebSockets package.

Provides real-time, push-based delivery of live game data to clients: the
connection registry (:mod:`app.websockets.manager`) and the WebSocket endpoint
that bridges Redis pub/sub to connected browsers (:mod:`app.websockets.live_stats`).
"""
