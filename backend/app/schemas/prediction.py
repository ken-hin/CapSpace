"""Pydantic schemas for the Prediction resource.

Defines the request/response contract for the ``/predictions`` API: a shared
base of common fields, a create-input schema, and a response schema that
serializes from the ORM model.
"""

from datetime import datetime
from pydantic import BaseModel

class PredictionBase(BaseModel):
    """Fields shared by all prediction schemas (target game, type, value, model version)."""
    game_id: int
    prediction_type: str
    predicted_value: float
    confidence: float | None = None
    model_version: str

class PredictionCreate(PredictionBase):
    """Input schema for creating a prediction; adds the optional ``features_used`` payload."""
    features_used: dict | None = None

class PredictionResponse(PredictionBase):
    """Output schema for a prediction, including its id and generation timestamp.

    ``from_attributes`` is enabled so instances can be built directly from the
    SQLAlchemy ORM object.
    """
    id: int
    generated_at: datetime
    model_config = {"from_attributes": True}
