"""Prediction service: query and persistence logic for predictions.

Provides the data-access functions the ``/predictions`` API routes delegate to,
plus a bulk-insert helper used by the offline ML pipeline to write a batch of
predictions.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.prediction import Prediction
from app.schemas.prediction import PredictionCreate

async def get_predictions_for_game(db: AsyncSession, game_id: int) -> list[Prediction]:
    """Fetch all predictions for a game, newest first.

    Args:
        db: Active async database session.
        game_id: Primary key of the game whose predictions are requested.

    Returns:
        list[Prediction]: Predictions for the game ordered by generation time
        descending (possibly empty).
    """
    result = await db.execute(
        select(Prediction).where(Prediction.game_id == game_id).order_by(Prediction.generated_at.desc())
    )
    return list(result.scalars().all())

async def create_predictions(db: AsyncSession, predictions: list[PredictionCreate]) -> list[Prediction]:
    """Bulk-insert a batch of predictions.

    Flushes (not commits) so generated primary keys are populated while leaving
    the final commit to the caller's session/transaction.

    Args:
        db: Active async database session.
        predictions: Validated payloads describing the predictions to create.

    Returns:
        list[Prediction]: The newly created ORM instances.
    """
    db_predictions = [Prediction(**p.model_dump()) for p in predictions]
    db.add_all(db_predictions)
    await db.flush()
    return db_predictions
