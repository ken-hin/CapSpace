"""Default-value tests — prove rows get the right values when you DON'T set them.

Constraints prove bad data is rejected. Defaults prove *good* data is filled in.
Your models lean on two different kinds of default, and the distinction is the
whole point of this file:

  1. Python-side `default=...`  (e.g. Game.status="scheduled", Game.home_score=0,
     Venue.country="USA", Venue.is_active=True). SQLAlchemy fills these in when it
     builds the INSERT — so the value is present after a flush.

  2. Server-side `server_default=func.now()` (the created_at / updated_at columns
     from TimestampMixin). The DATABASE computes these during the INSERT. The ORM
     object doesn't know the value until you read it back — so you must
     `await session.refresh(obj)` before asserting on created_at / updated_at.
     Assert-before-refresh is the classic trap here; that's why it's called out.

Runs against the real test DB via the `session` fixture (conftest.py). These are
happy-path tests: nothing should raise. You insert a MINIMAL row (only the
required fields), flush, and check what the layer below filled in for you.

--------------------------------------------------------------------------------
IMPORTS YOU'LL LIKELY NEED (write them yourself):
    from datetime import datetime, timezone
    from app.models.enums import Sport
    from app.models.venue import Venue
    from app.models.team import Team
    from app.models.game import Game

Minimal valid rows (only the nullable=False columns; everything else defaults):
    Venue(name=..., city=..., sport=Sport.MLB)
    Team(external_id=..., sport=Sport.MLB, name=..., abbreviation=..., city=...)
    Game(sport=Sport.MLB, home_team_id=..., away_team_id=...,
         scheduled_at=datetime.now(timezone.utc))
      -> Game needs two DISTINCT teams (home + away), so create two Team rows first.
--------------------------------------------------------------------------------
"""


# TEST 1 — Python-side defaults populate on a minimal Venue.
async def test_venue_defaults_are_applied(session):
    # ARRANGE: create a Venue with ONLY name/city/sport (leave country, timezone,
    #          is_active unset). Add it, `await session.flush()`.
    # ASSERT the defaults landed:
    #     assert venue.country == "USA"
    #     assert venue.timezone == "America/New_York"
    #     assert venue.is_active is True
    ...


# TEST 2 — Game gets its scoreboard/status defaults without you setting them.
async def test_game_scoreboard_defaults(session):
    # ARRANGE: two Teams (distinct external_id / name / abbreviation) + flush for their ids.
    #          Then a minimal Game(home_team_id=..., away_team_id=..., sport, scheduled_at).
    #          Add + flush.
    # ASSERT:
    #     assert game.status == "scheduled"
    #     assert game.home_score == 0
    #     assert game.away_score == 0
    #     assert game.is_postseason is False
    ...


# TEST 3 — server-side timestamps are set by the DB (the refresh trap).
#
# created_at / updated_at come from `server_default=func.now()`, so they're computed
# DURING the insert, not by Python. The ORM object won't show them until you pull the
# row back with refresh.
async def test_timestamps_are_server_generated(session):
    # ARRANGE: create any minimal row that uses TimestampMixin — a Venue is easiest.
    #          Add + `await session.flush()`.
    # ACT: `await session.refresh(venue)`   # <-- without this, created_at reads as None
    # ASSERT:
    #     assert venue.created_at is not None
    #     assert venue.updated_at is not None
    #
    # STRETCH (optional): grab created_at, then change a field (venue.city = "Denver"),
    # flush + refresh, and assert updated_at moved while created_at stayed put.
    # (updated_at uses onupdate=func.now(); created_at does not.)
    ...
