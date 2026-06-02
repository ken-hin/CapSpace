"""
PitcherArsenal — Pitch mix per pitcher per season.

Aggregated from Statcast pitch-level data. Shows each pitch type a pitcher
throws, its usage rate, average velocity/spin/movement, and outcome metrics
(whiff rate, chase rate, xwOBA against).

Essential for matchup modeling: a pitcher's slider performance vs LHH
may be the single most predictive feature for strikeout props.
"""

from sqlalchemy import Integer, Float, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class PitcherArsenal(Base, TimestampMixin):
    """Single pitch type in a pitcher's arsenal for a given season.

    Aggregated from Statcast pitch-level data — one row per
    (pitcher, season, pitch_type) — capturing usage, characteristics, and outcome
    metrics. Strong matchup features for strikeout props live here. The unique
    constraint enforces one row per (pitcher, season, pitch_type).

    Attributes:
        id: Surrogate primary key.
        pitcher_id: FK to the pitching :class:`~app.models.player.Player`.
        season: Season year.
        pitch_type: Pitch classification code, matching
            :attr:`~app.sports.mlb.models.pitch_event.PitchEvent.pitch_type`
            (``"FF"`` | ``"SL"`` | ``"CU"`` | ``"CH"`` | ``"SI"`` | ``"FC"`` |
            ``"KC"`` | ``"FS"`` | ``"KN"`` | ``"EP"``).
        pitch_count: Number of pitches of this type thrown in the season.
        usage_pct: Share of total pitches this type represents.
        avg_velocity: Average release velocity, in mph (nullable).
        avg_spin_rate: Average spin rate, in rpm (nullable).
        avg_pfx_x: Average horizontal movement, in inches (nullable).
        avg_pfx_z: Average vertical movement, in inches (nullable).
        whiff_pct: Swing-and-miss rate on this pitch (nullable).
        csw_pct: Called-strike-plus-whiff rate (nullable).
        chase_pct: Out-of-zone swing rate induced (nullable).
        xwoba_against: Expected wOBA allowed on this pitch (nullable).
        slg_against: Slugging allowed on this pitch (nullable).
        vs_lhh_woba: wOBA allowed vs left-handed hitters (nullable).
        vs_rhh_woba: wOBA allowed vs right-handed hitters (nullable).
        pitcher: Eager-loaded :class:`~app.models.player.Player` relationship.
        created_at: Row creation timestamp (from :class:`TimestampMixin`).
        updated_at: Last update timestamp (from :class:`TimestampMixin`).
    """

    __tablename__ = "pitcher_arsenals"
    __table_args__ = (
        UniqueConstraint(
            "pitcher_id", "season", "pitch_type",
            name="uq_pitcher_arsenal_pitcher_season_type",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pitcher_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False)
    season: Mapped[int] = mapped_column(Integer, nullable=False)

    # Pitch classification code (matches PitchEvent.pitch_type)
    # 'FF' | 'SL' | 'CU' | 'CH' | 'SI' | 'FC' | 'KC' | 'FS' | 'KN' | 'EP'
    pitch_type: Mapped[str] = mapped_column(String(5), nullable=False)

    # Volume
    pitch_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    usage_pct: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Characteristics
    avg_velocity: Mapped[float | None] = mapped_column(Float)
    avg_spin_rate: Mapped[int | None] = mapped_column(Integer)
    avg_pfx_x: Mapped[float | None] = mapped_column(Float)  # Avg horizontal movement (in)
    avg_pfx_z: Mapped[float | None] = mapped_column(Float)  # Avg vertical movement (in)

    # Outcome metrics
    whiff_pct: Mapped[float | None] = mapped_column(Float)   # Swing-and-miss rate on this pitch
    csw_pct: Mapped[float | None] = mapped_column(Float)     # Called strike + whiff %
    chase_pct: Mapped[float | None] = mapped_column(Float)   # Out-of-zone swing rate

    # Quality of contact allowed
    xwoba_against: Mapped[float | None] = mapped_column(Float)
    slg_against: Mapped[float | None] = mapped_column(Float)

    # Handedness splits for this pitch type
    vs_lhh_woba: Mapped[float | None] = mapped_column(Float)  # wOBA vs left-handed hitters
    vs_rhh_woba: Mapped[float | None] = mapped_column(Float)  # wOBA vs right-handed hitters

    # --- Relationships ---
    pitcher = relationship("Player", lazy="selectin")

    def __repr__(self) -> str:
        """Return a concise debug representation for logging/debugging."""
        return (
            f"<PitcherArsenal pitcher={self.pitcher_id} "
            f"season={self.season} type={self.pitch_type} usage={self.usage_pct:.1%}>"
        )
