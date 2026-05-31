"""Game REST endpoints.

Exposes CRUD-style HTTP routes for games under the ``/games`` prefix. The
handlers are thin: they validate/parse input via Pydantic schemas, delegate all
business logic and persistence to :mod:`app.services.game_service`, and return
ORM objects that FastAPI serializes through the response models.
"""

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
    """List games, optionally filtered by status, with pagination.

    Args:
        status: Optional status filter (e.g. ``scheduled``, ``live``, ``final``).
        skip: Number of records to skip (offset) for pagination.
        limit: Maximum number of records to return.
        db: Injected async database session.

    Returns:
        list[Game]: Matching games ordered by the service layer (most recent first).
    """
    return await game_service.get_games(db, status=status, skip=skip, limit=limit)

@router.get("/{game_id}", response_model=GameResponse)
async def get_game(game_id: int, db: AsyncSession = Depends(get_db)):
    """Fetch a single game by its primary key.

    Args:
        game_id: Primary key of the game to retrieve.
        db: Injected async database session.

    Returns:
        Game: The requested game.

    Raises:
        HTTPException: 404 if no game with ``game_id`` exists.
    """
    game = await game_service.get_game(db, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game

@router.post("/", response_model=GameResponse, status_code=201)
async def create_game(game: GameCreate, db: AsyncSession = Depends(get_db)):
    """Create a new game.

    Args:
        game: Validated payload describing the game to create.
        db: Injected async database session.

    Returns:
        Game: The newly persisted game, including its generated primary key.
    """
    return await game_service.create_game(db, game)
