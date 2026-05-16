from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.game import GameCreate, GameResponse
from app.services import game_service

router = APIRouter(prefix="/games", tags=["games"])

@router.get("/", response_model=list[GameResponse])
async def list_games(
    status: str | None = Query(None, description="Filter: scheduled, live, final"),
    skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db),
):
    return await game_service.get_games(db, status=status, skip=skip, limit=limit)

@router.get("/{game_id}", response_model=GameResponse)
async def get_game(game_id: int, db: AsyncSession = Depends(get_db)):
    game = await game_service.get_game(db, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game

@router.post("/", response_model=GameResponse, status_code=201)
async def create_game(game: GameCreate, db: AsyncSession = Depends(get_db)):
    return await game_service.create_game(db, game)
