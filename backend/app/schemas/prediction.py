from datetime import datetime
from pydantic import BaseModel

class PredictionBase(BaseModel):
    game_id: int
    prediction_type: str
    predicted_value: float
    confidence: float | None = None
    model_version: str

class PredictionCreate(PredictionBase):
    features_used: dict | None = None

class PredictionResponse(PredictionBase):
    id: int
    generated_at: datetime
    model_config = {"from_attributes": True}
