"""Check-constraint tests — prove the DATABASE rejects out-of-range *values*.

Unlike the unique / not-null / FK checks in test_constraints.py, these target a
CheckConstraint: ParkFactor.source must be one of ('baseball_savant', 'computed').
The row is otherwise well-formed — only the value is disallowed. Because the
column defaults to "baseball_savant", the happy path never trips the rule, so it
needs its own explicit test.

Runs against the real test DB via the `session` fixture (conftest.py). `flush()`
is when Postgres evaluates the constraint; a raised IntegrityError poisons the
transaction, so it's one failing write per test and the fixture rolls back.
"""

import pytest
from sqlalchemy.exc import IntegrityError
from app.models.enums import Sport
from app.models.venue import Venue
from app.sports.mlb.models.park_factor import ParkFactor


async def test_invalid_source_is_rejected(session):
    """A ``source`` value outside the allow-list is rejected by the check constraint.

    ``ParkFactor.source`` is free-form ``String`` at the type level, but a
    ``CheckConstraint`` restricts it to ``('baseball_savant', 'computed')``. The
    row here is well-formed and points at a real venue — its only problem is the
    value — so the flush fails specifically on the check, raising
    ``IntegrityError``.
    """
    # Parent venue: flush so its generated id is available as a FK.
    t_venue = Venue(name="Test Venue", city="Nashville", sport=Sport.MLB, external_id="t_venue_id")
    session.add(t_venue)
    await session.flush()

    # 'wikipedia' is well-formed text but not in ('baseball_savant', 'computed').
    t_venue_id = t_venue.id
    t_park_factor = ParkFactor(venue_id=t_venue_id, season=2025, source="wikipedia")
    session.add(t_park_factor)

    # The flush is where the DB checks the constraint -> IntegrityError.
    with pytest.raises(IntegrityError):
        await session.flush()


async def test_valid_source_is_accepted(session):
    """An allowed ``source`` value persists cleanly.

    The companion to the rejection test: it proves the allow-list actually
    admits the values the app uses, guarding against a too-strict constraint
    that would silently refuse good data. The flush raises nothing, and the
    populated ``id`` confirms the row was inserted.
    """
    # Parent venue.
    t_venue = Venue(name="Test Venue", city="Nashville", sport=Sport.MLB, external_id="t_venue_id")
    session.add(t_venue)
    await session.flush()

    # 'baseball_savant' is in the allow-list, so this row is valid.
    t_venue_id = t_venue.id
    t_park_factor = ParkFactor(venue_id=t_venue_id, season=2025, source="baseball_savant")
    session.add(t_park_factor)

    # No IntegrityError; a populated id confirms the INSERT landed.
    await session.flush()
    assert t_park_factor.id is not None
