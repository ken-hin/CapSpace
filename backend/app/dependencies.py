"""Shared FastAPI dependency providers.

Re-exports the common request-scoped dependency callables (database session and
Redis client) from a single module so route handlers can import them from one
convenient location, e.g. ``from app.dependencies import get_db``.
"""

from app.db.session import get_db
from app.db.redis import get_redis

# Public dependency callables intended for use with ``fastapi.Depends``.
__all__ = ["get_db", "get_redis"]
