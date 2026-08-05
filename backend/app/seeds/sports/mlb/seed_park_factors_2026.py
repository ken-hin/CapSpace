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
		# Yankee Stadium — NYY
    3313: _pf(
	    factor_overall=101,   factor_runs=106,
	    factor_hr_vs_l=113,   factor_hr_vs_r=121,
	    factor_hits=95,       factor_xwobacon=103,
	    factor_obp=101,       factor_hardhit=106,
	    factor_bb=117,        factor_so=102,
	    pa=46751,
    ),
		# Fenway Park — BOS
    3:    _pf(
	    factor_overall=102,   factor_runs=104,
	    factor_hr_vs_l=81,    factor_hr_vs_r=87,
	    factor_hits=104,      factor_xwobacon=99,
	    factor_obp=104,       factor_hardhit=100,
	    factor_bb=98,         factor_so=98,
	    pa=44597,
    ),
		# Oriole Park at Camden Yards — BAL
    2:    _pf(
	    factor_overall=103,   factor_runs=106,
	    factor_hr_vs_l=123,   factor_hr_vs_r=97,
	    factor_hits=105,      factor_xwobacon=102,
	    factor_obp=101,       factor_hardhit=104,
	    factor_bb=93,         factor_so=99,
	    pa=45371,
    ),
		# Rogers Centre — TOR
    14:   _pf(
	    factor_overall=101,   factor_runs=102,
	    factor_hr_vs_l=107,   factor_hr_vs_r=111,
	    factor_hits=102,      factor_xwobacon=101,
	    factor_obp=100,       factor_hardhit=100,
	    factor_bb=98,         factor_so=97,
	    pa=46116,
    ),
		# Tropicana Field — TB
    12:   _pf(
	    factor_overall=97,    factor_runs=94,
	    factor_hr_vs_l=84,    factor_hr_vs_r=112,
	    factor_hits=97,       factor_xwobacon=99,
	    factor_obp=97,        factor_hardhit=92,
	    factor_bb=97,         factor_so=102,
	    pa=25129,
    ),

    # ── American League Central ───────────────────────────────────────────
		# Progressive Field — CLE
    5:    _pf(
      factor_overall=98,    factor_runs=96,
	    factor_hr_vs_l=103,   factor_hr_vs_r=83,
	    factor_hits=98,       factor_xwobacon=99,
	    factor_obp=99,        factor_hardhit=97,
	    factor_bb=102,        factor_so=105,
	    pa=43703,
    ),
		# Comerica Park — DET
    2394: _pf(
      factor_overall=100,   factor_runs=100,
	    factor_hr_vs_l=99,    factor_hr_vs_r=103,
	    factor_hits=100,      factor_xwobacon=98,
	    factor_obp=100,       factor_hardhit=98,
	    factor_bb=99,         factor_so=99,
	    pa=43338,
    ),
		# Kauffman Stadium — KC
    7:    _pf(
      factor_overall=100,   factor_runs=100,
	    factor_hr_vs_l=75,    factor_hr_vs_r=89,
	    factor_hits=103,      factor_xwobacon=101,
	    factor_obp=101,       factor_hardhit=104,
	    factor_bb=99,         factor_so=91,
	    pa=43242,
    ),
		# Target Field — MIN
    3312: _pf(
      factor_overall=103,   factor_runs=96,
	    factor_hr_vs_l=96,    factor_hr_vs_r=97,
	    factor_hits=104,      factor_xwobacon=100,
	    factor_obp=104,       factor_hardhit=99,
	    factor_bb=99,         factor_so=97,
	    pa=44997,
    ),
		# Rate Field — CWS
    4:    _pf(
      factor_overall=99,    factor_runs=98,
	    factor_hr_vs_l=105,   factor_hr_vs_r=90,
	    factor_hits=97,       factor_xwobacon=98,
	    factor_obp=99,        factor_hardhit=97,
	    factor_bb=103,        factor_so=97,
	    pa=44300,
    ),

    # ── American League West ──────────────────────────────────────────────
    # Daikin Park — HOU
    2392: _pf(
      factor_overall=101,   factor_runs=102,
	    factor_hr_vs_l= 123,  factor_hr_vs_r=111,
	    factor_hits=100,      factor_xwobacon=99,
	    factor_obp=100,       factor_hardhit=99,
	    factor_bb=102,        factor_so=106,
	    pa=43847,
    ),
    # Angel Stadium — LAA
    1:    _pf(
      factor_overall=101,   factor_runs=102,
	    factor_hr_vs_l=98,    factor_hr_vs_r=113,
	    factor_hits=99,       factor_xwobacon=99,
	    factor_obp=100,       factor_hardhit=99,
	    factor_bb=100,        factor_so=105,
	    pa=43428,
    ),
    # T-Mobile Park — SEA
    680:  _pf(
      factor_overall=92,    factor_runs=85,
	    factor_hr_vs_l=97,    factor_hr_vs_r=98,
	    factor_hits=90,       factor_xwobacon=101,
	    factor_obp=92,        factor_hardhit=99,
	    factor_bb=95,         factor_so=117,
	    pa=43896,
    ),
    # Globe Life Field — TEX
    5325: _pf(
      factor_overall=92,    factor_runs=85,
	    factor_hr_vs_l=95,    factor_hr_vs_r=87,
	    factor_hits=92,       factor_xwobacon=98,
	    factor_obp=93,        factor_hardhit=100,
	    factor_bb=95,         factor_so=102,
	    pa=43159,
    ),
    # Sutter Health Park — ATH (new park; may need window_years=1)
    2529: _pf(
      factor_overall=0,   factor_runs=0,
	    factor_hr_vs_l=0,   factor_hr_vs_r=0,
	    factor_hits=0,      factor_xwobacon=0,
	    factor_obp=0,       factor_hardhit=0,
	    factor_bb=0,        factor_so=0,
	    pa=0,
    ),

    # ── National League East ──────────────────────────────────────────────
    # Citi Field — NYM
    3289: _pf(
      factor_overall=99,    factor_runs=98,
	    factor_hr_vs_l=96,    factor_hr_vs_r=107,
	    factor_hits=96,       factor_xwobacon=101,
	    factor_obp=100,       factor_hardhit=102,
	    factor_bb=108,        factor_so=103,
	    pa=45758,
    ),
    # Citizens Bank Park — PHI
    2681: _pf(
      factor_overall=102,   factor_runs=104,
	    factor_hr_vs_l=130,   factor_hr_vs_r=100,
	    factor_hits=102,      factor_xwobacon=98,
	    factor_obp=100,       factor_hardhit=99,
	    factor_bb=96,         factor_so=103,
	    pa=44713,
    ),
    # Truist Park — ATL
    4705: _pf(
      factor_overall=99,    factor_runs=98,
	    factor_hr_vs_l=97,    factor_hr_vs_r=91,
	    factor_hits=101,      factor_xwobacon=101,
	    factor_obp=100,       factor_hardhit=100,
	    factor_bb=99,         factor_so=104,
	    pa=44042,
    ),
    # Nationals Park — WSH
    3309: _pf(
      factor_overall=102,   factor_runs=104,
	    factor_hr_vs_l=103,   factor_hr_vs_r=97,
	    factor_hits=103,      factor_xwobacon=102,
	    factor_obp=102,       factor_hardhit=103,
	    factor_bb=96,         factor_so=94,
	    pa=44136,
    ),
    # loanDepot park — MIA
    4169: _pf(
      factor_overall=100,   factor_runs=100,
	    factor_hr_vs_l=94,    factor_hr_vs_r=81,
	    factor_hits=101,      factor_xwobacon=99,
	    factor_obp=101,       factor_hardhit=101,
	    factor_bb=100,        factor_so=97,
	    pa=45451,
    ),

    # ── National League Central ───────────────────────────────────────────
    # Wrigley Field — CHC
    17:   _pf(
      factor_overall=95,    factor_runs=90,
	    factor_hr_vs_l=97,    factor_hr_vs_r=101,
	    factor_hits=94,       factor_xwobacon=99,
	    factor_obp=96,        factor_hardhit=101,
	    factor_bb=101,        factor_so=103,
	    pa=45030,
    ),
    # Busch Stadium — STL
    2889: _pf(
      factor_overall=98,    factor_runs=96,
	    factor_hr_vs_l=79,    factor_hr_vs_r=80,
	    factor_hits=103,      factor_xwobacon=99,
	    factor_obp=100,       factor_hardhit=102,
	    factor_bb=92,         factor_so=90,
	    pa=43238,
    ),
    # American Family Field — MIL
    32:   _pf(
      factor_overall=97,    factor_runs=94,
	    factor_hr_vs_l=94,    factor_hr_vs_r=109,
	    factor_hits=95,       factor_xwobacon=98,
	    factor_obp=98,        factor_hardhit=96,
	    factor_bb=105,        factor_so=110,
	    pa=45680,
    ),
    # PNC Park — PIT
    31:   _pf(
      factor_overall=100,   factor_runs=100,
	    factor_hr_vs_l=96,    factor_hr_vs_r=70,
	    factor_hits=102,      factor_xwobacon=101,
	    factor_obp=102,       factor_hardhit=102,
	    factor_bb=99,         factor_so=98,
	    pa=44874,
    ),
    # Great American Ball Park — CIN
    2602: _pf(
      factor_overall=103,   factor_runs=106,
	    factor_hr_vs_l=129,   factor_hr_vs_r=119,
	    factor_hits=100,      factor_xwobacon=101,
	    factor_obp=101,       factor_hardhit=96,
	    factor_bb=96,         factor_so=107,
	    pa=43772,
    ),

    # ── National League West ──────────────────────────────────────────────
    # Dodger Stadium — LAD
    22:   _pf(
      factor_overall=101,   factor_runs=102,
	    factor_hr_vs_l=123,   factor_hr_vs_r=135,
	    factor_hits=97,       factor_xwobacon=103,
	    factor_obp=99,        factor_hardhit=101,
	    factor_bb=102,        factor_so=101,
	    pa=46943,
    ),
    # Petco Park — SD
    2680: _pf(
      factor_overall=97,    factor_runs=94,
	    factor_hr_vs_l=96,    factor_hr_vs_r=116,
	    factor_hits=95,       factor_xwobacon=101,
	    factor_obp=96,        factor_hardhit=99,
	    factor_bb=101,        factor_so=103,
	    pa=44563,
    ),
    # Oracle Park — SF
    2395: _pf(
      factor_overall=98,    factor_runs=96,
	    factor_hr_vs_l=73,    factor_hr_vs_r=82,
	    factor_hits=101,      factor_xwobacon=97,
	    factor_obp=99,        factor_hardhit=97,
	    factor_bb=93,         factor_so=97,
	    pa=43309,
    ),
    # Chase Field — ARI
    15:   _pf(
      factor_overall=104,   factor_runs=108,
	    factor_hr_vs_l=76,    factor_hr_vs_r=106,
	    factor_hits=105,      factor_xwobacon=102,
	    factor_obp=103,       factor_hardhit=102,
	    factor_bb=98,         factor_so=90,
	    pa=44411,
    ),
    # Coors Field — COL
    19:   _pf(
      factor_overall=112,   factor_runs=125,
	    factor_hr_vs_l=114,   factor_hr_vs_r=100,
	    factor_hits=118,      factor_xwobacon=101,
	    factor_obp=111,       factor_hardhit=101,
	    factor_bb=100,        factor_so=90,
	    pa=44542,
    ),
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
