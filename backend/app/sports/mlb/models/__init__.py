"""
MLB-specific models package.

Re-exports all MLB models so Alembic autogenerate discovers them when
this package is imported in alembic/env.py's metadata target.

Import order: tables with no inter-MLB FKs first, then those that reference them.
All MLB models reference the sport-agnostic core (Game, Player, Team, Venue)
which must already be imported before these.
"""

# 1:1 extensions of core models
from app.sports.mlb.models.mlb_game_details import MlbGameDetails  # noqa: F401
from app.sports.mlb.models.mlb_player_profile import MlbPlayerProfile  # noqa: F401

# Venue-dependent
from app.sports.mlb.models.park_factor import ParkFactor  # noqa: F401
from app.sports.mlb.models.park_dimensions import ParkDimensions  # noqa: F401

# Game-dependent
from app.sports.mlb.models.game_lineup import GameLineup  # noqa: F401
from app.sports.mlb.models.pitch_event import PitchEvent  # noqa: F401
from app.sports.mlb.models.at_bat import AtBat  # noqa: F401
from app.sports.mlb.models.bullpen_availability import BullpenAvailability  # noqa: F401

# Player-dependent aggregates
from app.sports.mlb.models.player_season_stats import MlbPlayerSeasonStats  # noqa: F401
from app.sports.mlb.models.player_split_stats import MlbPlayerSplitStats  # noqa: F401
from app.sports.mlb.models.pitcher_arsenal import PitcherArsenal  # noqa: F401
from app.sports.mlb.models.batter_vs_pitcher import BatterVsPitcher  # noqa: F401

# Team-dependent
from app.sports.mlb.models.standings import MlbStandings  # noqa: F401

__all__ = [
    # 1:1 extensions
    "MlbGameDetails",
    "MlbPlayerProfile",
    # Venue
    "ParkFactor",
    "ParkDimensions",
    # Game-level
    "GameLineup",
    "PitchEvent",
    "AtBat",
    "BullpenAvailability",
    # Player aggregates
    "MlbPlayerSeasonStats",
    "MlbPlayerSplitStats",
    "PitcherArsenal",
    "BatterVsPitcher",
    # Team
    "MlbStandings",
]
