from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.player import PlayerCreate, PlayerResponse
from app.services import player_service

router = APIRouter(prefix="/players", tags=["players"])

@router.get("/", response_model=list[PlayerResponse])
async def list_players(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await player_service.get_players(db, skip=skip, limit=limit)

@router.get("/{player_id}", response_model=PlayerResponse)
async def get_player(player_id: int, db: AsyncSession = Depends(get_db)):
    player = await player_service.get_player(db, player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return player

@router.post("/", response_model=PlayerResponse, status_code=201)
async def create_player(player: PlayerCreate, db: AsyncSession = Depends(get_db)):
    return await player_service.create_player(db, player)
