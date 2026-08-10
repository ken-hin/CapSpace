"""Composite-unique tests — broaden the "no duplicates" coverage past ParkFactor.

test_constraints.py already proves ONE unique rule (ParkFactor venue+season). But
almost every model has its own multi-column UniqueConstraint, and each is a separate
promise the DB makes. This file covers more of them, and teaches two things beyond
the single case you've already written:

  1. `pytest.mark.parametrize` — run the SAME test body against several models, so
     you add coverage without copy-pasting a near-identical test each time.

  2. The difference between "duplicate" and "not a duplicate" on a COMPOSITE key.
     A constraint on (a, b, c) only fires when ALL THREE match. Rows that differ in
     any one column are allowed — and proving that is what stops you from writing a
     constraint that's stricter (or looser) than you think.

Runs against the real test DB via `session` (conftest.py). Same flush/rollback rules
as the other constraint tests: `await session.flush()` triggers the check; one failing
write per test; the fixture rolls back.

--------------------------------------------------------------------------------
IMPORTS YOU'LL LIKELY NEED (write them yourself):
    import pytest
    from sqlalchemy.exc import IntegrityError
    from app.models.enums import Sport
    from app.models.venue import Venue
    from app.sports.mlb.models.park_factor import ParkFactor
    from app.sports.mlb.models.park_dimensions import ParkDimensions

Cheap-to-build models used below (only the required columns shown):
    ParkDimensions(venue_id=..., season=...)          # unique: (venue_id, season)
    ParkFactor(venue_id=..., season=..., window_years=...)  # unique: (venue_id, season, window_years)
--------------------------------------------------------------------------------
"""

import pytest
from sqlalchemy.exc import IntegrityError
from app.models.enums import Sport
from app.models.venue import Venue
from app.sports.mlb.models.park_factor import ParkFactor
from app.sports.mlb.models.park_dimensions import ParkDimensions


# TEST 1 — the (venue_id, season) unique rule on ParkDimensions rejects a duplicate.
# This mirrors the ParkFactor test you've already written, on a different model —
# a good one to write solo first before the parametrized version below.
async def test_duplicate_park_dimensions_is_rejected(session):
    # ARRANGE: minimal Venue + flush for venue.id.
    #          Add ParkDimensions(venue_id=venue.id, season=2025) + flush.
    # ACT + ASSERT: a second ParkDimensions with the SAME (venue_id, season):
    #     with pytest.raises(IntegrityError):
    #         await session.flush()
    ...


# TEST 2 — the COMPOSITE nature of ParkFactor's (venue_id, season, window_years):
# changing ONLY window_years is NOT a duplicate and must be allowed.
#
# This is the "robustness" companion to the existing rejection test. Together they
# pin down the exact shape of the constraint: same park + season but a different
# window is a legitimately different row.
async def test_same_venue_season_different_window_is_allowed(session):
    # ARRANGE: Venue + flush.
    #          ParkFactor(venue_id=venue.id, season=2025, window_years=1) + flush.
    # ACT: add ParkFactor(venue_id=venue.id, season=2025, window_years=3) + flush.
    # ASSERT: NO error, and both rows exist (e.g. assert the second got an id, or
    #         SELECT count(*) for that venue+season and assert it's 2).
    ...


# TEST 3 — one test body, many models (parametrize).
#
# `build` is a tiny factory: given the venue id, it returns a fresh model instance
# whose unique key is fixed. Calling it twice makes an intentional duplicate. Fill in
# the factories, then the body stays identical across models.
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
    # ARRANGE: minimal Venue + flush for venue.id.
    #          Insert the first row:  session.add(build(venue.id)); await session.flush()
    # ACT + ASSERT: insert a second identical row and expect rejection:
    #     session.add(build(venue.id))
    #     with pytest.raises(IntegrityError):
    #         await session.flush()
    ...
