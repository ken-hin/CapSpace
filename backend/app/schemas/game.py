from datetime import datetime
from pydantic import BaseModel

class GameBase(BaseModel):
    home_team_id: int
    away_team_id: int
    scheduled_at: datetime
    season: str | None = None
    is_postseason: bool = False

class GameCreate(GameBase):
    external_id: str | None = None

class GameResponse(GameBase):
    id: int
    status: str
    home_score: int
    away_score: int
    model_config = {"from_attributes": True}
