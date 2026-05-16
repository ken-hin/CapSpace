from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.player import Player
from app.schemas.player import PlayerCreate

async def get_players(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[Player]:
    result = await db.execute(select(Player).offset(skip).limit(limit))
    return list(result.scalars().all())

async def get_player(db: AsyncSession, player_id: int) -> Player | None:
    result = await db.execute(select(Player).where(Player.id == player_id))
    return result.scalar_one_or_none()

async def create_player(db: AsyncSession, player: PlayerCreate) -> Player:
    db_player = Player(**player.model_dump())
    db.add(db_player)
    await db.flush()
    await db.refresh(db_player)
    return db_player
