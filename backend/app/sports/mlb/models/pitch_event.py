"""
PitchEvent — The Statcast firehose.

Every pitch thrown in an MLB game, with full tracking data: release point,
velocity, spin rate, movement, plate location, and batted-ball metrics when
the ball is put in play. This is the foundation for pitcher arsenal analysis,
expected stats computation, and matchup-level feature engineering.

Designed as a TimescaleDB hypertable partitioned on `pitch_time` for
efficient time-range queries across seasons of data.

Data source: Baseball Savant via pybaseball (Tier B — modeling data).
"""

from datetime import datetime

from sqlalchemy import (
    Integer, String, Float, ForeignKey, DateTime, Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class PitchEvent(Base):
    """Single pitch from a Statcast-tracked MLB game."""

    __tablename__ = "pitch_events"
    __table_args__ = (
        Index("ix_pitch_events_game_ab_pitch", "game_id", "at_bat_num", "pitch_num"),
        Index("ix_pitch_events_pitcher_time", "pitcher_id", "pitch_time"),
        Index("ix_pitch_events_batter_time", "batter_id", "pitch_time"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # MLBAM play ID for deduplication and linking back to live feed
    mlb_play_id: Mapped[str | None] = mapped_column(String(50), index=True)

    # Game + participants
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id"), nullable=False)
    pitcher_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False)
    batter_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False)

    # At-bat context
    inning: Mapped[int] = mapped_column(Integer, nullable=False)
    half_inning: Mapped[str] = mapped_column(String(10), nullable=False)  # 'top' | 'bottom'
    at_bat_num: Mapped[int] = mapped_column(Integer, nullable=False)
    pitch_num: Mapped[int] = mapped_column(Integer, nullable=False)

    # Count state at time of pitch
    balls: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    strikes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    outs_when_up: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Denormalized handedness (avoids join to Player for split queries)
    pitcher_throws: Mapped[str | None] = mapped_column(String(1))  # 'L' | 'R'
    batter_stands: Mapped[str | None] = mapped_column(String(1))   # 'L' | 'R'

    # ========================
    # PITCH TRACKING DATA
    # ========================

    # Pitch classification
    # 'FF' = 4-seam, 'SL' = slider, 'CU' = curveball, 'CH' = changeup,
    # 'SI' = sinker, 'FC' = cutter, 'KC' = knuckle curve, 'FS' = splitter
    pitch_type: Mapped[str | None] = mapped_column(String(5))
    pitch_name: Mapped[str | None] = mapped_column(String(50))

    # Velocity
    release_speed_mph: Mapped[float | None] = mapped_column(Float)
    effective_speed_mph: Mapped[float | None] = mapped_column(Float)

    # Spin
    release_spin_rate: Mapped[int | None] = mapped_column(Integer)

    # Release point coordinates (feet from plate center)
    release_pos_x: Mapped[float | None] = mapped_column(Float)
    release_pos_y: Mapped[float | None] = mapped_column(Float)
    release_pos_z: Mapped[float | None] = mapped_column(Float)

    # Pitch movement (inches of break)
    pfx_x: Mapped[float | None] = mapped_column(Float)  # Horizontal movement
    pfx_z: Mapped[float | None] = mapped_column(Float)  # Vertical movement (induced)

    # Plate crossing location (feet from plate center; -1 to 1 typical)
    plate_x: Mapped[float | None] = mapped_column(Float)
    plate_z: Mapped[float | None] = mapped_column(Float)

    # Initial velocity components (ft/s)
    vx0: Mapped[float | None] = mapped_column(Float)
    vy0: Mapped[float | None] = mapped_column(Float)
    vz0: Mapped[float | None] = mapped_column(Float)

    # Acceleration components (ft/s^2)
    ax: Mapped[float | None] = mapped_column(Float)
    ay: Mapped[float | None] = mapped_column(Float)
    az: Mapped[float | None] = mapped_column(Float)

    # Strike zone number (1-14; 1-9 = zone, 11-14 = chase quadrants)
    zone: Mapped[int | None] = mapped_column(Integer)

    # ========================
    # OUTCOME
    # ========================

    # Pitch-level result description
    # 'called_strike' | 'ball' | 'foul' | 'swinging_strike' |
    # 'hit_into_play' | 'blocked_ball' | 'hit_by_pitch'
    description: Mapped[str | None] = mapped_column(String(100))

    # Terminal event (null for non-terminal pitches)
    # 'single' | 'double' | 'home_run' | 'walk' | 'strikeout' | 'field_out' | ...
    events: Mapped[str | None] = mapped_column(String(100))

    # ========================
    # BATTED BALL DATA (if hit into play)
    # ========================

    launch_speed_mph: Mapped[float | None] = mapped_column(Float)   # Exit velocity
    launch_angle_deg: Mapped[float | None] = mapped_column(Float)   # Launch angle
    hit_location: Mapped[int | None] = mapped_column(Integer)       # Fielder position
    # 'ground_ball' | 'fly_ball' | 'line_drive' | 'popup'
    bb_type: Mapped[str | None] = mapped_column(String(20))
    hit_distance_ft: Mapped[int | None] = mapped_column(Integer)

    # ========================
    # EXPECTED STATS (Statcast computed)
    # ========================

    estimated_ba: Mapped[float | None] = mapped_column(Float)    # xBA
    estimated_slg: Mapped[float | None] = mapped_column(Float)   # xSLG
    estimated_woba: Mapped[float | None] = mapped_column(Float)  # xwOBA

    woba_value: Mapped[float | None] = mapped_column(Float)
    woba_denom: Mapped[int | None] = mapped_column(Integer)
    babip_value: Mapped[float | None] = mapped_column(Float)
    iso_value: Mapped[float | None] = mapped_column(Float)

    # ========================
    # TIMESTAMP (TimescaleDB partitioning key)
    # ========================

    pitch_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

    # --- Relationships ---
    game = relationship("Game", lazy="selectin")
    pitcher = relationship("Player", foreign_keys=[pitcher_id], lazy="selectin")
    batter = relationship("Player", foreign_keys=[batter_id], lazy="selectin")

    def __repr__(self) -> str:
        return (
            f"<PitchEvent game={self.game_id} ab={self.at_bat_num} "
            f"pitch={self.pitch_num} type={self.pitch_type}>"
        )
