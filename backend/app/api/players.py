"""Player REST endpoints.

Exposes CRUD-style HTTP routes for players under the ``/players`` prefix.
Handlers delegate to :mod:`app.services.player_service` and rely on the
player Pydantic schemas for request validation and response serialization.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.player import PlayerCreate, PlayerResponse
from app.services import player_service

router = APIRouter(prefix="/players", tags=["players"])

@router.get("/", response_model=list[PlayerResponse])
async def list_players(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    """List players with pagination.

    Args:
        skip: Number of records to skip (offset) for pagination.
        limit: Maximum number of records to return.
        db: Injected async database session.

    Returns:
        list[Player]: The requested page of players.
    """
    return await player_service.get_players(db, skip=skip, limit=limit)

@router.get("/{player_id}", response_model=PlayerResponse)
async def get_player(player_id: int, db: AsyncSession = Depends(get_db)):
    """Fetch a single player by primary key.

    Args:
        player_id: Primary key of the player to retrieve.
        db: Injected async database session.

    Returns:
        Player: The requested player.

    Raises:
        HTTPException: 404 if no player with ``player_id`` exists.
    """
    player = await player_service.get_player(db, player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return player

@router.post("/", response_model=PlayerResponse, status_code=201)
async def create_player(player: PlayerCreate, db: AsyncSession = Depends(get_db)):
    """Create a new player.

    Args:
        player: Validated payload describing the player to create.
        db: Injected async database session.

    Returns:
        Player: The newly persisted player, including its generated primary key.
    """
    return await player_service.create_player(db, player)
