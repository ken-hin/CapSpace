"""Seed MLB physical outfield dimensions, keyed by venue and season.

Fence distances and wall heights are a slowly-changing physical property of a
ballpark, distinct from the statistical park factors seeded by
``seed_park_factors_2026.py``. They are stored per ``(venue_id, season)`` on the
:class:`ParkDimensions` table so that mid-career changes (e.g. the Orioles
moving the left-field wall) can be captured by season.

Like the park-factors seeder, :data:`PARK_DIMENSIONS` is keyed by **MLB Stats
API venue id** and translated to ``venues.id`` at seed time, so this MUST run
after venues are seeded and flushed. Rows are upserted on the
``(venue_id, season)`` unique constraint, making the seeder safe to re-run.

Down-the-line distances (``*_distance_ft``) are populated first; power-alley /
gap distances (``*_gap_distance_ft``) are optional and can be backfilled later.
Only a handful of parks are filled in below as a starting point — pass the
known measurements as keyword args to :func:`_pd` for the rest.
"""

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import Sport
from app.models.venue import Venue
from app.sports.mlb.models.park_dimensions import ParkDimensions

SEASON = 2026

# Physical dimension fields stored on ParkDimensions (feet).
DIMENSION_FIELDS = (
    "lf_distance_ft", "cf_distance_ft", "rf_distance_ft",
    "lf_gap_distance_ft", "rf_gap_distance_ft",
    "lf_wall_height_ft", "cf_wall_height_ft", "rf_wall_height_ft",
)


def _pd(**values) -> dict:
    """Build one dimensions row, defaulting unspecified measurements to ``None``.

    Args:
        **values: Any subset of :data:`DIMENSION_FIELDS` to populate.

    Returns:
        dict: A dimensions payload with every field in :data:`DIMENSION_FIELDS`
        present (``None`` where unspecified).

    Raises:
        ValueError: If a keyword is not a recognized dimension field, so typos
            fail loudly instead of being silently dropped.
    """
    unknown = set(values) - set(DIMENSION_FIELDS)
    if unknown:
        raise ValueError(f"Unknown dimension field(s): {sorted(unknown)}")
    row: dict = {field: None for field in DIMENSION_FIELDS}
    row.update(values)
    return row


# Outfield dimensions keyed by MLB Stats API venue id (matches VENUE_DETAILS in
# seed_venues.py). Line distances below were carried over from the original
# park-factors template; verify and add gap distances when available.
PARK_DIMENSIONS: dict[int, dict] = {

    # ── American League East ──────────────────────────────────────────────
    3313: _pd(lf_distance_ft=355, cf_distance_ft=408, rf_distance_ft=338.5,
              lf_wall_height_ft=8, rf_wall_height_ft=8),    # Yankee Stadium — NYY
    3:    _pd(lf_distance_ft=310, cf_distance_ft=420, rf_distance_ft=302,
              lf_wall_height_ft=37, rf_wall_height_ft=5),   # Fenway Park — BOS
    2:    _pd(),   # Oriole Park at Camden Yards — BAL
    14:   _pd(),   # Rogers Centre — TOR
    12:   _pd(),   # Tropicana Field — TB

    # ── American League Central ───────────────────────────────────────────
    5:    _pd(),   # Progressive Field — CLE
    2394: _pd(),   # Comerica Park — DET
    7:    _pd(),   # Kauffman Stadium — KC
    3312: _pd(),   # Target Field — MIN
    4:    _pd(),   # Rate Field — CWS

    # ── American League West ──────────────────────────────────────────────
    2392: _pd(),   # Daikin Park — HOU
    1:    _pd(),   # Angel Stadium — LAA
    680:  _pd(lf_distance_ft=331, cf_distance_ft=401, rf_distance_ft=326,
              lf_wall_height_ft=8, rf_wall_height_ft=8),    # T-Mobile Park — SEA
    5325: _pd(),   # Globe Life Field — TEX
    2529: _pd(),   # Sutter Health Park — ATH

    # ── National League East ──────────────────────────────────────────────
    3289: _pd(),   # Citi Field — NYM
    2681: _pd(),   # Citizens Bank Park — PHI
    4705: _pd(),   # Truist Park — ATL
    3309: _pd(),   # Nationals Park — WSH
    4169: _pd(),   # loanDepot park — MIA

    # ── National League Central ───────────────────────────────────────────
    17:   _pd(),   # Wrigley Field — CHC
    2889: _pd(),   # Busch Stadium — STL
    32:   _pd(),   # American Family Field — MIL
    31:   _pd(),   # PNC Park — PIT
    2602: _pd(),   # Great American Ball Park — CIN

    # ── National League West ──────────────────────────────────────────────
    22:   _pd(),   # Dodger Stadium — LAD
    2680: _pd(),   # Petco Park — SD
    2395: _pd(),   # Oracle Park — SF
    15:   _pd(),   # Chase Field — ARI
    19:   _pd(lf_distance_ft=347, cf_distance_ft=415, rf_distance_ft=350,
              lf_wall_height_ft=8, rf_wall_height_ft=14),   # Coors Field — COL
}


async def _venue_id_by_external_id(session: AsyncSession) -> dict[str, int]:
    """Build a map of MLB venue ``external_id`` (string) → ``venues.id`` (PK).

    Args:
        session: Active async database session.

    Returns:
        dict[str, int]: external_id → venues.id for all MLB venues.
    """
    result = await session.execute(
        select(Venue.external_id, Venue.id).where(Venue.sport == Sport.MLB)
    )
    return {ext_id: vid for ext_id, vid in result.all()}


def _build_rows(venue_id_map: dict[str, int], season: int) -> list[dict]:
    """Translate PARK_DIMENSIONS (keyed by MLBAM id) into ParkDimensions rows.

    Args:
        venue_id_map: external_id → venues.id map from :func:`_venue_id_by_external_id`.
        season: The season these dimensions apply to.

    Returns:
        list[dict]: Insert-ready ParkDimensions kwargs with resolved ``venue_id``.

    Raises:
        KeyError: If a PARK_DIMENSIONS entry references an MLBAM venue id that has
            no seeded venue, so missing data is loud rather than silently dropped.
    """
    rows: list[dict] = []
    for mlbam_id, dimensions in PARK_DIMENSIONS.items():
        external_id = str(mlbam_id)
        if external_id not in venue_id_map:
            raise KeyError(
                f"PARK_DIMENSIONS venue {mlbam_id} has no seeded venue "
                f"(external_id={external_id!r}); seed venues first."
            )
        rows.append({
            "venue_id": venue_id_map[external_id],
            "season": season,
            **dimensions,
        })
    return rows


async def seed_park_dimensions(session: AsyncSession, season: int = SEASON) -> int:
    """Upsert MLB outfield dimensions for the given season.

    Resolves each PARK_DIMENSIONS entry's MLBAM venue id to a ``venues.id``, then
    performs an idempotent upsert keyed on the ``(venue_id, season)`` unique
    constraint so re-running refreshes measurements without creating duplicates.

    Args:
        session: Active async database session. Venues must already be seeded
            and flushed so their primary keys exist.
        season: Season the dimensions apply to (defaults to :data:`SEASON`).

    Returns:
        int: The number of dimension rows upserted.
    """
    venue_id_map = await _venue_id_by_external_id(session)
    rows = _build_rows(venue_id_map, season)
    if not rows:
        return 0

    stmt = insert(ParkDimensions).values(rows)
    stmt = stmt.on_conflict_do_update(
        constraint="uq_park_dimensions_venue_season",
        set_={col: getattr(stmt.excluded, col) for col in DIMENSION_FIELDS},
    )
    await session.execute(stmt)
    return len(rows)
