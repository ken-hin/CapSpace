"""Relationship tests — prove the Game ↔ MlbGameDetails wiring behaves at the DB level.

Declaring a relationship in Python isn't the same as it working in Postgres. These
tests exercise the 1:1 extension between ``Game`` and its ``MlbGameDetails`` row —
keyed on ``game_id``, which is both the PK and a FK to ``games.id`` with
``ondelete="CASCADE"``:

  1. deleting a Game cascades the delete to its details row,
  2. the relationship is navigable in both directions, and
  3. it is truly 1:1 — a second details row for the same game is rejected.

Runs against the real test DB via the `session` fixture (conftest.py), which rolls
back after each test.
"""

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timezone

from app.models import Team
from app.models.game import Game
from app.sports.mlb.models.mlb_game_details import MlbGameDetails
from app.models.enums import Sport


async def test_deleting_game_cascades_to_details(session):
    """Deleting a Game cascades the delete to its MlbGameDetails row.

    ``MlbGameDetails.game_id`` is the PK *and* a FK to ``games.id`` with
    ``ondelete="CASCADE"``, and ``Game.mlb_details`` is configured with
    ``cascade="all, delete-orphan", passive_deletes=True`` — so removing the parent
    removes the child. After deleting the game and flushing, a query for the details
    row comes back empty.
    """
    # Two distinct teams (unique external_id / name / abbreviation) to satisfy the FKs.
    ht = Team(external_id="ht", sport=Sport.MLB, name="Home Team", abbreviation="HT", city="Home")
    at = Team(external_id="at", sport=Sport.MLB, name="Away Team", abbreviation="AT", city="Away")
    session.add_all([ht, at])
    await session.flush()

    # Minimal Game: only the nullable=False fields set.
    game = Game(sport=Sport.MLB, home_team=ht, away_team=at, scheduled_at=datetime.now(timezone.utc))
    session.add(game)
    await session.flush()

    # Attach the details via the relationship (game=game) so the 1:1 link is wired.
    game_details = MlbGameDetails(game=game, mlb_game_pk=1)
    session.add(game_details)
    await session.flush()

    # Delete the parent game; the cascade should take its details row with it.
    await session.delete(game)
    await session.flush()

    # The details row should be gone — the query returns nothing.
    result = await session.execute(
            select(MlbGameDetails).where(MlbGameDetails.game == game)
    )
    assert result.scalar_one_or_none() is None


async def test_game_details_relationship_navigation(session):
    """The 1:1 relationship is navigable in both directions.

    Building the details row with ``game=game`` wires both sides in memory via
    ``back_populates``, so no reload is needed: from the game you reach its details
    (``game.mlb_details``) and from the details you reach the game (``details.game``).
    Both resolve to the very same in-memory objects, so ``is`` holds.
    """
    # Two distinct teams (unique external_id / name / abbreviation) to satisfy the FKs.
    ht = Team(external_id="ht", sport=Sport.MLB, name="Home Team", abbreviation="HT", city="Home")
    at = Team(external_id="at", sport=Sport.MLB, name="Away Team", abbreviation="AT", city="Away")
    session.add_all([ht, at])
    await session.flush()

    # A game plus its details, linked via the relationship.
    game = Game(sport=Sport.MLB, home_team=ht, away_team=at, scheduled_at=datetime.now(timezone.utc))
    session.add(game)
    await session.flush()

    game_details = MlbGameDetails(game=game, mlb_game_pk=1)
    session.add(game_details)
    await session.flush()
    assert game.mlb_details is game_details  # game  -> details
    assert game_details.game is game         # details -> game


async def test_second_details_for_same_game_is_rejected(session):
    """A second MlbGameDetails for the same game is rejected — proving it's 1:1.

    ``game_id`` is the primary key of ``mlb_game_details``, so only one details row
    can exist per game. The two rows here set ``game_id`` *directly* (rather than the
    ``game`` relationship) on purpose: assigning the relationship twice would simply
    reassign the 1:1 slot and orphan-delete the first row, so no duplicate would ever
    reach the database. Setting the FK directly makes both rows collide on the PK, and
    the second flush raises ``IntegrityError``.
    """
    # Teams + parent game.
    ht = Team(external_id="ht", sport=Sport.MLB, name="Home Team", abbreviation="HT", city="Home")
    at = Team(external_id="at", sport=Sport.MLB, name="Away Team", abbreviation="AT", city="Away")
    session.add_all([ht, at])
    await session.flush()

    game = Game(sport=Sport.MLB, home_team=ht, away_team=at, scheduled_at=datetime.now(timezone.utc))
    session.add(game)
    await session.flush()

    # First details — FK set directly (not via game=) so the 1:1 relationship
    # doesn't swap/orphan it when the second row is added.
    game_details = MlbGameDetails(game_id=game.id, mlb_game_pk=1)
    session.add(game_details)
    await session.flush()

    # Second details on the SAME game_id -> duplicate primary key on flush.
    dup_game_details = MlbGameDetails(game_id=game.id, mlb_game_pk=2)
    session.add(dup_game_details)
    with pytest.raises(IntegrityError):
        await session.flush()
