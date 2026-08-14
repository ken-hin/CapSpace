"""Migration test — prove the Alembic migration registers TimescaleDB hypertables.

This one is DIFFERENT from the model tests, and understanding why is the point:

    Base.metadata.create_all (used by the model tests) builds the tables straight from
    the models as PLAIN Postgres tables. It does NOT run the migration's
    ``op.execute("SELECT create_hypertable(...)")`` lines — only the Alembic migration
    does. So this test runs the REAL migration and then asks TimescaleDB's own catalog
    which tables it manages as hypertables. If someone ever deletes a create_hypertable
    call, the table still works — silently as a plain table — and only this test catches it.

Tables the migration registers as hypertables:
    stat_events       -> occurred_at
    pitch_events      -> pitch_time
    book_odds         -> captured_at
    weather_snapshots -> captured_at

Isolation: the migration runs into its OWN throwaway database (NOT the
``sports_analytics_test`` DB the model tests build with create_all), so the two
schema-management approaches never collide. The ``migrated_db`` fixture creates that DB,
enables the ``timescaledb`` extension (the migration itself doesn't), runs
``alembic upgrade head``, yields a sync engine for catalog queries, and drops the DB
afterward.

These tests are intentionally synchronous: ``alembic.command.upgrade`` drives the async
``env.py`` via ``asyncio.run(...)``, which must be called from a plain (non-async)
context. That's why a sync driver (psycopg2) is needed alongside asyncpg.
"""

import pytest
from pathlib import Path
from sqlalchemy import create_engine, text
from alembic.config import Config
from alembic import command

# tests/test_migrations/ -> tests/ -> backend/
BACKEND_DIR = Path(__file__).resolve().parents[2]
# Maintenance DB (always exists) used to CREATE/DROP the throwaway migration DB.
ADMIN_URL = "postgresql+psycopg2://postgres:password@localhost:5432/postgres"
MIGRATION_DB = "sports_analytics_migration_test"
# Async URL for Alembic (env.py runs an async engine); sync URL for admin + catalog queries.
MIGRATION_URL_ASYNC = f"postgresql+asyncpg://postgres:password@localhost:5432/{MIGRATION_DB}"
MIGRATION_URL_SYNC = f"postgresql+psycopg2://postgres:password@localhost:5432/{MIGRATION_DB}"


@pytest.fixture(scope="module")
def migrated_db():
    """Build an isolated DB, run the real Alembic migration into it, yield a sync engine.

    Module-scoped because standing up a fresh database and replaying the full migration
    is expensive — both tests share one build. Kept on its own database so it never
    collides with the create_all schema the model tests build on ``sports_analytics_test``.

    Yields:
        Engine: a plain synchronous engine connected to the migrated database, for
        querying TimescaleDB's ``timescaledb_information.hypertables`` catalog.
    """
    # 1. (Re)create a throwaway database — isolated from the model-test schema.
    #    AUTOCOMMIT because CREATE/DROP DATABASE cannot run inside a transaction.
    admin = create_engine(ADMIN_URL, isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(text(f'DROP DATABASE IF EXISTS {MIGRATION_DB} WITH (FORCE)'))
        conn.execute(text(f'CREATE DATABASE {MIGRATION_DB}'))
    admin.dispose()

    # 2. TimescaleDB is preloaded by the image, but the extension must be created
    #    per-database — the migration doesn't, so do it before create_hypertable runs.
    setup = create_engine(MIGRATION_URL_SYNC, isolation_level="AUTOCOMMIT")
    with setup.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb"))
    setup.dispose()

    # 3. Run the REAL migration. env.py drives an async engine, so keep the +asyncpg URL;
    #    absolute paths make this independent of pytest's working directory.
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    cfg.set_main_option("sqlalchemy.url", MIGRATION_URL_ASYNC)
    command.upgrade(cfg, "head")

    # 4. Hand tests a plain sync engine to query Timescale's catalog.
    engine = create_engine(MIGRATION_URL_SYNC)
    yield engine

    # Teardown: close connections, then drop the whole DB (no downgrade needed).
    engine.dispose()
    admin = create_engine(ADMIN_URL, isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(text(f'DROP DATABASE IF EXISTS {MIGRATION_DB} WITH (FORCE)'))
    admin.dispose()


def test_pitch_events_is_hypertable(migrated_db):
    """pitch_events is registered as a hypertable after the migration runs.

    Timescale records each hypertable in ``timescaledb_information.hypertables``; a row
    for ``pitch_events`` means ``create_hypertable`` actually ran (a plain CREATE TABLE
    would leave no such row).
    """
    with migrated_db.connect() as conn:
        rows = conn.execute(text(
            "SELECT hypertable_name FROM timescaledb_information.hypertables "
            "WHERE hypertable_name = 'pitch_events'"
        )).all()
    # Exactly one catalog row -> Timescale manages this table as a hypertable.
    assert len(rows) == 1


def test_book_odds_and_stat_events_are_hypertables(migrated_db):
    """book_odds and stat_events are both registered as hypertables.

    One catalog query for both names; two rows back means both were converted.
    """
    with migrated_db.connect() as conn:
        rows = conn.execute(text(
            "SELECT hypertable_name FROM timescaledb_information.hypertables "
            "WHERE hypertable_name IN ('book_odds', 'stat_events')"
        )).all()
    # Both names present -> two catalog rows.
    assert len(rows) == 2


def test_weather_snapshots_is_hypertable(migrated_db):
    """weather_snapshots is registered as a hypertable (partitioned on captured_at)."""
    with migrated_db.connect() as conn:
        rows = conn.execute(text(
            "SELECT hypertable_name FROM timescaledb_information.hypertables "
            "WHERE hypertable_name = 'weather_snapshots'"
        )).all()
    assert len(rows) == 1
