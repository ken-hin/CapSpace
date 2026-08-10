"""Composite primary-key tests — prove the multi-column PK rejects duplicates.

Most tables have a single-column primary key (`id`). A few of yours don't: the
time-series tables declare a COMPOSITE primary key so the timestamp can be part of
the key (this is what lets them become TimescaleDB hypertables later). Examples:

    WeatherSnapshot -> PrimaryKeyConstraint("id", "captured_at")
    StatEvent       -> PrimaryKeyConstraint("id", "occurred_at")
    BookOdds        -> composite PK too

A primary key is "unique + not null" on the WHOLE combination. So two rows are only
a collision when EVERY key column matches. That's the twist worth testing, and it
comes with a gotcha:

    `id` is autoincrement. If you insert two rows WITHOUT setting id, each gets a
    fresh id and they never collide — so you'd be testing nothing. To actually force
    a duplicate you must set the SAME id AND the same timestamp on both rows.

We use WeatherSnapshot because it only needs one parent (a Venue). Runs against the
real test DB via `session` (conftest.py); usual flush/rollback rules apply.

NOTE: create_all builds these as PLAIN Postgres tables in the test DB (the hypertable
step lives in the Alembic migration, tested separately). A plain table still enforces
the composite PK, so this test is valid here.

--------------------------------------------------------------------------------
IMPORTS YOU'LL LIKELY NEED (write them yourself):
    import pytest
    from datetime import datetime, timezone
    from sqlalchemy.exc import IntegrityError
    from app.models.enums import Sport
    from app.models.venue import Venue
    from app.models.weather_snapshot import WeatherSnapshot
--------------------------------------------------------------------------------
"""


# TEST 1 — same (id, captured_at) is rejected as a duplicate primary key.
async def test_duplicate_composite_pk_is_rejected(session):
    # ARRANGE
    #   1. minimal Venue + `await session.flush()` for venue.id.
    #   2. pick a fixed timestamp:  ts = datetime(2026, 4, 1, 18, 0, tzinfo=timezone.utc)
    #   3. insert WeatherSnapshot(id=1, venue_id=venue.id, captured_at=ts) + flush.
    #
    # ACT + ASSERT
    #   4. insert a SECOND WeatherSnapshot with the SAME id=1 and SAME captured_at=ts:
    #          session.add(WeatherSnapshot(id=1, venue_id=venue.id, captured_at=ts))
    #          with pytest.raises(IntegrityError):
    #              await session.flush()
    ...


# TEST 2 — same id but a DIFFERENT captured_at is allowed (proves the PK is composite).
#
# If this row were rejected, your "primary key" would effectively be `id` alone and the
# timestamp wouldn't be doing its job. Allowing it is what makes the table a time series.
async def test_same_id_different_timestamp_is_allowed(session):
    # ARRANGE: Venue + flush. Two timestamps ts1 != ts2.
    #          WeatherSnapshot(id=1, venue_id=venue.id, captured_at=ts1) + flush.
    # ACT: WeatherSnapshot(id=1, venue_id=venue.id, captured_at=ts2) + flush.
    # ASSERT: no error — both rows coexist because (1, ts1) != (1, ts2).
    ...
