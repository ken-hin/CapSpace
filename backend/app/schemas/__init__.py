"""Pydantic schemas package.

Aggregates and re-exports the request/response models used by the API layer for
validation and serialization. Each domain (team, player, game, prediction)
defines a ``*Base`` of shared fields, a ``*Create`` input schema, and a
``*Response`` output schema.
"""

from app.schemas.team import TeamCreate, TeamResponse
from app.schemas.player import PlayerCreate, PlayerResponse
from app.schemas.game import GameCreate, GameResponse
from app.schemas.prediction import PredictionCreate, PredictionResponse

# Public schema names re-exported by this package.
__all__ = [
    "TeamCreate", "TeamResponse", "PlayerCreate", "PlayerResponse",
    "GameCreate", "GameResponse", "PredictionCreate", "PredictionResponse",
]
