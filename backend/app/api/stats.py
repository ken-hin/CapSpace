from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.stat_event import StatEvent

router = APIRouter(prefix="/stats", tags=["stats"])

@router.get("/game/{game_id}")
async def get_game_stats(game_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(StatEvent.player_id, StatEvent.event_type, func.count(StatEvent.id).label("count"), func.sum(StatEvent.value).label("total"))
        .where(StatEvent.game_id == game_id).group_by(StatEvent.player_id, StatEvent.event_type)
    )
    return [{"player_id": r.player_id, "event_type": r.event_type, "count": r.count, "total": float(r.total)} for r in result.all()]

@router.get("/player/{player_id}")
async def get_player_stats(player_id: int, season: str | None = Query(None), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(StatEvent.event_type, func.count(StatEvent.id).label("count"), func.sum(StatEvent.value).label("total"), func.avg(StatEvent.value).label("average"))
        .where(StatEvent.player_id == player_id).group_by(StatEvent.event_type)
    )
    return [{"event_type": r.event_type, "count": r.count, "total": float(r.total), "average": round(float(r.average), 2)} for r in result.all()]
