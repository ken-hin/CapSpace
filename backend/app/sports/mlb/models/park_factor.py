"""
ParkFactor — Season-level park effects for MLB venues.

Park factors shift year-to-year due to construction changes, humidor
installations, and environmental drift. Keyed by (venue, season) so the
model can look up the correct factor for any historical or current game.

Also stores MLB-specific outfield dimensions that influence batted-ball
outcomes (HR probability varies with fence distance and wall height).
"""

from datetime import datetime

from sqlalchemy import Integer, Float, String, ForeignKey, UniqueConstraint, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ParkFactor(Base):
    """MLB park factor data per venue per season."""

    __tablename__ = "park_factors"
    __table_args__ = (
        UniqueConstraint("venue_id", "season", name="uq_park_factors_venue_season"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    venue_id: Mapped[int] = mapped_column(ForeignKey("venues.id"), nullable=False)
    season: Mapped[int] = mapped_column(Integer, nullable=False)

    # --- Outfield dimensions ---
    lf_distance_ft: Mapped[int | None] = mapped_column(Integer)
    cf_distance_ft: Mapped[int | None] = mapped_column(Integer)
    rf_distance_ft: Mapped[int | None] = mapped_column(Integer)
    lf_wall_height_ft: Mapped[int | None] = mapped_column(Integer)
    rf_wall_height_ft: Mapped[int | None] = mapped_column(Integer)

    # --- Park factors (100 = league average) ---
    # Overall run factor — the most commonly cited single number
    factor_runs: Mapped[float] = mapped_column(Float, nullable=False, default=100.0)

    # HR factors split by batter handedness (critical for matchup modeling)
    factor_hr_vs_l: Mapped[float] = mapped_column(Float, default=100.0)
    factor_hr_vs_r: Mapped[float] = mapped_column(Float, default=100.0)

    # Hit-type factors
    factor_hits: Mapped[float] = mapped_column(Float, default=100.0)
    factor_singles: Mapped[float] = mapped_column(Float, default=100.0)
    factor_doubles: Mapped[float] = mapped_column(Float, default=100.0)
    factor_triples: Mapped[float] = mapped_column(Float, default=100.0)

    # Plate discipline factors
    factor_bb: Mapped[float] = mapped_column(Float, default=100.0)
    factor_so: Mapped[float] = mapped_column(Float, default=100.0)

    # Data provenance
    # 'fangraphs' | 'baseball_savant' | 'computed'
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="fangraphs")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # --- Relationships ---
    venue = relationship("Venue", lazy="selectin")

    def __repr__(self) -> str:
        return f"<ParkFactor venue_id={self.venue_id} season={self.season} runs={self.factor_runs}>"
