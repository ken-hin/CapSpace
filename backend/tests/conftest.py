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


# ═══════════════════════════════════════════════════════════════════════════════
# DATABASE TEST HARNESS  —  SCAFFOLD (comments + pseudocode; write the real code)
# ═══════════════════════════════════════════════════════════════════════════════
#
# GOAL: give every DB test a ready-to-use AsyncSession that talks to a SEPARATE
#       test database and rolls back after each test, so tests stay isolated and
#       never touch your dev data.
#
# ── ONE-TIME PREP (outside this file) ─────────────────────────────────────────
#
#   1. Add to backend/pyproject.toml so async tests/fixtures actually run:
#
#          [tool.pytest.ini_options]
#          asyncio_mode = "auto"
#          testpaths = ["tests"]
#
#   2. Start the DB container and create the throwaway test database once:
#
#          docker compose up -d db
#          docker exec sports-analytics-db createdb -U postgres sports_analytics_test
#
# ── IMPORTS you'll add at the top of this file ────────────────────────────────
#
#       from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
#       from app.models.base import Base
#       # Import every model module so Base.metadata "knows" all tables. Importing
#       # the two package __init__ files that re-export them is the easy way:
#       import app.models            # noqa: F401
#       import app.sports.mlb.models # noqa: F401
#
#
# ── 1) TEST ENGINE ────────────────────────────────────────────────────────────
# TODO: a SEPARATE engine pointed at the TEST db. Do NOT reuse
#       app.db.session.engine — that one points at your DEV database.
#
#   TEST_DATABASE_URL = "postgresql+asyncpg://postgres:password@localhost:5432/sports_analytics_test"
#
#   @pytest.fixture(scope="session")
#   def test_engine():
#       # create_async_engine(TEST_DATABASE_URL)
#       # scope="session" => built once for the whole test run
#       ...
#
#
# ── 2) SCHEMA SETUP ───────────────────────────────────────────────────────────
# TODO: before any test runs, create all tables in the test DB from your models.
#       (This is create_all — fine for relationship/constraint tests. The
#        hypertable test runs the real migration instead; see test_migrations/.)
#
#   @pytest.fixture(scope="session", autouse=True)
#   async def _create_schema(test_engine):
#       # async with test_engine.begin() as conn:
#       #     await conn.run_sync(Base.metadata.create_all)
#       # yield
#       # # (optional teardown) await conn.run_sync(Base.metadata.drop_all)
#       ...
#
#
# ── 3) SESSION FIXTURE  (the harness each test plugs into) ─────────────────────
# TODO: hand each test a session wrapped so EVERYTHING it does is rolled back.
#       A test asks for it just by naming it as a parameter:  def test_x(session):
#
#   @pytest.fixture
#   async def session(test_engine):
#       # rough shape — open a connection, begin a transaction, bind a session to
#       # it, yield, then roll the transaction back so nothing survives:
#       #
#       #   async with test_engine.connect() as conn:
#       #       txn = await conn.begin()
#       #       Session = async_sessionmaker(bind=conn, expire_on_commit=False)
#       #       async with Session() as s:
#       #           yield s
#       #       await txn.rollback()
#       ...
