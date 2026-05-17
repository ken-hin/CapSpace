# Sport-agnostic core models
# Import order matters: tables with no FKs first, then those that reference them.

# Base + mixins
from app.models.base import Base, TimestampMixin  # noqa: F401

# No-dependency models
from app.models.enums import Sport  # noqa: F401
from app.models.venue import Venue  # noqa: F401
from app.models.model_registry import ModelRegistry  # noqa: F401
from app.models.ingestion_run import IngestionRun  # noqa: F401

# Models that depend on Venue / Team / Player (but Team/Player come next)
from app.models.team import Team  # noqa: F401
from app.models.player import Player  # noqa: F401

# Game depends on Team + Venue
from app.models.game import Game  # noqa: F401

# Prediction depends on Game + ModelRegistry
from app.models.prediction import Prediction  # noqa: F401

# Player-related operational models
from app.models.injury import Injury  # noqa: F401
from app.models.transaction import Transaction  # noqa: F401

# Odds + closing line (depend on Game + Player)
from app.models.book_odds import BookOdds  # noqa: F401
from app.models.closing_line import ClosingLine  # noqa: F401

# Weather (depends on Venue)
from app.models.weather_snapshot import WeatherSnapshot  # noqa: F401

# ML pipeline bridge (depends on Game)
from app.models.feature_snapshot import FeatureSnapshot  # noqa: F401

# Bet tracking (depends on Prediction)
from app.models.bet_record import BetRecord  # noqa: F401

# Generic time-series event log (depends on Game + Player + Team)
from app.models.stat_event import StatEvent  # noqa: F401

__all__ = [
    "Base",
    "TimestampMixin",
    "Sport",
    # Core entities
    "Venue",
    "Team",
    "Player",
    "Game",
    # Prediction system
    "ModelRegistry",
    "Prediction",
    "FeatureSnapshot",
    "BetRecord",
    # Odds
    "BookOdds",
    "ClosingLine",
    # Player status
    "Injury",
    "Transaction",
    # Weather
    "WeatherSnapshot",
    # Operational
    "IngestionRun",
    "StatEvent",
]
