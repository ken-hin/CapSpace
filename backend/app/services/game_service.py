"""Game service: query and persistence logic for :class:`~app.models.game.Game`.

Provides the data-access functions the ``/games`` API routes delegate to,
keeping SQLAlchemy queries out of the HTTP layer.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.game import Game
from app.schemas.game import GameCreate

async def get_games(db: AsyncSession, status: str | None = None, skip: int = 0, limit: int = 100) -> list[Game]:
    """Fetch a paginated list of games, optionally filtered by status.

    Args:
        db: Active async database session.
        status: Optional status to filter on (e.g. ``scheduled``, ``live``, ``final``).
        skip: Number of rows to skip (offset) for pagination.
        limit: Maximum number of rows to return.

    Returns:
        list[Game]: Matching games ordered by scheduled time, most recent first.
    """
    query = select(Game)
    if status:
        query = query.where(Game.status == status)
    query = query.order_by(Game.scheduled_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())

async def get_game(db: AsyncSession, game_id: int) -> Game | None:
    """Fetch a single game by primary key.

    Args:
        db: Active async database session.
        game_id: Primary key of the game.

    Returns:
        Game | None: The matching game, or ``None`` if it does not exist.
    """
    result = await db.execute(select(Game).where(Game.id == game_id))
    return result.scalar_one_or_none()

async def create_game(db: AsyncSession, game: GameCreate) -> Game:
    """Persist a new game from a validated create schema.

    Flushes (not commits) so the generated primary key is populated; the
    surrounding request-scoped session is responsible for the final commit.

    Args:
        db: Active async database session.
        game: Validated payload describing the game to create.

    Returns:
        Game: The newly created, refreshed ORM instance.
    """
    db_game = Game(**game.model_dump())
    db.add(db_game)
    await db.flush()
    await db.refresh(db_game)
    return db_game
