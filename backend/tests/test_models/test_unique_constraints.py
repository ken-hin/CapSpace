"""Composite-unique tests — broaden the "no duplicates" coverage past ParkFactor.

test_constraints.py already proves ONE unique rule (ParkFactor venue+season). Almost
every model has its own multi-column UniqueConstraint, though, and each is a separate
promise the DB makes. This file covers more of them and teaches two ideas beyond that
single case:

  1. ``pytest.mark.parametrize`` — run the SAME test body against several models, so
     you add coverage without copy-pasting a near-identical test each time.

  2. The difference between "duplicate" and "not a duplicate" on a COMPOSITE key. A
     constraint on (a, b, c) only fires when ALL THREE match; rows differing in any one
     column are allowed. Proving both halves pins the constraint to exactly those columns.

Runs against the real test DB via the `session` fixture (conftest.py). Same flush/rollback
rules as the other constraint tests: `await session.flush()` triggers the check, one failing
write per test, and the fixture rolls back.
"""

import pytest
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from app.models.enums import Sport
from app.models.venue import Venue
from app.sports.mlb.models.park_factor import ParkFactor
from app.sports.mlb.models.park_dimensions import ParkDimensions


async def test_duplicate_park_dimensions_is_rejected(session):
    """A duplicate ParkDimensions on ``(venue_id, season)`` is rejected.

    The same rejection shape as the ParkFactor test in test_constraints.py, on a
    different model: the first row inserts cleanly, and a second with the identical
    ``(venue_id, season)`` violates the unique constraint, so the flush raises
    ``IntegrityError``.
    """
    # Parent venue; flush for its generated id.
    venue = Venue(name="Test Venue", city="Nashville", sport=Sport.MLB)
    session.add(venue)
    await session.flush()
    venue_id = venue.id

    # First row inserts cleanly.
    session.add(ParkDimensions(venue_id=venue_id, season=2025))
    await session.flush()

    # Second row on the same (venue_id, season) -> unique violation on flush.
    session.add(ParkDimensions(venue_id=venue_id, season=2025))
    with pytest.raises(IntegrityError):
        await session.flush()


async def test_same_venue_season_different_window_is_allowed(session):
    """Same venue + season but a different window_years is NOT a duplicate.

    ParkFactor's unique key is the full triple ``(venue_id, season, window_years)``, so
    two rows sharing venue and season but differing on ``window_years`` are legitimately
    distinct, and both persist. This is the robustness companion to the rejection test:
    the second flush not raising is the core proof, and the count confirms both rows landed.
    """
    # Parent venue.
    venue = Venue(name="Test Venue", city="Nashville", sport=Sport.MLB)
    session.add(venue)
    await session.flush()

    # Same venue + season, different window_years -> distinct on the composite key.
    session.add(ParkFactor(venue_id=venue.id, season=2025, window_years=1))
    await session.flush()

    session.add(ParkFactor(venue_id=venue.id, season=2025, window_years=3))
    await session.flush()  # no IntegrityError == the real assertion

    # Belt-and-suspenders: confirm both rows persisted for that venue + season.
    pf_count = await session.execute(
            select(func.count()).
            select_from(ParkFactor).
            where(ParkFactor.venue_id == venue.id, ParkFactor.season == 2025)
    )

    assert pf_count.scalar_one() == 2


# `build` is a per-model factory: given a venue id it returns a fresh instance whose
# unique key is fixed, so calling it twice makes an intentional duplicate. Add a model
# to the coverage by adding a `pytest.param` here — the test body stays identical.
@pytest.mark.parametrize(
    "build",
    [
        pytest.param(lambda vid: ParkDimensions(venue_id=vid, season=2025), id="park_dimensions"),
        pytest.param(lambda vid: ParkFactor(venue_id=vid, season=2025), id="park_factor"),
        # ADD MORE as you go. Models keyed on a Player instead of a Venue need a Player
        # parent built in the ARRANGE step, so start with the venue-keyed ones above.
    ],
)
async def test_composite_unique_rejects_duplicate(session, build):
    """One rejection test body run against several models (parametrized).

    For each ``build`` factory, the first instance inserts cleanly and a second built
    from the same factory reuses the identical unique key — so the second flush must
    raise ``IntegrityError``. Adding a model above extends the coverage for free.
    """
    # Parent venue; flush for its generated id.
    venue = Venue(name="Test Venue", city="Nashville", sport=Sport.MLB)
    session.add(venue)
    await session.flush()

    # First row inserts cleanly.
    session.add(build(venue.id))
    await session.flush()

    # Second row with the same unique key -> rejected on flush.
    session.add(build(venue.id))
    with pytest.raises(IntegrityError):
        await session.flush()
