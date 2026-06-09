"""Seed MLB park factors, keyed by venue, season, and rolling window.

Baseball Savant publishes park factors over a *rolling window* (the trailing
``window_years`` seasons, default 3) to smooth the small-sample noise of ~81
home games per year. Each row is stored per ``(venue_id, season, window_years)``
on the :class:`ParkFactor` table, where ``season`` is the **end year** of the
window — e.g. ``season=2026, window_years=3`` is the 2024–2026 window.

The hardcoded :data:`PARK_FACTORS` table below is keyed by **MLB Stats API venue
id** (the same integer keys used by ``VENUE_DETAILS`` in ``seed_venues.py``)
because that id is stable and easy to cross-check by hand. At seed time those
MLBAM ids are translated into real ``venues.id`` primary keys by querying the
already-seeded ``venues`` table, so this seeder MUST run after venues have been
seeded and flushed. Rows are upserted on the
``(venue_id, season, window_years)`` unique constraint, making the seeder safe
to re-run.

Factors are on the standard 100 = league-average scale. ``factor_overall`` is
Savant's headline composite (wOBAcon-based); ``factor_runs`` is the runs factor
(Savant ``R`` column). Unspecified factors default to ``None`` (unknown) rather
than 100, so a not-yet-filled park is distinguishable from a truly neutral one.

Physical outfield dimensions live in a separate table and are seeded by
``seed_park_dimensions.py`` — they come from a different source and change on a
different cadence than these statistical factors.

Values below are placeholders. Fill each venue from the Baseball Savant park-
factors leaderboard by passing the known factors as keyword args to
:func:`_pf` (HR-by-handedness comes from the separate L/R Savant views).
"""

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import Sport
from app.models.venue import Venue
from app.sports.mlb.models.park_factor import ParkFactor

SEASON = 2026          # end year of the rolling window
WINDOW_YEARS = 3       # Baseball Savant default rolling window

# Statistical factor fields stored on ParkFactor (100 = league average).
# Dimensions are intentionally NOT here — see seed_park_dimensions.py.
FACTOR_FIELDS = (
    "factor_overall",                       # Savant headline index (wOBAcon-based)
    "factor_runs",                          # Savant 'R' column
    "factor_hr_vs_l", "factor_hr_vs_r",     # from the separate L/R Savant views
    "factor_hits", "factor_xwobacon", "factor_obp", "factor_hardhit",
    "factor_bb", "factor_so",
    "pa",                                   # sample size backing the window
)


def _pf(*, source: str = "baseball_savant", **values) -> dict:
    """Build one park-factor row, defaulting unspecified factors to ``None``.

    Args:
        source: Data provenance; must satisfy the ck_park_factors_source check
            (``"baseball_savant"`` | ``"computed"``).
        **values: Any subset of :data:`FACTOR_FIELDS` to populate.

    Returns:
        dict: A factor payload with every field in :data:`FACTOR_FIELDS` present
        (``None`` where unspecified) plus ``source``.

    Raises:
        ValueError: If a keyword is not a recognized factor field, so typos fail
            loudly instead of being silently dropped.
    """
    unknown = set(values) - set(FACTOR_FIELDS)
    if unknown:
        raise ValueError(f"Unknown park-factor field(s): {sorted(unknown)}")
    row: dict = {field: None for field in FACTOR_FIELDS}
    row["source"] = source
    row.update(values)
    return row


# Park factors keyed by MLB Stats API venue id (matches VENUE_DETAILS in
# seed_venues.py). Replace each _pf() placeholder with the real Savant numbers,
# e.g. 19: _pf(factor_overall=112, factor_runs=125, factor_hr_vs_l=108, ...).
PARK_FACTORS: dict[int, dict] = {

    # ── American League East ──────────────────────────────────────────────
    3313: _pf(),   # Yankee Stadium — NYY
    3:    _pf(),   # Fenway Park — BOS
    2:    _pf(),   # Oriole Park at Camden Yards — BAL
    14:   _pf(),   # Rogers Centre — TOR
    12:   _pf(),   # Tropicana Field — TB

    # ── American League Central ───────────────────────────────────────────
    5:    _pf(),   # Progressive Field — CLE
    2394: _pf(),   # Comerica Park — DET
    7:    _pf(),   # Kauffman Stadium — KC
    3312: _pf(),   # Target Field — MIN
    4:    _pf(),   # Rate Field — CWS

    # ── American League West ──────────────────────────────────────────────
    2392: _pf(),   # Daikin Park — HOU
    1:    _pf(),   # Angel Stadium — LAA
    680:  _pf(),   # T-Mobile Park — SEA
    5325: _pf(),   # Globe Life Field — TEX
    2529: _pf(),   # Sutter Health Park — ATH (new park; may need window_years=1)

    # ── National League East ──────────────────────────────────────────────
    3289: _pf(),   # Citi Field — NYM
    2681: _pf(),   # Citizens Bank Park — PHI
    4705: _pf(),   # Truist Park — ATL
    3309: _pf(),   # Nationals Park — WSH
    4169: _pf(),   # loanDepot park — MIA

    # ── National League Central ───────────────────────────────────────────
    17:   _pf(),   # Wrigley Field — CHC
    2889: _pf(),   # Busch Stadium — STL
    32:   _pf(),   # American Family Field — MIL
    31:   _pf(),   # PNC Park — PIT
    2602: _pf(),   # Great American Ball Park — CIN

    # ── National League West ──────────────────────────────────────────────
    22:   _pf(),   # Dodger Stadium — LAD
    2680: _pf(),   # Petco Park — SD
    2395: _pf(),   # Oracle Park — SF
    15:   _pf(),   # Chase Field — ARI
    19:   _pf(),   # Coors Field — COL
}

# Columns refreshed on conflict: every factor field plus provenance. The keys
# (venue_id, season, window_years) and updated_at are intentionally excluded.
_FACTOR_COLUMNS = (*FACTOR_FIELDS, "source")


async def _venue_id_by_external_id(session: AsyncSession) -> dict[str, int]:
    """Build a map of MLB venue ``external_id`` (string) → ``venues.id`` (PK).

    Park factors are authored against MLBAM venue ids, but ``ParkFactor.venue_id``
    is a foreign key to the ``venues`` primary key, so we resolve the mapping
    from the already-seeded venues table.

    Args:
        session: Active async database session.

    Returns:
        dict[str, int]: external_id → venues.id for all MLB venues.
    """
    result = await session.execute(
        select(Venue.external_id, Venue.id).where(Venue.sport == Sport.MLB)
    )
    return {ext_id: vid for ext_id, vid in result.all()}


def _build_rows(
    venue_id_map: dict[str, int], season: int, window_years: int
) -> list[dict]:
    """Translate PARK_FACTORS (keyed by MLBAM id) into ParkFactor row payloads.

    Args:
        venue_id_map: external_id → venues.id map from :func:`_venue_id_by_external_id`.
        season: End year of the rolling window these factors apply to.
        window_years: Length of the rolling window in seasons.

    Returns:
        list[dict]: Insert-ready ParkFactor kwargs with resolved ``venue_id``.

    Raises:
        KeyError: If a PARK_FACTORS entry references an MLBAM venue id that has
            no seeded venue, so missing data is loud rather than silently dropped.
    """
    rows: list[dict] = []
    for mlbam_id, factors in PARK_FACTORS.items():
        external_id = str(mlbam_id)
        if external_id not in venue_id_map:
            raise KeyError(
                f"PARK_FACTORS venue {mlbam_id} has no seeded venue "
                f"(external_id={external_id!r}); seed venues first."
            )
        rows.append({
            "venue_id": venue_id_map[external_id],
            "season": season,
            "window_years": window_years,
            **factors,
        })
    return rows


async def seed_park_factors(
    session: AsyncSession,
    season: int = SEASON,
    window_years: int = WINDOW_YEARS,
) -> int:
    """Upsert MLB park factors for the given season and rolling window.

    Resolves each PARK_FACTORS entry's MLBAM venue id to a ``venues.id``, then
    performs an idempotent upsert keyed on the
    ``(venue_id, season, window_years)`` unique constraint so re-running
    refreshes factor values without creating duplicates.

    Args:
        session: Active async database session. Venues must already be seeded
            and flushed so their primary keys exist.
        season: End year of the window (defaults to :data:`SEASON`).
        window_years: Length of the rolling window (defaults to
            :data:`WINDOW_YEARS`).

    Returns:
        int: The number of park-factor rows upserted.
    """
    venue_id_map = await _venue_id_by_external_id(session)
    rows = _build_rows(venue_id_map, season, window_years)
    if not rows:
        return 0

    stmt = insert(ParkFactor).values(rows)
    stmt = stmt.on_conflict_do_update(
        constraint="uq_park_factors_venue_season_window",
        set_={col: getattr(stmt.excluded, col) for col in _FACTOR_COLUMNS},
    )
    await session.execute(stmt)
    return len(rows)
