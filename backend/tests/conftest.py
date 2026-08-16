"""Shared pytest fixtures for the test suite.

Fixtures here are auto-discovered by pytest across all test modules. They fall into
two groups: an async HTTP ``client`` bound directly to the FastAPI app via an
in-process ASGI transport (no network or running server required), and a database
test harness — ``_ensure_test_database`` creates the test database if it's missing,
``test_engine`` builds a session-wide engine against that separate test database,
``_create_schema`` creates and drops the tables around the run, and ``session`` hands
each test an isolated AsyncSession that is rolled back afterward.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.models.base import Base
import app.models            # noqa: F401
import app.sports.mlb.models # noqa: F401

TEST_DATABASE_URL = "postgresql+asyncpg://postgres:password@localhost:5432/sports_analytics_test"

# Name of the throwaway test database, plus a *synchronous* (psycopg2) URL to the
# always-present ``postgres`` maintenance database — the one place CREATE DATABASE for the
# test DB can be issued from. Kept next to TEST_DATABASE_URL so every test-DB coordinate
# lives in one spot. The migration test uses the same admin URL for the same reason:
# CREATE/DROP DATABASE can't run over asyncpg inside a transaction.
TEST_DATABASE_NAME = "sports_analytics_test"
ADMIN_DATABASE_URL = "postgresql+psycopg2://postgres:password@localhost:5432/postgres"

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


# ─────────────────────────────── TEST DATABASE BOOTSTRAP ───────────────────────────────────
@pytest.fixture(scope="session")
def _ensure_test_database():
    """Create the ``sports_analytics_test`` database once, if it doesn't already exist.

    This closes a gap that used to bite on any fresh machine: ``test_engine`` connects
    *straight* to ``sports_analytics_test`` and ``_create_schema``'s ``create_all`` only
    builds tables *inside* it — neither one ever issues ``CREATE DATABASE``. So on a checkout
    where the manual ``createdb`` step (docs/testing_guide.md §4) had never been run, every
    test errored with ``InvalidCatalogNameError: database "sports_analytics_test" does not
    exist``. With this fixture a fresh clone + ``docker compose up -d db`` + ``pytest`` just
    works, no manual step.

    It mirrors the ``migrated_db`` fixture in ``tests/test_migrations``: talk to the
    always-present ``postgres`` maintenance database through a *synchronous* psycopg2 engine
    in AUTOCOMMIT mode — ``CREATE DATABASE`` cannot run inside a transaction, and psycopg2 is
    the clean path for one-off admin DDL (asyncpg is awkward for it, which is exactly why the
    migration test reaches for psycopg2 too). It checks the ``pg_database`` catalog and
    creates the database only when it's missing. Unlike ``migrated_db`` it never drops the
    DB: the test database is meant to persist between runs — ``create_all``/``drop_all``
    manage the *tables* — so the next run finds it already there and skips straight past.

    Plain ``def`` (not ``async``) on purpose: it does all its work through psycopg2 before any
    async engine touches the test DB, and ``test_engine`` names it as a dependency so it is
    guaranteed to finish first.
    """
    # The maintenance DB always exists; AUTOCOMMIT because CREATE DATABASE can't run in a txn.
    admin = create_engine(ADMIN_DATABASE_URL, isolation_level="AUTOCOMMIT")
    with admin.connect() as connection:
        already_exists = connection.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :name"),
            {"name": TEST_DATABASE_NAME},
        ).scalar()
        if not already_exists:
            # A database name is an identifier, so it can't be a bound parameter — it has to
            # be interpolated. Safe here because TEST_DATABASE_NAME is a hard-coded constant,
            # never user input.
            connection.execute(text(f'CREATE DATABASE {TEST_DATABASE_NAME}'))
    admin.dispose()  # drop the admin pool; the test DB now exists for test_engine to use


# ───────────────────────────────────── TEST ENGINE ──────────────────────────────────────────
@pytest.fixture(scope="session")
async def test_engine(_ensure_test_database):
    """Provide one async Engine for the whole test session, bound to the TEST database.

    The engine owns the connection pool and is the entry point for talking to
    Postgres. It is built once (``scope="session"``) because standing up an engine
    and its pool is relatively expensive and every test can safely share it —
    per-test isolation is handled separately by the ``session`` fixture's rollback,
    not by giving each test its own engine.

    Depends on ``_ensure_test_database`` so the target database is guaranteed to exist
    before the pool opens its first connection — without that ordering the engine would
    point at a missing DB and every test would error before it started.

    Yields:
        AsyncEngine: Engine connected to ``sports_analytics_test``.
    """
    engine = create_async_engine(TEST_DATABASE_URL)  # build the engine + pool once, against the TEST DB
    yield engine                                     # hand it to any fixture/test that asks for it
    await engine.dispose()                           # close the pool so no connections leak past the run


# ───────────────────────────────────── SCHEMA SETUP ─────────────────────────────────────────
@pytest.fixture(scope="session", autouse=True)
async def _create_schema(test_engine):
    """Create the schema once before any test runs and drop it after the last one.

    ``autouse=True`` makes this run automatically for the session — no test has to
    request it. ``create_all`` builds every table registered on ``Base.metadata``,
    which is why all model modules are imported at the top of this file: importing a
    model registers its table, and ``create_all`` only creates tables it knows about.

    ``create_all`` runs inside its own ``begin()`` block that commits when the block
    exits, and that commit matters. The ``session`` fixture opens its own separate
    connection, and a separate connection can only see tables that have already been
    committed — leave the schema in an open, uncommitted transaction and tests fail
    with "relation does not exist". The matching ``drop_all`` after the ``yield``
    leaves the test database empty once the run finishes.

    Note:
        This creates plain Postgres tables straight from the models. The TimescaleDB
        hypertables are validated by the real Alembic migration under
        ``tests/test_migrations`` instead of here.
    """
    async with test_engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)  # DDL commits on block exit -> visible to other connections
    yield                                                    # tests run here, against the live schema
    async with test_engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)    # leave the test DB clean for next time


# ────────────────── SESSION FIXTURE (the harness each test plugs into) ─────────────────────
@pytest.fixture
async def session(test_engine):
    """Yield an AsyncSession whose writes are undone at the end of each test.

    This is the harness DB tests plug into: a test simply names ``session`` as a
    parameter and receives a ready-to-use session. Each test runs inside its own
    transaction that is rolled back on teardown, so tests never see one another's
    data and the database is left untouched between tests.

    How the isolation works:
        1. open a dedicated connection and begin an outer transaction on it,
        2. bind a session to that same connection,
        3. hand the session to the test,
        4. on teardown, close the session, then roll the outer transaction back.

    Because the connection is already inside a transaction when the session starts,
    SQLAlchemy nests the session's work in a SAVEPOINT by default. That means even a
    test that calls ``session.commit()`` stays contained — the commit releases the
    savepoint, and the outer ``rollback()`` still wipes everything out.

    Yields:
        AsyncSession: A session bound to a transaction that is rolled back afterward.
    """
    async with test_engine.connect() as connection:
        transaction = await connection.begin()  # outer transaction we roll back after the test
        # expire_on_commit=False keeps ORM objects usable after a commit, so tests can
        # still read an object's attributes when asserting on it.
        # join_transaction_mode="create_savepoint" runs the session inside a SAVEPOINT, so a
        # failed flush (e.g. an expected IntegrityError) rolls back only the savepoint and
        # leaves the outer transaction intact for a clean teardown rollback (no
        # "transaction already deassociated from connection" warning).
        session = async_sessionmaker(
            bind=connection,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )
        async with session() as sesh:
            yield sesh                           # the test runs here, using this session
        await transaction.rollback()             # undo everything the test did