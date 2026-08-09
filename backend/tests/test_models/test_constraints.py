"""Constraint tests — prove the DATABASE rejects invalid data.

These are the "unhappy path" tests. For each one you deliberately try to write
data that breaks a constraint, then assert the database raises IntegrityError.
If no error is raised, the guardrail isn't actually protecting you.

Runs against the real test DB (see the setup notes in conftest.py). Every test
below asks for the `session` fixture, which hands you a rolled-back-after
AsyncSession so nothing you insert here survives into the next test.

--------------------------------------------------------------------------------
IMPORTS YOU'LL LIKELY NEED (write them yourself):
    import pytest
    from sqlalchemy.exc import IntegrityError
    from app.models.venue import Venue
    from app.sports.mlb.models.park_factor import ParkFactor

WHY flush()? `await session.flush()` sends the pending INSERT to Postgres NOW,
which is when the constraint is actually checked — so the IntegrityError fires
inside your `pytest.raises(...)` block instead of later. (commit would also work
but ends the transaction; flush keeps it open so the fixture can roll back.)

NOTE: once a flush raises IntegrityError the transaction is "poisoned" — don't
keep using the same session after the expected failure. One failing write per
test; the fixture rolls back when the test ends.
--------------------------------------------------------------------------------
"""

import pytest
from sqlalchemy.exc import IntegrityError
from app.models.enums import Sport
from app.models.venue import Venue
from app.sports.mlb.models.park_factor import ParkFactor

async def test_duplicate_venue_season_is_rejected(session):
    # Create a venue, add to test session, and flush to get generated venue.id.
    venue = Venue(name="Test Venue", city="Nashville", sport=Sport.MLB, external_id="test_venue_id")
    session.add(venue)
    await session.flush()
    # Create first ParkFactor, add to test session, and flush to ensure it's added before second.
    session.add(ParkFactor(venue_id=venue.id,  season=2025))
    await session.flush()
    # Attempt to add second ParkFactor with same venue_id and season, expect IntegrityError.
    session.add(ParkFactor(venue_id=venue.id, season=2025))
    with pytest.raises(IntegrityError):
        await session.flush()


async def test_missing_required_field_is_rejected(session):
    venue = Venue(name="Test Venue", city="Nashville", sport=Sport.MLB, external_id="test_venue_id")
    session.add(venue)
    await session.flush()
    # Attempt to add a ParkFactor with season=None, expect IntegrityError.
    session.add(ParkFactor(venue_id=venue.id, season=None))
    with pytest.raises(IntegrityError):
        await session.flush()


async def test_orphan_foreign_key_is_rejected(session):
    # Attempt to add a ParkFactor with venue_id=999999, expect IntegrityError.
    session.add(ParkFactor(venue_id=999999, season=2024))
    with pytest.raises(IntegrityError):
        await session.flush()

