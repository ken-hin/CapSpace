"""Seed 2025 MLB park factors, keyed by venue and season.

Park factors shift year-to-year (construction, humidors, environmental drift),
so they are stored per ``(venue_id, season)`` on the :class:`ParkFactor` table.
The hardcoded :data:`PARK_FACTORS` table below is keyed by **MLB Stats API venue
id** (the same integer keys used by ``VENUE_DETAILS`` in ``seed_venues.py``)
because that id is stable and easy to cross-check by hand.

At seed time those MLBAM ids are translated into real ``venues.id`` primary keys
by querying the already-seeded ``venues`` table, so this seeder MUST run after
venues have been seeded and flushed. Rows are upserted on the
``(venue_id, season)`` unique constraint, making the seeder safe to re-run.

Factors are on the standard 100 = league-average scale. ``factor_runs`` is the
single most-cited number; the rest refine it by hit type, handedness, and plate
discipline. Outfield dimensions are optional (nullable) and rarely change.

Numbers below are TEMPLATE values for three parks (Coors, Fenway, a neutral
park) proving the shape end-to-end. The remaining 27 venues are filled from
FanGraphs 2025 park factors in a follow-up pass (see seeding TODO step 5).
"""

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import Sport
from app.models.venue import Venue
from app.sports.mlb.models.park_factor import ParkFactor

SEASON = 2025

# Park factors keyed by MLB Stats API venue id (matches VENUE_DETAILS in
# seed_venues.py). All factors are on a 100 = league-average scale.
# Dimension keys (lf/cf/rf_distance_ft, lf/rf_wall_height_ft) are optional.
#
# TEMPLATE rows only — fill the remaining 27 venues from FanGraphs 2025.
PARK_FACTORS: dict[int, dict] = {
    # ── National League West ──────────────────────────────────────────────
    # Coors Field — COL (extreme hitter's park / altitude)
    19: {
        "factor_runs": 112.0,
        "factor_hr_vs_l": 108.0, "factor_hr_vs_r": 110.0,
        "factor_hits": 110.0, "factor_singles": 106.0,
        "factor_doubles": 113.0, "factor_triples": 134.0,
        "factor_bb": 100.0, "factor_so": 95.0,
        "lf_distance_ft": 347, "cf_distance_ft": 415, "rf_distance_ft": 350,
        "lf_wall_height_ft": 8, "rf_wall_height_ft": 14,
        "source": "fangraphs",
    },

    # ── American League East ──────────────────────────────────────────────
    # Fenway Park — BOS (high doubles via the Green Monster)
    3: {
        "factor_runs": 104.0,
        "factor_hr_vs_l": 97.0, "factor_hr_vs_r": 102.0,
        "factor_hits": 105.0, "factor_singles": 102.0,
        "factor_doubles": 118.0, "factor_triples": 110.0,
        "factor_bb": 100.0, "factor_so": 99.0,
        "lf_distance_ft": 310, "cf_distance_ft": 420, "rf_distance_ft": 302,
        "lf_wall_height_ft": 37, "rf_wall_height_ft": 5,
        "source": "fangraphs",
    },

    # ── American League West ──────────────────────────────────────────────
    # T-Mobile Park — SEA (roughly neutral / slight pitcher's park)
    680: {
        "factor_runs": 96.0,
        "factor_hr_vs_l": 95.0, "factor_hr_vs_r": 97.0,
        "factor_hits": 97.0, "factor_singles": 99.0,
        "factor_doubles": 95.0, "factor_triples": 98.0,
        "factor_bb": 100.0, "factor_so": 102.0,
        "lf_distance_ft": 331, "cf_distance_ft": 401, "rf_distance_ft": 326,
        "lf_wall_height_ft": 8, "rf_wall_height_ft": 8,
        "source": "fangraphs",
    },

    # TODO(step 5): add the remaining 27 venues from FanGraphs 2025. MLBAM ids
    # to fill (see VENUE_DETAILS in seed_venues.py for the name mapping):
    #   3313, 2, 14, 12, 5, 2394, 7, 3312, 4, 2392, 1, 5325, 2529,
    #   3289, 2681, 4705, 3309, 4169, 17, 2889, 32, 31, 2602, 22, 2680, 2395, 15
}

# Factor columns updated on conflict (everything except keys + provenance ts).
_FACTOR_COLUMNS = (
    "lf_distance_ft", "cf_distance_ft", "rf_distance_ft",
    "lf_wall_height_ft", "rf_wall_height_ft",
    "factor_runs", "factor_hr_vs_l", "factor_hr_vs_r",
    "factor_hits", "factor_singles", "factor_doubles", "factor_triples",
    "factor_bb", "factor_so", "source",
)


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


def _build_rows(venue_id_map: dict[str, int], season: int) -> list[dict]:
    """Translate PARK_FACTORS (keyed by MLBAM id) into ParkFactor row payloads.

    Args:
        venue_id_map: external_id → venues.id map from :func:`_venue_id_by_external_id`.
        season: The season these factors apply to.

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
            **factors,
        })
    return rows


async def seed_park_factors(session: AsyncSession, season: int = SEASON) -> int:
    """Upsert MLB park factors for the given season.

    Resolves each PARK_FACTORS entry's MLBAM venue id to a ``venues.id``, then
    performs an idempotent upsert keyed on the ``(venue_id, season)`` unique
    constraint so re-running refreshes factor values without creating duplicates.

    Args:
        session: Active async database session. Venues must already be seeded
            and flushed so their primary keys exist.
        season: Season the factors apply to (defaults to :data:`SEASON`).

    Returns:
        int: The number of park-factor rows upserted.
    """
    venue_id_map = await _venue_id_by_external_id(session)
    rows = _build_rows(venue_id_map, season)
    if not rows:
        return 0

    stmt = insert(ParkFactor).values(rows)
    stmt = stmt.on_conflict_do_update(
        constraint="uq_park_factors_venue_season",
        set_={col: getattr(stmt.excluded, col) for col in _FACTOR_COLUMNS},
    )
    await session.execute(stmt)
    return len(rows)
