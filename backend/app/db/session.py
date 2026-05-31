"""Async SQLAlchemy engine and session management.

Creates the process-wide async database engine and session factory from the
configured ``DATABASE_URL`` and exposes :func:`get_db`, the request-scoped
session dependency used throughout the API and service layers. The engine is
configured with a connection pool sized for moderate concurrency.
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.config import get_settings

settings = get_settings()

# Async engine backing all database access. ``echo`` mirrors DEBUG so SQL is
# logged during development; the pool settings cap concurrent connections.
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=20,
    max_overflow=10,
)

# Session factory. ``expire_on_commit=False`` keeps ORM objects usable after a
# commit (e.g. when serializing a just-created row in a response).
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncSession:
    """Provide a request-scoped async database session (FastAPI dependency).

    Opens a new session, commits it if the request handler succeeds, rolls it
    back on any exception, and always closes it afterward. Designed to be used
    with ``fastapi.Depends`` so each request gets an isolated transaction.

    Yields:
        AsyncSession: The active database session for the current request.

    Raises:
        Exception: Re-raises any error after rolling back the transaction.
    """
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
