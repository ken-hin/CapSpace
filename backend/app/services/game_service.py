from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.game import Game
from app.schemas.game import GameCreate

async def get_games(db: AsyncSession, status: str | None = None, skip: int = 0, limit: int = 100) -> list[Game]:
    query = select(Game)
    if status:
        query = query.where(Game.status == status)
    query = query.order_by(Game.scheduled_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())

async def get_game(db: AsyncSession, game_id: int) -> Game | None:
    result = await db.execute(select(Game).where(Game.id == game_id))
    return result.scalar_one_or_none()

async def create_game(db: AsyncSession, game: GameCreate) -> Game:
    db_game = Game(**game.model_dump())
    db.add(db_game)
    await db.flush()
    await db.refresh(db_game)
    return db_game
