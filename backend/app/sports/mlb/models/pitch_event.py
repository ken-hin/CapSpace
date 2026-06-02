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
    Integer, String, Float, ForeignKey, DateTime, Index, PrimaryKeyConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class PitchEvent(Base):
    """Single pitch from a Statcast-tracked MLB game.

    The lowest-grain MLB table — one row per pitch — and the foundation for arsenal
    analysis, expected-stats computation, and matchup features. Stored as a
    TimescaleDB hypertable; uses a composite PK (id, pitch_time) because TimescaleDB
    requires the partitioning column to be part of any unique index/primary key.

    Attributes:
        id: Auto-incrementing id (part of composite PK with ``pitch_time``).
        mlb_play_id: MLBAM play id for dedup and live-feed linking (indexed, nullable).
        game_id: FK to the :class:`~app.models.game.Game`.
        pitcher_id: FK to the pitching :class:`~app.models.player.Player`.
        batter_id: FK to the batting :class:`~app.models.player.Player`.
        inning: Inning number.
        half_inning: Half of the inning (``"top"`` | ``"bottom"``).
        at_bat_num: At-bat number within the game.
        pitch_num: Pitch number within the at-bat.
        balls: Ball count before the pitch.
        strikes: Strike count before the pitch.
        outs_when_up: Outs in the inning when the pitch was thrown.
        pitcher_throws: Denormalized pitcher handedness (``"L"`` | ``"R"``).
        batter_stands: Denormalized batter handedness (``"L"`` | ``"R"``).
        pitch_type: Pitch classification code (``"FF"`` 4-seam, ``"SL"`` slider,
            ``"CU"`` curve, ``"CH"`` change, ``"SI"`` sinker, ``"FC"`` cutter,
            ``"KC"`` knuckle curve, ``"FS"`` splitter).
        pitch_name: Human-readable pitch name.
        release_speed_mph: Velocity at release, in mph.
        effective_speed_mph: Perceived velocity adjusted for extension, in mph.
        release_spin_rate: Spin rate at release, in rpm.
        release_pos_x: Horizontal release position, in feet from plate center.
        release_pos_y: Release distance from the plate, in feet.
        release_pos_z: Vertical release height, in feet.
        pfx_x: Horizontal movement, in inches of break.
        pfx_z: Induced vertical movement, in inches of break.
        plate_x: Horizontal plate-crossing location, in feet from center.
        plate_z: Vertical plate-crossing location, in feet.
        vx0: Initial x-velocity component, in ft/s.
        vy0: Initial y-velocity component, in ft/s.
        vz0: Initial z-velocity component, in ft/s.
        ax: x-acceleration component, in ft/s^2.
        ay: y-acceleration component, in ft/s^2.
        az: z-acceleration component, in ft/s^2.
        zone: Strike-zone number (1-9 in-zone, 11-14 chase quadrants).
        description: Pitch-level result, e.g. ``"called_strike"``, ``"ball"``,
            ``"swinging_strike"``, ``"hit_into_play"``.
        events: Terminal at-bat event, if this pitch ended the PA (nullable).
        launch_speed_mph: Batted-ball exit velocity, in mph (if in play).
        launch_angle_deg: Batted-ball launch angle, in degrees (if in play).
        hit_location: Fielder position the ball was hit to (if in play).
        bb_type: Batted-ball type (``"ground_ball"`` | ``"fly_ball"`` |
            ``"line_drive"`` | ``"popup"``).
        hit_distance_ft: Estimated batted-ball distance, in feet.
        estimated_ba: Statcast expected batting average (xBA).
        estimated_slg: Statcast expected slugging (xSLG).
        estimated_woba: Statcast expected wOBA (xwOBA).
        woba_value: wOBA value credited to the outcome.
        woba_denom: wOBA denominator for the PA.
        babip_value: BABIP value for the outcome.
        iso_value: Isolated-power value for the outcome.
        pitch_time: Pitch timestamp and hypertable partition key (tz-aware).
        game: Eager-loaded :class:`~app.models.game.Game` relationship.
        pitcher: Eager-loaded pitching :class:`~app.models.player.Player` relationship.
        batter: Eager-loaded batting :class:`~app.models.player.Player` relationship.
    """

    __tablename__ = "pitch_events"
    __table_args__ = (
        PrimaryKeyConstraint("id", "pitch_time"),
        Index("ix_pitch_events_game_ab_pitch", "game_id", "at_bat_num", "pitch_num"),
        Index("ix_pitch_events_pitcher_time", "pitcher_id", "pitch_time"),
        Index("ix_pitch_events_batter_time", "batter_id", "pitch_time"),
    )

    id: Mapped[int] = mapped_column(Integer, autoincrement=True)

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
        """Return a concise debug representation for logging/debugging."""
        return (
            f"<PitchEvent game={self.game_id} ab={self.at_bat_num} "
            f"pitch={self.pitch_num} type={self.pitch_type}>"
        )
