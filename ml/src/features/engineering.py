"""Feature engineering for pre-game predictions. Customize for your sport."""
import pandas as pd

def compute_team_features(games_df: pd.DataFrame, team_id: int, n_games: int = 10) -> dict:
    """Compute rolling features for a team. TODO: implement for your sport."""
    return {}

def compute_player_features(stats_df: pd.DataFrame, player_id: int, n_games: int = 10) -> dict:
    """Compute rolling features for a player. TODO: implement for your sport."""
    return {}

def build_game_feature_matrix(games_df: pd.DataFrame, stats_df: pd.DataFrame) -> pd.DataFrame:
    """Build full feature matrix for model training. TODO: implement for your sport."""
    return pd.DataFrame()
