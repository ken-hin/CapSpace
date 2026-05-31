"""
MlbPlayerProfile — 1:1 extension of the sport-agnostic Player model.

Stores MLB-specific player identifiers (cross-reference IDs for Baseball
Reference, FanGraphs, Retrosheet) and MLB service-time data. This enables
joining data from Statcast, FanGraphs, and historical sources without
polluting the core Player table.
"""

from sqlalchemy import Integer, String, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class MlbPlayerProfile(Base, TimestampMixin):
    """MLB-specific ID crosswalks and player metadata (1:1 with players)."""

    __tablename__ = "mlb_player_profiles"

    # Primary key is also the FK — enforces 1:1
    player_id: Mapped[int] = mapped_column(
        ForeignKey("players.id", ondelete="CASCADE"),
        primary_key=True,
    )

    # The canonical MLBAM player ID (same value stored in Player.external_id
    # for MLB players, but explicit here for clarity and direct lookups)
    mlb_player_id: Mapped[int] = mapped_column(Integer, unique=True, index=True, nullable=False)

    # Cross-reference identifiers for joining across data sources
    bbref_id: Mapped[str | None] = mapped_column(String(50), index=True)   # Baseball Reference
    fangraphs_id: Mapped[str | None] = mapped_column(String(50), index=True)
    retrosheet_id: Mapped[str | None] = mapped_column(String(50))          # For deep history

    # MLB service time in years (e.g. 5.142 = 5 years, 142 days)
    mlb_service_time: Mapped[float | None] = mapped_column(Float)

    # --- Relationships ---
    player = relationship("Player", lazy="selectin")

    def __repr__(self) -> str:
        """Return a concise debug representation for logging/debugging."""
        return f"<MlbPlayerProfile player_id={self.player_id} mlbam={self.mlb_player_id}>"
