"""Player service: query and persistence logic for :class:`~app.models.player.Player`.

Provides the data-access functions the ``/players`` API routes delegate to.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.player import Player
from app.schemas.player import PlayerCreate

async def get_players(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[Player]:
    """Fetch a paginated list of players.

    Args:
        db: Active async database session.
        skip: Number of rows to skip (offset) for pagination.
        limit: Maximum number of rows to return.

    Returns:
        list[Player]: The requested page of players.
    """
    result = await db.execute(select(Player).offset(skip).limit(limit))
    return list(result.scalars().all())

async def get_player(db: AsyncSession, player_id: int) -> Player | None:
    """Fetch a single player by primary key.

    Args:
        db: Active async database session.
        player_id: Primary key of the player.

    Returns:
        Player | None: The matching player, or ``None`` if it does not exist.
    """
    result = await db.execute(select(Player).where(Player.id == player_id))
    return result.scalar_one_or_none()

async def create_player(db: AsyncSession, player: PlayerCreate) -> Player:
    """Persist a new player from a validated create schema.

    Flushes (not commits) so the generated primary key is populated; the
    surrounding request-scoped session handles the final commit.

    Args:
        db: Active async database session.
        player: Validated payload describing the player to create.

    Returns:
        Player: The newly created, refreshed ORM instance.
    """
    db_player = Player(**player.model_dump())
    db.add(db_player)
    await db.flush()
    await db.refresh(db_player)
    return db_player
