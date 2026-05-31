"""Feature engineering for pre-game predictions.

Provides the functions that transform raw game/stat DataFrames into the numeric
features used to train models and to score upcoming games. These are currently
sport-agnostic scaffolding stubs (they return empty results) to be implemented
per sport; the signatures define the intended interface so callers can be wired
up ahead of the implementations.
"""
import pandas as pd

def compute_team_features(games_df: pd.DataFrame, team_id: int, n_games: int = 10) -> dict:
    """Compute rolling team-level features over a team's recent games.

    Args:
        games_df: DataFrame of games to draw history from.
        team_id: Identifier of the team to compute features for.
        n_games: Size of the trailing window (most recent games) to roll over.

    Returns:
        dict: Mapping of feature name to value. Currently empty (stub).

    TODO:
        Implement the sport-specific rolling feature calculations.
    """
    return {}

def compute_player_features(stats_df: pd.DataFrame, player_id: int, n_games: int = 10) -> dict:
    """Compute rolling player-level features over a player's recent games.

    Args:
        stats_df: DataFrame of per-game player stats to draw history from.
        player_id: Identifier of the player to compute features for.
        n_games: Size of the trailing window (most recent games) to roll over.

    Returns:
        dict: Mapping of feature name to value. Currently empty (stub).

    TODO:
        Implement the sport-specific rolling feature calculations.
    """
    return {}

def build_game_feature_matrix(games_df: pd.DataFrame, stats_df: pd.DataFrame) -> pd.DataFrame:
    """Assemble the full per-game feature matrix used for model training.

    Combines team- and player-level features into one row per game (or per
    game/side), producing the design matrix consumed by the training pipeline.

    Args:
        games_df: DataFrame of games to build feature rows for.
        stats_df: DataFrame of player/team stats feeding the feature calculations.

    Returns:
        pd.DataFrame: One row of features per game. Currently empty (stub).

    TODO:
        Implement the sport-specific feature-matrix assembly.
    """
    return pd.DataFrame()
