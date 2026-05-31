"""Prediction REST endpoints.

Read-only HTTP routes (under the ``/predictions`` prefix) for retrieving model
predictions associated with games. Persistence and any model-output logic live
in :mod:`app.services.prediction_service`.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.prediction import PredictionResponse
from app.services import prediction_service

router = APIRouter(prefix="/predictions", tags=["predictions"])

@router.get("/game/{game_id}", response_model=list[PredictionResponse])
async def get_predictions_for_game(game_id: int, db: AsyncSession = Depends(get_db)):
    """Return all predictions generated for a given game.

    Args:
        game_id: Primary key of the game whose predictions are requested.
        db: Injected async database session.

    Returns:
        list[Prediction]: Predictions associated with the game (possibly empty).
    """
    return await prediction_service.get_predictions_for_game(db, game_id)
