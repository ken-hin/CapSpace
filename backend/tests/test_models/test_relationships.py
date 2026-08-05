"""Relationship tests — prove the model wiring behaves at the DB level.

Declaring a relationship in Python isn't the same as it working in Postgres.
These tests create linked rows and check that (a) a cascade delete actually
fires, and (b) the 1:1 extension is navigable and truly 1:1.

Uses the `session` fixture from conftest.py against the real test DB.

--------------------------------------------------------------------------------
IMPORTS YOU'LL LIKELY NEED (write them yourself):
    import pytest
    from sqlalchemy import select
    from sqlalchemy.exc import IntegrityError
    from app.models.game import Game
    from app.sports.mlb.models.mlb_game_details import MlbGameDetails

HOMEWORK: open game.py and mlb_game_details.py and note which columns are
nullable=False. To "create a minimal valid Game" you only need to fill those
required fields — leave the rest to their defaults.
--------------------------------------------------------------------------------
"""


# TEST 1 — deleting a Game cascades to its MlbGameDetails.
# Your model: MlbGameDetails.game_id is PK + FK → games.id with ondelete="CASCADE".
async def test_deleting_game_cascades_to_details(session):
    # ARRANGE
    #   1. Create a minimal valid Game. Add + `await session.flush()` to get game.id.
    #   2. Create MlbGameDetails(game_id=game.id, ...required fields...). Add + flush.
    #
    # ACT
    #   3. Delete the game:   await session.delete(game)   then   await session.flush()
    #
    # ASSERT
    #   4. The details row is gone. Query for it and expect None:
    #
    #          result = await session.execute(
    #              select(MlbGameDetails).where(MlbGameDetails.game_id == game.id)
    #          )
    #          assert result.scalar_one_or_none() is None
    ...


# TEST 2 — 1:1 navigation works in both directions.
async def test_game_details_relationship_navigation(session):
    # ARRANGE: create a Game + its MlbGameDetails, flush.
    #   (you may need `await session.refresh(game)` so the relationship loads.)
    # ASSERT:
    #   - from the game you can reach its details   (game.<details-relationship-name>)
    #   - from the details you can reach the game   (details.game)
    #   Check the relationship() names defined in your two models.
    ...


# TEST 3 — it's really 1:1: a second details row for the same game is rejected.
async def test_second_details_for_same_game_is_rejected(session):
    # ARRANGE: Game + MlbGameDetails #1, flush.
    # ACT + ASSERT: MlbGameDetails #2 with the SAME game_id violates the PK/unique →
    #
    #     with pytest.raises(IntegrityError):
    #         await session.flush()
    ...
