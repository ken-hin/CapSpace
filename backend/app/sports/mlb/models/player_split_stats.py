"""
MlbPlayerSplitStats — Same shape as MlbPlayerSeasonStats with a split_type column.

Splits are subsets of a player's season stats filtered by situation:
handedness matchups (vs LHP/RHP), home/away, day/night, pre/post All-Star
break, and rolling windows (last 7/15/30 days).

Critical for prediction modeling: a batter's xwOBA vs LHP may diverge
significantly from their overall line, and pitchers often have dramatic
home/away splits.
"""

from datetime import datetime

from sqlalchemy import Integer, Float, String, ForeignKey, DateTime, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class MlbPlayerSplitStats(Base):
    """Split-specific stat line for an MLB player (one row per player/season/role/split).

    Same column shape as
    :class:`~app.sports.mlb.models.player_season_stats.MlbPlayerSeasonStats` plus a
    ``split_type`` discriminator. Splits are situational subsets of a season line
    (handedness matchups, home/away, day/night, pre/post All-Star break, and rolling
    7/15/30-day windows) and are key inputs for matchup modeling. The unique
    constraint enforces one row per (player, season, role, split_type).

    The statistical columns are grouped and documented inline below under banner
    comments; only the identity/metadata columns are summarized here.

    Attributes:
        id: Surrogate primary key.
        player_id: FK to the :class:`~app.models.player.Player`.
        season: Season year.
        team_id: FK to the :class:`~app.models.team.Team` (nullable).
        role: Stat group populated (``"batter"`` | ``"pitcher"``).
        split_type: Situational split identifier (``"vs_lhp"`` | ``"vs_rhp"`` |
            ``"home"`` | ``"away"`` | ``"day"`` | ``"night"`` | ``"pre_asg"`` |
            ``"post_asg"`` | ``"last_7d"`` | ``"last_15d"`` | ``"last_30d"``).
        updated_at: Last refresh timestamp (server default ``now()``).
        source: Data source identifier; defaults to ``"mlb_stats_api"``.
        player: Eager-loaded :class:`~app.models.player.Player` relationship.
        team: Eager-loaded :class:`~app.models.team.Team` relationship.

    Note:
        Batter and pitcher statistical columns mirror
        :class:`~app.sports.mlb.models.player_season_stats.MlbPlayerSeasonStats`
        and are defined and documented inline below.
    """

    __tablename__ = "mlb_player_split_stats"
    __table_args__ = (
        UniqueConstraint(
            "player_id", "season", "role", "split_type",
            name="uq_mlb_split_stats_player_season_role_split",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False)
    season: Mapped[int] = mapped_column(Integer, nullable=False)
    team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"))

    # 'batter' | 'pitcher'
    role: Mapped[str] = mapped_column(String(20), nullable=False)

    # Split type identifier:
    # 'vs_lhp' | 'vs_rhp' | 'home' | 'away' | 'day' | 'night' |
    # 'pre_asg' | 'post_asg' | 'last_7d' | 'last_15d' | 'last_30d'
    split_type: Mapped[str] = mapped_column(String(20), nullable=False)

    # ========================
    # BATTER COUNTING STATS
    # ========================
    games: Mapped[int | None] = mapped_column(Integer)
    pa: Mapped[int | None] = mapped_column(Integer)
    ab: Mapped[int | None] = mapped_column(Integer)
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
    hbp: Mapped[int | None] = mapped_column(Integer)
    sac_flies: Mapped[int | None] = mapped_column(Integer)
    sac_hits: Mapped[int | None] = mapped_column(Integer)
    gidp: Mapped[int | None] = mapped_column(Integer)

    # ========================
    # BATTER RATE STATS
    # ========================
    avg: Mapped[float | None] = mapped_column(Float)
    obp: Mapped[float | None] = mapped_column(Float)
    slg: Mapped[float | None] = mapped_column(Float)
    ops: Mapped[float | None] = mapped_column(Float)
    iso: Mapped[float | None] = mapped_column(Float)
    babip: Mapped[float | None] = mapped_column(Float)
    k_pct: Mapped[float | None] = mapped_column(Float)
    bb_pct: Mapped[float | None] = mapped_column(Float)
    hr_per_fb: Mapped[float | None] = mapped_column(Float)

    # ========================
    # BATTER SABERMETRIC
    # ========================
    woba: Mapped[float | None] = mapped_column(Float)
    wrc_plus: Mapped[float | None] = mapped_column(Float)
    war: Mapped[float | None] = mapped_column(Float)

    # ========================
    # BATTER STATCAST METRICS
    # ========================
    avg_exit_velocity: Mapped[float | None] = mapped_column(Float)
    max_exit_velocity: Mapped[float | None] = mapped_column(Float)
    avg_launch_angle: Mapped[float | None] = mapped_column(Float)
    sweet_spot_pct: Mapped[float | None] = mapped_column(Float)
    hard_hit_pct: Mapped[float | None] = mapped_column(Float)
    barrel_pct: Mapped[float | None] = mapped_column(Float)
    xba: Mapped[float | None] = mapped_column(Float)
    xslg: Mapped[float | None] = mapped_column(Float)
    xwoba: Mapped[float | None] = mapped_column(Float)
    xiso: Mapped[float | None] = mapped_column(Float)
    whiff_pct: Mapped[float | None] = mapped_column(Float)
    chase_pct: Mapped[float | None] = mapped_column(Float)
    zone_contact_pct: Mapped[float | None] = mapped_column(Float)
    sprint_speed_ft_per_sec: Mapped[float | None] = mapped_column(Float)

    # ========================
    # PITCHER COUNTING STATS
    # ========================
    games_started: Mapped[int | None] = mapped_column(Integer)
    innings_pitched: Mapped[float | None] = mapped_column(Float)
    hits_allowed: Mapped[int | None] = mapped_column(Integer)
    runs_allowed: Mapped[int | None] = mapped_column(Integer)
    earned_runs: Mapped[int | None] = mapped_column(Integer)
    hr_allowed: Mapped[int | None] = mapped_column(Integer)
    qs: Mapped[int | None] = mapped_column(Integer)
    holds: Mapped[int | None] = mapped_column(Integer)
    saves: Mapped[int | None] = mapped_column(Integer)
    blown_saves: Mapped[int | None] = mapped_column(Integer)

    # ========================
    # PITCHER RATE STATS
    # ========================
    era: Mapped[float | None] = mapped_column(Float)
    fip: Mapped[float | None] = mapped_column(Float)
    xfip: Mapped[float | None] = mapped_column(Float)
    siera: Mapped[float | None] = mapped_column(Float)
    whip: Mapped[float | None] = mapped_column(Float)
    k_per_9: Mapped[float | None] = mapped_column(Float)
    bb_per_9: Mapped[float | None] = mapped_column(Float)
    hr_per_9: Mapped[float | None] = mapped_column(Float)
    k_bb_pct: Mapped[float | None] = mapped_column(Float)
    lob_pct: Mapped[float | None] = mapped_column(Float)
    gb_pct: Mapped[float | None] = mapped_column(Float)
    fb_pct: Mapped[float | None] = mapped_column(Float)

    # ========================
    # PITCHER STATCAST METRICS
    # ========================
    avg_fb_velocity: Mapped[float | None] = mapped_column(Float)
    avg_fb_spin_rate: Mapped[float | None] = mapped_column(Float)
    csw_pct: Mapped[float | None] = mapped_column(Float)
    zone_pct: Mapped[float | None] = mapped_column(Float)
    first_pitch_strike_pct: Mapped[float | None] = mapped_column(Float)
    barrel_pct_allowed: Mapped[float | None] = mapped_column(Float)
    hard_hit_pct_allowed: Mapped[float | None] = mapped_column(Float)
    xera: Mapped[float | None] = mapped_column(Float)
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
        """Return a concise debug representation for logging/debugging."""
        return (
            f"<MlbPlayerSplitStats player={self.player_id} "
            f"season={self.season} role={self.role} split={self.split_type}>"
        )
