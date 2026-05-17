"""
MlbGameDetails — 1:1 extension of the sport-agnostic Game model.

Holds MLB-only game-level fields such as game type, starting/winning/losing
pitchers, runs by inning, and doubleheader metadata. Keyed on game_id so
cross-sport queries on the base Game table stay clean without nullable
MLB-specific columns polluting it.
"""

from sqlalchemy import Integer, String, Boolean, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class MlbGameDetails(Base, TimestampMixin):
    """MLB-specific extension of the games table (1:1 relationship)."""

    __tablename__ = "mlb_game_details"

    # Primary key is also the FK back to games — enforces 1:1 cardinality
    game_id: Mapped[int] = mapped_column(
        ForeignKey("games.id", ondelete="CASCADE"),
        primary_key=True,
    )

    # Official MLBAM gamePk — the canonical identifier across MLB systems
    mlb_game_pk: Mapped[int] = mapped_column(Integer, unique=True, index=True, nullable=False)

    # Game type code:
    # 'R' = Regular, 'P' = Postseason, 'F' = Final, 'D' = Division Series,
    # 'L' = League Championship, 'W' = World Series, 'S' = Spring Training
    game_type: Mapped[str] = mapped_column(String(5), nullable=False, default="R")

    # Starting pitchers (nullable for TBD / postponed games)
    home_starter_id: Mapped[int | None] = mapped_column(ForeignKey("players.id"))
    away_starter_id: Mapped[int | None] = mapped_column(ForeignKey("players.id"))

    # Decision pitchers (populated post-game)
    winning_pitcher_id: Mapped[int | None] = mapped_column(ForeignKey("players.id"))
    losing_pitcher_id: Mapped[int | None] = mapped_column(ForeignKey("players.id"))
    save_pitcher_id: Mapped[int | None] = mapped_column(ForeignKey("players.id"))

    # Extra-inning games (standard is 9)
    total_innings: Mapped[int | None] = mapped_column(Integer)

    # Linescore: runs scored per inning stored as JSON arrays
    # e.g. [0, 1, 0, 3, 0, 0, 2, 0, 1] for a 9-inning game
    home_runs_by_inning: Mapped[list | None] = mapped_column(JSON)
    away_runs_by_inning: Mapped[list | None] = mapped_column(JSON)

    # Doubleheader metadata
    is_doubleheader: Mapped[bool] = mapped_column(Boolean, default=False)
    doubleheader_game_num: Mapped[int | None] = mapped_column(Integer)  # 1 or 2

    # --- Relationships ---
    game = relationship("Game", lazy="selectin")
    home_starter = relationship("Player", foreign_keys=[home_starter_id], lazy="selectin")
    away_starter = relationship("Player", foreign_keys=[away_starter_id], lazy="selectin")
    winning_pitcher = relationship("Player", foreign_keys=[winning_pitcher_id], lazy="selectin")
    losing_pitcher = relationship("Player", foreign_keys=[losing_pitcher_id], lazy="selectin")
    save_pitcher = relationship("Player", foreign_keys=[save_pitcher_id], lazy="selectin")

    def __repr__(self) -> str:
        return f"<MlbGameDetails game_id={self.game_id} pk={self.mlb_game_pk} type={self.game_type}>"
