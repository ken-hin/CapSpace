"""Composite primary-key tests — prove the multi-column PK rejects duplicates.

Most tables have a single-column primary key (`id`). A few of yours don't: the
time-series tables declare a COMPOSITE primary key so the timestamp is part of the
key (this is what lets them become TimescaleDB hypertables later), e.g.
WeatherSnapshot -> PrimaryKeyConstraint("id", "captured_at").

A primary key is "unique + not null" across the WHOLE combination, so two rows only
collide when EVERY key column matches. The gotcha: `id` is autoincrement, so two
rows inserted without an explicit id get different ids and never collide — to force
a duplicate you must set the SAME id AND the same timestamp on both rows.

Runs against the real test DB via the `session` fixture (conftest.py); usual
flush/rollback rules apply. create_all builds these as PLAIN Postgres tables here
(the hypertable step lives in the Alembic migration, tested separately), and a
plain table still enforces the composite PK, so these tests are valid.
"""

import pytest
from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError
from app.models.enums import Sport
from app.models.venue import Venue
from app.models.weather_snapshot import WeatherSnapshot


async def test_duplicate_composite_pk_is_rejected(session):
    """Two WeatherSnapshot rows with the same ``(id, captured_at)`` are rejected.

    The primary key is the whole ``(id, captured_at)`` pair, so a duplicate has to
    match on both columns. Both rows here pin ``id=1`` and the same ``captured_at``,
    so the second INSERT collides with the composite PK and the flush raises
    ``IntegrityError``. The venue is created first so the snapshots point at a real
    parent, isolating the failure to the PK rather than the ``venue_id`` foreign key.
    """
    # Parent venue: flush so its generated id is available as a FK.
    tv = Venue(name = "Test Venue", city = "Nashville", sport = Sport.MLB, external_id = "t_venue_id")
    session.add(tv)
    await session.flush()

    # One fixed capture time reused on both rows so their (id, captured_at) keys match.
    ts = datetime(2026, 4, 1, 18, 0, tzinfo=timezone.utc)

    # First snapshot inserts cleanly.
    session.add(WeatherSnapshot(id=1, venue_id=tv.id, captured_at=ts))
    await session.flush()

    # Second snapshot on the SAME (id, captured_at) -> composite-PK collision on flush.
    session.add(WeatherSnapshot(id=1, venue_id=tv.id, captured_at=ts))
    with pytest.raises(IntegrityError):
        await session.flush()


async def test_same_id_different_timestamp_is_allowed(session):
    """Same ``id`` but a different ``captured_at`` is allowed — the PK is composite.

    If ``id`` alone were the key, the second row would be rejected. Because the key
    is ``(id, captured_at)``, ``(1, ts1)`` and ``(1, ts2)`` are distinct, so both
    rows persist — which is what makes the table usable as a time series. The flush
    raising nothing is the assertion here.
    """
    # Parent venue.
    tv = Venue(name = "Test Venue", city = "Nashville", sport = Sport.MLB, external_id = "t_venue_id")
    session.add(tv)
    await session.flush()

    # Two different capture times; id is held constant at 1.
    ts1 = datetime(2026, 4, 1, 18, 0, tzinfo=timezone.utc)
    ts2 = datetime(2026, 4, 1, 19, 0, tzinfo=timezone.utc)
    session.add(WeatherSnapshot(id=1, venue_id=tv.id, captured_at=ts1))
    await session.flush()

    # (1, ts2) differs from (1, ts1) in the key, so this second row is accepted.
    session.add(WeatherSnapshot(id=1, venue_id=tv.id, captured_at=ts2))
    await session.flush()
