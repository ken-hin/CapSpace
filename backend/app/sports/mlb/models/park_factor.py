"""
ParkFactor — Statcast park-factor indices for MLB venues, per rolling window.

Baseball Savant publishes park factors over a *rolling window* (typically the
trailing 3 seasons) rather than a single year, which smooths the small-sample
noise of ~81 home games per season. Each row is therefore keyed by
``(venue, season, window_years)`` where ``season`` is the **end year** of the
window and ``window_years`` its length — e.g. ``season=2026, window_years=3``
means the 2024–2026 window. Storing the window length lets a stable 3-year
figure and a reactive 1-year figure (for a park that just changed, or a brand
new venue with no 3-year history) coexist without colliding.

Physical outfield dimensions live in a separate
:class:`~app.sports.mlb.models.park_dimensions.ParkDimensions` table — they come
from a different source and change on a different cadence than these indices.
"""

from datetime import datetime

from sqlalchemy import (
    Integer, Float, String, ForeignKey, UniqueConstraint, CheckConstraint,
    DateTime, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ParkFactor(Base):
    """MLB Statcast park factors per venue, per rolling window.

    Factors are on the standard ``100 = league average`` scale. Values are
    nullable with no neutral default so an unseeded park reads as ``NULL``
    (unknown) rather than masquerading as a perfectly average ``100``; the
    feature layer can coalesce to 100 at read time when that is the desired
    behaviour. The unique constraint enforces one row per
    ``(venue, season, window_years)``.

    Attributes:
        id: Surrogate primary key.
        venue_id: FK to the :class:`~app.models.venue.Venue`.
        season: End year of the rolling window these factors apply to.
        window_years: Length of the rolling window in seasons (Savant default 3).
        factor_overall: Headline Savant park-factor index (wOBAcon-based composite).
        factor_runs: Runs park factor (Savant ``R`` column).
        factor_hr_vs_l: Home-run factor vs left-handed batters.
        factor_hr_vs_r: Home-run factor vs right-handed batters.
        factor_hits: Hits park factor.
        factor_xwobacon: Expected wOBA-on-contact factor (more stable than raw).
        factor_obp: On-base-percentage park factor.
        factor_hardhit: Hard-hit-rate park factor.
        factor_bb: Walk park factor.
        factor_so: Strikeout park factor.
        pa: Plate appearances in the window (sample size, for confidence weighting).
        source: Data provenance (``"baseball_savant"`` | ``"computed"``).
        updated_at: Last refresh timestamp (server default ``now()``).
        venue: Eager-loaded :class:`~app.models.venue.Venue` relationship.
    """

    __tablename__ = "park_factors"
    __table_args__ = (
        UniqueConstraint(
            "venue_id", "season", "window_years",
            name="uq_park_factors_venue_season_window",
        ),
        CheckConstraint(
            "source IN ('baseball_savant', 'computed')",
            name="ck_park_factors_source",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    venue_id: Mapped[int] = mapped_column(ForeignKey("venues.id"), nullable=False)
    season: Mapped[int] = mapped_column(Integer, nullable=False)
    window_years: Mapped[int] = mapped_column(Integer, nullable=False, default=3)

    # --- Park factors (100 = league average; NULL = unknown/unseeded) ---
    # Headline Savant composite index (wOBAcon-based) — distinct from runs.
    factor_overall: Mapped[float | None] = mapped_column(Float)
    # Runs factor — Savant 'R' column.
    factor_runs: Mapped[float | None] = mapped_column(Float)

    # HR factors split by batter handedness (separate Savant L/R pulls;
    # critical for matchup modeling).
    factor_hr_vs_l: Mapped[float | None] = mapped_column(Float)
    factor_hr_vs_r: Mapped[float | None] = mapped_column(Float)

    # Contact / hit quality
    factor_hits: Mapped[float | None] = mapped_column(Float)
    factor_xwobacon: Mapped[float | None] = mapped_column(Float)
    factor_obp: Mapped[float | None] = mapped_column(Float)
    factor_hardhit: Mapped[float | None] = mapped_column(Float)

    # Plate discipline
    factor_bb: Mapped[float | None] = mapped_column(Float)
    factor_so: Mapped[float | None] = mapped_column(Float)

    # Sample size backing the window (Savant 'PA' column).
    pa: Mapped[int | None] = mapped_column(Integer)

    # Data provenance — constrained by ck_park_factors_source above.
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="baseball_savant")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # --- Relationships ---
    venue = relationship("Venue", lazy="selectin")

    def __repr__(self) -> str:
        """Return a concise debug representation for logging/debugging."""
        return (
            f"<ParkFactor venue_id={self.venue_id} season={self.season} "
            f"window={self.window_years}y overall={self.factor_overall}>"
        )
