"""Aggregated stats REST endpoints.

Provides read-only HTTP routes (under the ``/stats`` prefix) that compute
on-the-fly aggregations over the raw :class:`~app.models.stat_event.StatEvent`
table. Unlike the other API modules, these handlers query the database directly
with SQLAlchemy aggregate functions rather than going through a service layer,
because the logic is purely a grouped read with no side effects.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.stat_event import StatEvent

router = APIRouter(prefix="/stats", tags=["stats"])

@router.get("/game/{game_id}")
async def get_game_stats(game_id: int, db: AsyncSession = Depends(get_db)):
    """Aggregate stat events for a game, grouped by player and event type.

    Args:
        game_id: Primary key of the game to summarize.
        db: Injected async database session.

    Returns:
        list[dict]: One row per (player, event_type) pair with the event
        ``count`` and summed ``total`` value.
    """
    # Group raw stat events by player + event type, counting occurrences and
    # summing their numeric value (e.g. total bases, total pitches).
    result = await db.execute(
        select(StatEvent.player_id, StatEvent.event_type, func.count(StatEvent.id).label("count"), func.sum(StatEvent.value).label("total"))
        .where(StatEvent.game_id == game_id).group_by(StatEvent.player_id, StatEvent.event_type)
    )
    return [{"player_id": r.player_id, "event_type": r.event_type, "count": r.count, "total": float(r.total)} for r in result.all()]

@router.get("/player/{player_id}")
async def get_player_stats(player_id: int, season: str | None = Query(None), db: AsyncSession = Depends(get_db)):
    """Aggregate a single player's stat events across all games, by event type.

    Args:
        player_id: Primary key of the player to summarize.
        season: Optional season filter (currently accepted but not yet applied
            to the query).
        db: Injected async database session.

    Returns:
        list[dict]: One row per event type with ``count``, summed ``total``, and
        rounded ``average`` value for that event type.
    """
    # Aggregate the player's events by type, returning count, sum and mean value.
    result = await db.execute(
        select(StatEvent.event_type, func.count(StatEvent.id).label("count"), func.sum(StatEvent.value).label("total"), func.avg(StatEvent.value).label("average"))
        .where(StatEvent.player_id == player_id).group_by(StatEvent.event_type)
    )
    return [{"event_type": r.event_type, "count": r.count, "total": float(r.total), "average": round(float(r.average), 2)} for r in result.all()]
