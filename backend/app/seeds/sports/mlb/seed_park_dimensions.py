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

All 30 parks are fully populated for the 2026 season (line, gap, and center
distances plus per-section wall heights); see the source notes above
:data:`PARK_DIMENSIONS` for provenance and API overrides.
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
# seed_venues.py).
#
# Sources (verified June 2026):
#   * Distances: MLB Stats API ``/api/v1/venues?sportId=1&season=2026&hydrate=fieldInfo``
#     (leftLine/center/rightLine + the fieldInfo point nearest each power alley),
#     overridden where the API is stale vs. announced renovations:
#       - Rogers Centre: 2023 renovation (LC 368 / CF 400 / RC 359); API still
#         lists the pre-2023 375/404/375.
#       - Comerica Park: CF moved in to 412 for 2023; API still lists 420.
#       - Kauffman Stadium: foul lines stay 330 to the poles per the Royals /
#         Wikipedia; the API's 347/344 are the new 2026 corner-bend distances.
#   * 2025-26 renovations reflected: Kauffman 2026 (gaps 387→379, walls 10→8.5
#     except CF), Camden Yards 2025 ("Walltimore" pulled back in, LC 376).
#   * Wall heights: representative values per section (many walls vary within a
#     section) from Clem's Baseball stadium statistics + team renovation
#     announcements (TOR 2023, DET 2023, KC 2026).
PARK_DIMENSIONS: dict[int, dict] = {

    # ── American League East ──────────────────────────────────────────────
    # Yankee Stadium — NYY
    3313: _pd(lf_distance_ft=318, cf_distance_ft=408, rf_distance_ft=314,
              lf_gap_distance_ft=399, rf_gap_distance_ft=385,
              lf_wall_height_ft=8, cf_wall_height_ft=8, rf_wall_height_ft=8),
    # Fenway Park — BOS (cf is the deep CF "triangle"; straightaway CF ~390;
    # lf wall = Green Monster)
    3:    _pd(lf_distance_ft=310, cf_distance_ft=420, rf_distance_ft=302,
              lf_gap_distance_ft=379, rf_gap_distance_ft=380,
              lf_wall_height_ft=37, cf_wall_height_ft=17, rf_wall_height_ft=5),
    # Oriole Park at Camden Yards — BAL (2025 LF wall pulled back in; rf wall
    # is the 21 ft scoreboard wall)
    2:    _pd(lf_distance_ft=333, cf_distance_ft=410, rf_distance_ft=318,
              lf_gap_distance_ft=376, rf_gap_distance_ft=373,
              lf_wall_height_ft=7, cf_wall_height_ft=7, rf_wall_height_ft=21),
    # Rogers Centre — TOR (post-2023 renovation; staggered walls 8 to 14'4")
    14:   _pd(lf_distance_ft=328, cf_distance_ft=400, rf_distance_ft=328,
              lf_gap_distance_ft=368, rf_gap_distance_ft=359,
              lf_wall_height_ft=14.3, cf_wall_height_ft=8, rf_wall_height_ft=12.6),
    # Tropicana Field — TB
    12:   _pd(lf_distance_ft=315, cf_distance_ft=404, rf_distance_ft=322,
              lf_gap_distance_ft=370, rf_gap_distance_ft=370,
              lf_wall_height_ft=11, cf_wall_height_ft=9, rf_wall_height_ft=11),

    # ── American League Central ───────────────────────────────────────────
    # Progressive Field — CLE (lf wall = 19 ft "mini-monster")
    5:    _pd(lf_distance_ft=325, cf_distance_ft=405, rf_distance_ft=325,
              lf_gap_distance_ft=370, rf_gap_distance_ft=375,
              lf_wall_height_ft=19, cf_wall_height_ft=9, rf_wall_height_ft=9),
    # Comerica Park — DET (CF 412 since 2023; LF/RF walls lowered to 7 ft)
    2394: _pd(lf_distance_ft=345, cf_distance_ft=412, rf_distance_ft=330,
              lf_gap_distance_ft=370, rf_gap_distance_ft=365,
              lf_wall_height_ft=7, cf_wall_height_ft=9, rf_wall_height_ft=7),
    # Kauffman Stadium — KC (2026: gaps in to 379, walls down to 8.5 except CF)
    7:    _pd(lf_distance_ft=330, cf_distance_ft=410, rf_distance_ft=330,
              lf_gap_distance_ft=379, rf_gap_distance_ft=379,
              lf_wall_height_ft=8.5, cf_wall_height_ft=10, rf_wall_height_ft=8.5),
    # Target Field — MIN (rf wall = 23 ft overhang wall)
    3312: _pd(lf_distance_ft=339, cf_distance_ft=404, rf_distance_ft=328,
              lf_gap_distance_ft=377, rf_gap_distance_ft=367,
              lf_wall_height_ft=8, cf_wall_height_ft=8, rf_wall_height_ft=23),
    # Rate Field — CWS
    4:    _pd(lf_distance_ft=330, cf_distance_ft=400, rf_distance_ft=335,
              lf_gap_distance_ft=377, rf_gap_distance_ft=372,
              lf_wall_height_ft=8, cf_wall_height_ft=8, rf_wall_height_ft=8),

    # ── American League West ──────────────────────────────────────────────
    # Daikin Park — HOU (lf wall = Crawford Boxes)
    2392: _pd(lf_distance_ft=315, cf_distance_ft=409, rf_distance_ft=326,
              lf_gap_distance_ft=362, rf_gap_distance_ft=373,
              lf_wall_height_ft=21, cf_wall_height_ft=9, rf_wall_height_ft=7),
    # Angel Stadium — LAA (rf wall = 18 ft scoreboard wall)
    1:    _pd(lf_distance_ft=330, cf_distance_ft=396, rf_distance_ft=330,
              lf_gap_distance_ft=389, rf_gap_distance_ft=365,
              lf_wall_height_ft=5, cf_wall_height_ft=8, rf_wall_height_ft=18),
    # T-Mobile Park — SEA (Stats API fieldInfo; scoreboard-marked CF is 401)
    680:  _pd(lf_distance_ft=331, cf_distance_ft=405, rf_distance_ft=327,
              lf_gap_distance_ft=390, rf_gap_distance_ft=387,
              lf_wall_height_ft=8, cf_wall_height_ft=8, rf_wall_height_ft=8),
    # Globe Life Field — TEX
    5325: _pd(lf_distance_ft=329, cf_distance_ft=407, rf_distance_ft=326,
              lf_gap_distance_ft=372, rf_gap_distance_ft=374,
              lf_wall_height_ft=8, cf_wall_height_ft=8, rf_wall_height_ft=8),
    # Sutter Health Park — ATH (temporary Triple-A home through ~2027)
    2529: _pd(lf_distance_ft=330, cf_distance_ft=403, rf_distance_ft=325,
              lf_gap_distance_ft=380, rf_gap_distance_ft=380,
              lf_wall_height_ft=8, cf_wall_height_ft=8, rf_wall_height_ft=8),

    # ── National League East ──────────────────────────────────────────────
    # Citi Field — NYM
    3289: _pd(lf_distance_ft=335, cf_distance_ft=408, rf_distance_ft=330,
              lf_gap_distance_ft=370, rf_gap_distance_ft=380,
              lf_wall_height_ft=8, cf_wall_height_ft=8, rf_wall_height_ft=8),
    # Citizens Bank Park — PHI
    2681: _pd(lf_distance_ft=329, cf_distance_ft=401, rf_distance_ft=330,
              lf_gap_distance_ft=381, rf_gap_distance_ft=369,
              lf_wall_height_ft=11, cf_wall_height_ft=6, rf_wall_height_ft=13),
    # Truist Park — ATL (rf wall = 16 ft)
    4705: _pd(lf_distance_ft=335, cf_distance_ft=400, rf_distance_ft=325,
              lf_gap_distance_ft=385, rf_gap_distance_ft=375,
              lf_wall_height_ft=6, cf_wall_height_ft=8, rf_wall_height_ft=16),
    # Nationals Park — WSH
    3309: _pd(lf_distance_ft=336, cf_distance_ft=402, rf_distance_ft=335,
              lf_gap_distance_ft=377, rf_gap_distance_ft=370,
              lf_wall_height_ft=10, cf_wall_height_ft=12, rf_wall_height_ft=9),
    # loanDepot park — MIA
    4169: _pd(lf_distance_ft=344, cf_distance_ft=407, rf_distance_ft=335,
              lf_gap_distance_ft=386, rf_gap_distance_ft=392,
              lf_wall_height_ft=10, cf_wall_height_ft=15, rf_wall_height_ft=10),

    # ── National League Central ───────────────────────────────────────────
    # Wrigley Field — CHC (ivy-covered brick; taller in the corner "wells")
    17:   _pd(lf_distance_ft=355, cf_distance_ft=400, rf_distance_ft=353,
              lf_gap_distance_ft=368, rf_gap_distance_ft=368,
              lf_wall_height_ft=16, cf_wall_height_ft=11, rf_wall_height_ft=16),
    # Busch Stadium — STL
    2889: _pd(lf_distance_ft=336, cf_distance_ft=400, rf_distance_ft=335,
              lf_gap_distance_ft=375, rf_gap_distance_ft=375,
              lf_wall_height_ft=8, cf_wall_height_ft=8, rf_wall_height_ft=8),
    # American Family Field — MIL
    32:   _pd(lf_distance_ft=344, cf_distance_ft=400, rf_distance_ft=345,
              lf_gap_distance_ft=371, rf_gap_distance_ft=374,
              lf_wall_height_ft=8, cf_wall_height_ft=8, rf_wall_height_ft=8),
    # PNC Park — PIT (rf wall = 21 ft Clemente Wall; deep LC notch runs to 410)
    31:   _pd(lf_distance_ft=325, cf_distance_ft=399, rf_distance_ft=320,
              lf_gap_distance_ft=389, rf_gap_distance_ft=375,
              lf_wall_height_ft=6, cf_wall_height_ft=10, rf_wall_height_ft=21),
    # Great American Ball Park — CIN (lf wall = 12 ft sun/moon deck wall)
    2602: _pd(lf_distance_ft=328, cf_distance_ft=404, rf_distance_ft=325,
              lf_gap_distance_ft=379, rf_gap_distance_ft=370,
              lf_wall_height_ft=12, cf_wall_height_ft=8, rf_wall_height_ft=8),

    # ── National League West ──────────────────────────────────────────────
    # Dodger Stadium — LAD (low ~4 ft fences at the corners)
    22:   _pd(lf_distance_ft=330, cf_distance_ft=395, rf_distance_ft=330,
              lf_gap_distance_ft=385, rf_gap_distance_ft=385,
              lf_wall_height_ft=4, cf_wall_height_ft=8, rf_wall_height_ft=4),
    # Petco Park — SD
    2680: _pd(lf_distance_ft=336, cf_distance_ft=396, rf_distance_ft=322,
              lf_gap_distance_ft=386, rf_gap_distance_ft=391,
              lf_wall_height_ft=4, cf_wall_height_ft=7, rf_wall_height_ft=10),
    # Oracle Park — SF (rf wall = 24 ft brick wall; rf gap = 415 Triples Alley)
    2395: _pd(lf_distance_ft=339, cf_distance_ft=391, rf_distance_ft=309,
              lf_gap_distance_ft=399, rf_gap_distance_ft=415,
              lf_wall_height_ft=8, cf_wall_height_ft=8, rf_wall_height_ft=24),
    # Chase Field — ARI (cf wall = 25 ft batter's eye)
    15:   _pd(lf_distance_ft=328, cf_distance_ft=407, rf_distance_ft=335,
              lf_gap_distance_ft=376, rf_gap_distance_ft=376,
              lf_wall_height_ft=8, cf_wall_height_ft=25, rf_wall_height_ft=8),
    # Coors Field — COL
    19:   _pd(lf_distance_ft=347, cf_distance_ft=415, rf_distance_ft=350,
              lf_gap_distance_ft=390, rf_gap_distance_ft=375,
              lf_wall_height_ft=8, cf_wall_height_ft=8, rf_wall_height_ft=14),
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
