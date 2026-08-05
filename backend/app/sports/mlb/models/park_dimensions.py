"""
ParkDimensions — Physical outfield configuration for MLB venues, per season.

Fence distances and wall heights are a slowly-changing physical property of a
ballpark, distinct from the statistical park factors in
:class:`~app.sports.mlb.models.park_factor.ParkFactor`. They come from a
different source (stadium dimension references, not the Savant park-factor
leaderboard) and only change when a park is physically altered — e.g. the
Orioles moving the left-field wall. Keying by ``(venue, season)`` captures
those mid-career changes while still joining cleanly to ParkFactor on
``(venue_id, season)``.

Distances are stored as feet. The down-the-line distances (``*_distance_ft``)
are populated first; the power-alley / gap distances (``*_gap_distance_ft``)
are optional and can be backfilled later.
"""

from sqlalchemy import Integer, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class ParkDimensions(Base, TimestampMixin):
    """Physical outfield dimensions for an MLB venue in a given season.

    Stored as ``Float`` feet because wall heights and gap distances are not
    always whole numbers. All dimension fields are nullable so a row can be
    created with whatever subset is known. The unique constraint enforces one
    row per ``(venue, season)``.

    Attributes:
        id: Surrogate primary key.
        venue_id: FK to the :class:`~app.models.venue.Venue`.
        season: Season this physical configuration applies to.
        lf_distance_ft: Left-field foul-line distance, in feet.
        cf_distance_ft: Center-field distance, in feet.
        rf_distance_ft: Right-field foul-line distance, in feet.
        lf_gap_distance_ft: Left-center power-alley (gap) distance, in feet.
        rf_gap_distance_ft: Right-center power-alley (gap) distance, in feet.
        lf_wall_height_ft: Left-field wall height, in feet.
        cf_wall_height_ft: Center-field wall height, in feet.
        rf_wall_height_ft: Right-field wall height, in feet.
        created_at: Row creation timestamp (from :class:`TimestampMixin`).
        updated_at: Last update timestamp (from :class:`TimestampMixin`).
        venue: Eager-loaded :class:`~app.models.venue.Venue` relationship.
    """

    __tablename__ = "park_dimensions"
    __table_args__ = (
        UniqueConstraint("venue_id", "season", name="uq_park_dimensions_venue_season"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    venue_id: Mapped[int] = mapped_column(ForeignKey("venues.id"), nullable=False)
    season: Mapped[int] = mapped_column(Integer, nullable=False)

    # --- Down-the-line distances (populated first) ---
    lf_distance_ft: Mapped[float | None] = mapped_column(Float)
    cf_distance_ft: Mapped[float | None] = mapped_column(Float)
    rf_distance_ft: Mapped[float | None] = mapped_column(Float)

    # --- Power-alley / gap distances (optional, backfill later) ---
    lf_gap_distance_ft: Mapped[float | None] = mapped_column(Float)
    rf_gap_distance_ft: Mapped[float | None] = mapped_column(Float)

    # --- Wall heights ---
    lf_wall_height_ft: Mapped[float | None] = mapped_column(Float)
    cf_wall_height_ft: Mapped[float | None] = mapped_column(Float)
    rf_wall_height_ft: Mapped[float | None] = mapped_column(Float)

    # --- Relationships ---
    venue = relationship("Venue", lazy="selectin")

    def __repr__(self) -> str:
        """Return a concise debug representation for logging/debugging."""
        return (
            f"<ParkDimensions venue_id={self.venue_id} season={self.season} "
            f"lf={self.lf_distance_ft} cf={self.cf_distance_ft} rf={self.rf_distance_ft}>"
        )
