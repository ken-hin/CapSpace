from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.prediction import PredictionResponse
from app.services import prediction_service

router = APIRouter(prefix="/predictions", tags=["predictions"])

@router.get("/game/{game_id}", response_model=list[PredictionResponse])
async def get_predictions_for_game(game_id: int, db: AsyncSession = Depends(get_db)):
    return await prediction_service.get_predictions_for_game(db, game_id)
