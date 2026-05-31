"""Pydantic schemas for the Game resource.

Defines the request/response contract for the ``/games`` API: a shared base of
common fields, a create-input schema, and a response schema that serializes from
the ORM model.
"""

from datetime import datetime
from pydantic import BaseModel

class GameBase(BaseModel):
    """Fields shared by all game request/response schemas (matchup, schedule, season)."""
    home_team_id: int
    away_team_id: int
    scheduled_at: datetime
    season: str | None = None
    is_postseason: bool = False

class GameCreate(GameBase):
    """Input schema for creating a game; adds the optional provider ``external_id``."""
    external_id: str | None = None

class GameResponse(GameBase):
    """Output schema for a game, including its id and current result/status.

    ``from_attributes`` is enabled so instances can be built directly from the
    SQLAlchemy ORM object.
    """
    id: int
    status: str
    home_score: int
    away_score: int
    model_config = {"from_attributes": True}
