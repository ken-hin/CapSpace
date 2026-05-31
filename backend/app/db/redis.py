"""Redis client setup.

Instantiates a shared async Redis client from the configured ``REDIS_URL`` and
exposes :func:`get_redis` as a FastAPI dependency. Used for caching and any
pub/sub or ephemeral state (e.g. live-stat fan-out).
"""

import redis.asyncio as redis
from app.config import get_settings

settings = get_settings()

# Shared async Redis client. ``decode_responses`` returns ``str`` instead of
# ``bytes`` so callers don't have to decode values manually.
redis_client = redis.from_url(
    settings.REDIS_URL,
    encoding="utf-8",
    decode_responses=True,
)


async def get_redis() -> redis.Redis:
    """Provide the shared Redis client (FastAPI dependency).

    Returns:
        redis.Redis: The process-wide async Redis client instance.
    """
    return redis_client
