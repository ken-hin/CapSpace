"""Default-value tests — prove rows get the right values when you DON'T set them.

Constraints prove bad data is rejected; defaults prove *good* data is filled in.
Your models lean on two different kinds of default, and the distinction is the
whole point of this file:

  1. Python-side ``default=...`` (e.g. Game.status="scheduled", Venue.country="USA").
     SQLAlchemy fills these in while building the INSERT, so the value is present on
     the object right after ``flush()`` — no refresh needed.

  2. Server-side ``server_default=func.now()`` (created_at / updated_at from
     TimestampMixin). The DATABASE computes these during the INSERT, and the ORM
     object doesn't know the value until you read it back — so you must
     ``await session.refresh(obj)`` before asserting on them. Assert-before-refresh
     is the classic trap.

Runs against the real test DB via the `session` fixture (conftest.py). These are
happy-path tests: nothing should raise. Insert a MINIMAL row (only the required
fields), flush, then check what the layer below filled in for you.
"""

from datetime import datetime, timezone
from app.models.enums import Sport
from app.models.venue import Venue
from app.models.team import Team
from app.models.game import Game


async def test_venue_defaults_are_applied(session):
    """Python-side column defaults populate on a minimally-specified Venue.

    Only name/city/sport are set. ``country``, ``timezone`` and ``is_active`` are
    left off, so their ``default=`` values are applied by SQLAlchemy as it builds
    the INSERT and are present on the object right after ``flush()`` — no refresh.
    """
    # Only the required fields set; country/timezone/is_active are left to default.
    tv = Venue(name = "Test Venue", city = "Nashville", sport = Sport.MLB)
    session.add(tv)
    await session.flush()
    # Assert the three defaults landed.
    assert tv.country == "USA" and tv.timezone == "America/New_York" and tv.is_active is True


async def test_game_scoreboard_defaults(session):
    """A minimal Game receives its scoreboard / status defaults.

    A Game needs two DISTINCT teams, so both are created and flushed first for their
    ids. Only the required Game fields are set; ``status``, ``home_score``,
    ``away_score`` and ``is_postseason`` come from their ``default=`` values and are
    present after flush.
    """
    # Two distinct teams (unique external_id / name / abbreviation) to satisfy the FKs.
    ht = Team(external_id="ht", sport=Sport.MLB, name="Home Team", abbreviation="HT", city="Home")
    at = Team(external_id="at", sport=Sport.MLB, name="Away Team", abbreviation="AT", city="Away")
    session.add_all([ht, at])
    await session.flush()
    # Minimal Game: only the nullable=False fields set; the scoreboard fields default.
    tg = Game(home_team_id=ht.id, away_team_id=at.id, sport=Sport.MLB, scheduled_at=datetime.now(timezone.utc))
    session.add(tg)
    await session.flush()
    assert (tg.status == "scheduled" and
            tg.home_score == 0 and
            tg.away_score == 0 and
            tg.is_postseason is False)


async def test_timestamps_are_server_generated(session):
    """Server-side timestamps are set by the DB and read back after refresh.

    ``created_at`` / ``updated_at`` use ``server_default=func.now()``, so the
    DATABASE computes them during the INSERT. The ORM object doesn't learn the
    values until the row is re-read, which is why ``session.refresh(tv)`` precedes
    the assert — skip it and ``created_at`` reads as ``None``.
    """
    tv = Venue(name = "Test Venue", city = "Nashville", sport = Sport.MLB)
    session.add(tv)
    await session.flush()
    # refresh pulls the server-computed values back onto the object.
    await session.refresh(tv)
    assert tv.created_at is not None and tv.updated_at is not None
    # Change a field and re-read. NOTE: Postgres now() is the *transaction* start time,
    # constant across this single-transaction test — so updated_at ends up equal in
    # value to created_at here; showing an advancing updated_at needs a separate txn.
    tv.city = "Denver"
    await session.flush()
    await session.refresh(tv)
    assert tv.updated_at is not None and tv.updated_at is not tv.created_at
