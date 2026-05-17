"""
MlbPlayerSeasonStats — Cached season-level aggregates per (player, season, role).

Refreshed daily from the MLB Stats API and Statcast. Contains the full MLB-specific
column set for both batters and pitchers, including traditional counting stats,
rate stats, sabermetric metrics (wRC+, FIP, WAR), and Statcast quality-of-contact
metrics (exit velocity, barrel rate, xwOBA).

The `role` column distinguishes batter vs pitcher rows — two-way players like
Ohtani will have separate rows for each role.
"""

from datetime import datetime

from sqlalchemy import Integer, Float, String, ForeignKey, DateTime, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class MlbPlayerSeasonStats(Base):
    """Full-season stat line for an MLB player (one row per player/season/role)."""

    __tablename__ = "mlb_player_season_stats"
    __table_args__ = (
        UniqueConstraint("player_id", "season", "role", name="uq_mlb_season_stats_player_season_role"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False)
    season: Mapped[int] = mapped_column(Integer, nullable=False)
    team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"))  # Last team that season

    # 'batter' | 'pitcher' — two-way players get separate rows
    role: Mapped[str] = mapped_column(String(20), nullable=False)

    # ========================
    # BATTER COUNTING STATS
    # ========================
    games: Mapped[int | None] = mapped_column(Integer)
    pa: Mapped[int | None] = mapped_column(Integer)       # Plate appearances
    ab: Mapped[int | None] = mapped_column(Integer)       # At bats
    runs: Mapped[int | None] = mapped_column(Integer)
    hits: Mapped[int | None] = mapped_column(Integer)
    doubles: Mapped[int | None] = mapped_column(Integer)
    triples: Mapped[int | None] = mapped_column(Integer)
    home_runs: Mapped[int | None] = mapped_column(Integer)
    rbi: Mapped[int | None] = mapped_column(Integer)
    walks: Mapped[int | None] = mapped_column(Integer)
    strikeouts: Mapped[int | None] = mapped_column(Integer)
    stolen_bases: Mapped[int | None] = mapped_column(Integer)
    caught_stealing: Mapped[int | None] = mapped_column(Integer)
    hbp: Mapped[int | None] = mapped_column(Integer)      # Hit by pitch
    sac_flies: Mapped[int | None] = mapped_column(Integer)
    sac_hits: Mapped[int | None] = mapped_column(Integer)  # Sac bunts
    gidp: Mapped[int | None] = mapped_column(Integer)     # Grounded into double play

    # ========================
    # BATTER RATE STATS
    # ========================
    avg: Mapped[float | None] = mapped_column(Float)      # Batting average
    obp: Mapped[float | None] = mapped_column(Float)      # On-base percentage
    slg: Mapped[float | None] = mapped_column(Float)      # Slugging percentage
    ops: Mapped[float | None] = mapped_column(Float)      # OBP + SLG
    iso: Mapped[float | None] = mapped_column(Float)      # Isolated power (SLG - AVG)
    babip: Mapped[float | None] = mapped_column(Float)    # Batting average on balls in play
    k_pct: Mapped[float | None] = mapped_column(Float)    # Strikeout rate
    bb_pct: Mapped[float | None] = mapped_column(Float)   # Walk rate
    hr_per_fb: Mapped[float | None] = mapped_column(Float)  # HR per fly ball

    # ========================
    # BATTER SABERMETRIC
    # ========================
    woba: Mapped[float | None] = mapped_column(Float)     # Weighted on-base average
    wrc_plus: Mapped[float | None] = mapped_column(Float)  # Weighted runs created+ (100 = avg)
    war: Mapped[float | None] = mapped_column(Float)      # Wins above replacement

    # ========================
    # BATTER STATCAST METRICS
    # ========================
    avg_exit_velocity: Mapped[float | None] = mapped_column(Float)
    max_exit_velocity: Mapped[float | None] = mapped_column(Float)
    avg_launch_angle: Mapped[float | None] = mapped_column(Float)
    sweet_spot_pct: Mapped[float | None] = mapped_column(Float)  # 8-32 degree LA%
    hard_hit_pct: Mapped[float | None] = mapped_column(Float)    # 95+ mph EV%
    barrel_pct: Mapped[float | None] = mapped_column(Float)      # Barrel rate

    # Expected stats (Statcast-modeled)
    xba: Mapped[float | None] = mapped_column(Float)
    xslg: Mapped[float | None] = mapped_column(Float)
    xwoba: Mapped[float | None] = mapped_column(Float)
    xiso: Mapped[float | None] = mapped_column(Float)

    # Plate discipline (Statcast)
    whiff_pct: Mapped[float | None] = mapped_column(Float)         # Swing-and-miss rate
    chase_pct: Mapped[float | None] = mapped_column(Float)         # Out-of-zone swing rate
    zone_contact_pct: Mapped[float | None] = mapped_column(Float)  # Contact on in-zone swings
    sprint_speed_ft_per_sec: Mapped[float | None] = mapped_column(Float)

    # ========================
    # PITCHER COUNTING STATS
    # ========================
    games_started: Mapped[int | None] = mapped_column(Integer)
    innings_pitched: Mapped[float | None] = mapped_column(Float)  # e.g. 6.2 = 6 2/3 IP
    hits_allowed: Mapped[int | None] = mapped_column(Integer)
    runs_allowed: Mapped[int | None] = mapped_column(Integer)
    earned_runs: Mapped[int | None] = mapped_column(Integer)
    # walks and strikeouts are shared with batter columns above
    hr_allowed: Mapped[int | None] = mapped_column(Integer)
    qs: Mapped[int | None] = mapped_column(Integer)        # Quality starts
    holds: Mapped[int | None] = mapped_column(Integer)
    saves: Mapped[int | None] = mapped_column(Integer)
    blown_saves: Mapped[int | None] = mapped_column(Integer)

    # ========================
    # PITCHER RATE STATS
    # ========================
    era: Mapped[float | None] = mapped_column(Float)       # Earned run average
    fip: Mapped[float | None] = mapped_column(Float)       # Fielding independent pitching
    xfip: Mapped[float | None] = mapped_column(Float)      # Expected FIP (league-avg HR/FB)
    siera: Mapped[float | None] = mapped_column(Float)     # Skill-interactive ERA
    whip: Mapped[float | None] = mapped_column(Float)      # Walks + hits per IP
    k_per_9: Mapped[float | None] = mapped_column(Float)   # Strikeouts per 9 innings
    bb_per_9: Mapped[float | None] = mapped_column(Float)  # Walks per 9 innings
    hr_per_9: Mapped[float | None] = mapped_column(Float)  # Home runs per 9 innings
    k_bb_pct: Mapped[float | None] = mapped_column(Float)  # K% - BB%
    # babip is shared with batter column above
    lob_pct: Mapped[float | None] = mapped_column(Float)   # Left on base percentage
    gb_pct: Mapped[float | None] = mapped_column(Float)    # Ground ball rate
    fb_pct: Mapped[float | None] = mapped_column(Float)    # Fly ball rate
    # hr_per_fb is shared with batter column above

    # ========================
    # PITCHER STATCAST METRICS
    # ========================
    avg_fb_velocity: Mapped[float | None] = mapped_column(Float)      # Avg fastball velo
    avg_fb_spin_rate: Mapped[float | None] = mapped_column(Float)     # Avg fastball spin
    csw_pct: Mapped[float | None] = mapped_column(Float)              # Called strikes + whiffs %
    # whiff_pct and chase_pct are shared with batter section
    zone_pct: Mapped[float | None] = mapped_column(Float)             # % pitches in zone
    first_pitch_strike_pct: Mapped[float | None] = mapped_column(Float)

    # Quality-of-contact allowed (pitcher perspective)
    barrel_pct_allowed: Mapped[float | None] = mapped_column(Float)
    hard_hit_pct_allowed: Mapped[float | None] = mapped_column(Float)
    xera: Mapped[float | None] = mapped_column(Float)                 # Expected ERA
    xwoba_allowed: Mapped[float | None] = mapped_column(Float)

    # ========================
    # METADATA
    # ========================
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="mlb_stats_api")

    # --- Relationships ---
    player = relationship("Player", lazy="selectin")
    team = relationship("Team", lazy="selectin")

    def __repr__(self) -> str:
        return (
            f"<MlbPlayerSeasonStats player={self.player_id} "
            f"season={self.season} role={self.role}>"
        )
