"""Constraint tests — prove the DATABASE rejects invalid data.

"Unhappy path" tests: deliberately write data that breaks a constraint and
assert the database raises IntegrityError. Runs against the real test DB via the
`session` fixture (conftest.py), which rolls back after each test.

`await session.flush()` sends the INSERT so the constraint fires now, inside the
`pytest.raises(...)` block. Once it raises, the transaction is poisoned — one
failing write per test, then the fixture rolls back.
"""

import pytest
from sqlalchemy.exc import IntegrityError
from app.models.enums import Sport
from app.models.venue import Venue
from app.sports.mlb.models.park_factor import ParkFactor


async def test_duplicate_venue_season_is_rejected(session):
    """Two ParkFactor rows sharing the same unique key are rejected.

    Proves the composite ``UniqueConstraint`` holds at the database level: the
    first row inserts cleanly, and the second — identical on the unique key —
    raises ``IntegrityError`` when flushed. The venue is created first so both
    park factors reference a real parent, isolating the failure to the unique
    rule rather than a foreign-key violation.

    Note:
        The full key is ``(venue_id, season, window_years)``; ``window_years``
        defaults to 3 on both rows, which is what makes them collide.
    """
    # Create a venue and flush so its generated id is available as a FK.
    t_venue = Venue(name="Test Venue", city="Nashville", sport=Sport.MLB, external_id="t_venue_id")
    session.add(t_venue)
    await session.flush()

    # First ParkFactor for this venue+season: flush it in so the next one collides.
    session.add(ParkFactor(venue_id=t_venue.id,  season=2025))
    await session.flush()

    # Second ParkFactor on the same unique key -> the flush must raise.
    session.add(ParkFactor(venue_id=t_venue.id, season=2025))
    with pytest.raises(IntegrityError):
        await session.flush()


async def test_missing_required_field_is_rejected(session):
    """A ParkFactor missing a required field (``season=None``) is rejected.

    ``season`` is ``nullable=False``, so a NULL violates the not-null
    constraint. The row is otherwise valid — it points at a real venue — so the
    flush fails specifically on the missing value, raising ``IntegrityError``.
    """
    t_venue = Venue(name="Test Venue", city="Nashville", sport=Sport.MLB, external_id="t_venue_id")
    session.add(t_venue)
    await session.flush()

    # season is NOT NULL; passing None violates that constraint on flush.
    session.add(ParkFactor(venue_id=t_venue.id, season=None))
    with pytest.raises(IntegrityError):
        await session.flush()


async def test_orphan_foreign_key_is_rejected(session):
    """A ParkFactor whose ``venue_id`` points at no venue is rejected.

    ``venue_id`` is a foreign key into ``venues``; using an id that does not
    exist violates referential integrity, so the database refuses the INSERT
    with ``IntegrityError`` on flush. No venue is created here — the missing
    parent is the whole point.
    """
    # venue_id 999999 has no matching venues row -> foreign-key violation on flush.
    session.add(ParkFactor(venue_id=999999, season=2024))
    with pytest.raises(IntegrityError):
        await session.flush()
