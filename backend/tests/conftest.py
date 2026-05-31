"""Shared pytest fixtures for the test suite.

Defines fixtures that are automatically discovered by pytest across all test
modules, notably an async HTTP ``client`` bound directly to the FastAPI app via
an in-process ASGI transport (no network/server required).
"""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.fixture
async def client():
    """Yield an async HTTP client wired to the app via in-process ASGI transport.

    Lets tests call the API (e.g. ``await client.get("/api/games")``) without
    binding a real socket. The client is torn down automatically when the test
    completes.

    Yields:
        httpx.AsyncClient: Client targeting the FastAPI app at ``http://test``.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
