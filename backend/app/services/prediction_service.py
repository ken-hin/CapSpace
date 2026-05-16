from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.prediction import Prediction
from app.schemas.prediction import PredictionCreate

async def get_predictions_for_game(db: AsyncSession, game_id: int) -> list[Prediction]:
    result = await db.execute(
        select(Prediction).where(Prediction.game_id == game_id).order_by(Prediction.generated_at.desc())
    )
    return list(result.scalars().all())

async def create_predictions(db: AsyncSession, predictions: list[PredictionCreate]) -> list[Prediction]:
    db_predictions = [Prediction(**p.model_dump()) for p in predictions]
    db.add_all(db_predictions)
    await db.flush()
    return db_predictions
