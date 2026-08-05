"""Migration test — prove the Alembic migration registers TimescaleDB hypertables.

This one is DIFFERENT from the model tests, and understanding why is the point:

    Base.metadata.create_all (used by the model tests) builds your tables straight
    from the models — as PLAIN Postgres tables. It does NOT run your
    `op.execute("SELECT create_hypertable(...)")` lines. Only the Alembic
    migration runs those.

So here you run the REAL migration against the test DB, then ask TimescaleDB's own
catalog which tables it manages as hypertables. If someone ever deletes the
create_hypertable call, the table still works — silently as a plain table — and
only this test will catch it.

Tables that SHOULD be hypertables (from your migration):
    stat_events   -> occurred_at
    pitch_events  -> pitch_time
    book_odds     -> captured_at

--------------------------------------------------------------------------------
IMPORTS / TOOLS YOU'LL LIKELY NEED (write them yourself):
    import pytest
    from sqlalchemy import create_engine, text     # a PLAIN (sync) engine is fine here
    from alembic.config import Config
    from alembic import command

WHY sync here? Running migrations and a one-off catalog query doesn't need the
async session machinery — a normal sync engine keeps this test simpler.
--------------------------------------------------------------------------------
"""


# SETUP — run migrations on the test DB (NOT create_all).
# @pytest.fixture(scope="module")
# def migrated_db():
#     # TODO:
#     #   1. cfg = Config("alembic.ini")                      # path to your alembic config
#     #   2. point it at the TEST db, e.g.
#     #        cfg.set_main_option("sqlalchemy.url", TEST_DATABASE_URL_SYNC)
#     #      (sync URL = postgresql://...  — no +asyncpg — for alembic's sync run)
#     #   3. command.upgrade(cfg, "head")                     # build the schema for real
#     #   4. yield                                            # tests run here
#     #   5. (optional) command.downgrade(cfg, "base")        # leave the DB clean
#     ...


# TEST — pitch_events is registered as a hypertable.
def test_pitch_events_is_hypertable(migrated_db):
    # Query Timescale's catalog and assert the table shows up:
    #
    #   SELECT hypertable_name
    #   FROM timescaledb_information.hypertables
    #   WHERE hypertable_name = 'pitch_events';
    #
    # ARRANGE: open a connection to the test DB (sync engine).
    # ACT: run the query above with sqlalchemy `text(...)`.
    # ASSERT: exactly one row comes back (the table is a hypertable).
    ...


# TEST — book_odds and stat_events are hypertables too.
def test_book_odds_and_stat_events_are_hypertables(migrated_db):
    # Same catalog query for 'book_odds' and 'stat_events'; assert BOTH are present.
    # (Either query them individually, or `WHERE hypertable_name IN (...)` and
    #  assert you got 2 rows back.)
    ...
