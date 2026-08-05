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


# TEST 1 — UNIQUE constraint: no two ParkFactors for the same (venue_id, season).
# Your model declares:  UniqueConstraint("venue_id", "season", name="uq_park_factors_venue_season")
async def test_duplicate_venue_season_is_rejected(session):
    # ARRANGE
    #   1. Create a Venue (ParkFactor.venue_id is a FK → venues.id, so a real
    #      venue must exist first). Add it, then `await session.flush()` to get
    #      its generated id.
    #   2. Create ParkFactor #1 for (venue.id, season=2025). Add + flush.
    #      This one should succeed.
    #
    # ACT + ASSERT
    #   3. Create ParkFactor #2 for the SAME (venue.id, 2025). Add it, then:
    #
    #          with pytest.raises(IntegrityError):
    #              await session.flush()
    #
    #      The test passes only if that flush raises.
    ...


# TEST 2 — NOT NULL: a required column can't be empty.
# e.g. ParkFactor.venue_id and .season are nullable=False.
async def test_missing_required_field_is_rejected(session):
    # ARRANGE: build a ParkFactor but leave a required field unset (e.g. no season).
    # ACT + ASSERT: add it and expect flush to raise IntegrityError.
    #
    #     with pytest.raises(IntegrityError):
    #         await session.flush()
    ...


# TEST 3 (stretch) — FOREIGN KEY: can't point at a venue that doesn't exist.
async def test_orphan_foreign_key_is_rejected(session):
    # ARRANGE: ParkFactor with venue_id = 999999 (no such venue) + a valid season.
    # ACT + ASSERT: flush raises IntegrityError.
    #     with pytest.raises(IntegrityError):
    #         await session.flush()
    ...
