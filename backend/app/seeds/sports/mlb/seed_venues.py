"""Seed all 30 MLB venues from the MLB Stats API + hardcoded analytics fields.

Venue identity/location comes from the MLB Stats API (hydrated onto the teams
endpoint), while analytics-critical attributes the API doesn't provide
(capacity, surface, roof type, elevation, timezone, coordinates) are supplied by
the hardcoded :data:`VENUE_DETAILS` table keyed by MLB Stats API venue id. Rows
are upserted on ``external_id`` so the seeder is safe to re-run.
"""

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert
from app.models.venue import Venue
from app.models.enums import Sport

MLB_API_TEAMS_URL = "https://statsapi.mlb.com/api/v1/teams?sportId=1&hydrate=venue"

# Analytics-critical fields the API doesn't provide, keyed by MLB Stats API venue ID.
# TODO: Capacity/elevation/coords are approximate and should be refined
#       from a source like Ballparks of Baseball or Wikipedia.
# TODO: Add city and state info for each item in VENUE_DETAILS
VENUE_DETAILS: dict[int, dict] = {
    # ── American League East ──────────────────────────────────────────────
    # Yankee Stadium — NYY
    3313: {
        "capacity": 46537, "surface": "grass", "roof_type": "open",
        "elevation_ft": 17, "timezone": "America/New_York",
        "lat": 40.829, "lon": -73.926,
    },
    # Fenway Park — BOS
    3: {
        "capacity": 37755, "surface": "grass", "roof_type": "open",
        "elevation_ft": 20, "timezone": "America/New_York",
        "lat": 42.346, "lon": -71.098,
    },
    # Oriole Park at Camden Yards — BAL
    2: {
        "capacity": 45971, "surface": "grass", "roof_type": "open",
        "elevation_ft": 30, "timezone": "America/New_York",
        "lat": 39.284, "lon": -76.622,
    },
    # Rogers Centre — TOR
    14: {
        "capacity": 49282, "surface": "turf", "roof_type": "retractable",
        "elevation_ft": 266, "timezone": "America/Toronto",
        "lat": 43.641, "lon": -79.389,
    },
    # Tropicana Field — TB
    12: {
        "capacity": 25000, "surface": "turf", "roof_type": "fixed",
        "elevation_ft": 45, "timezone": "America/New_York",
        "lat": 27.768, "lon": -82.653,
    },

    # ── American League Central ───────────────────────────────────────────
    # Progressive Field — CLE
    5: {
        "capacity": 34788, "surface": "grass", "roof_type": "open",
        "elevation_ft": 653, "timezone": "America/New_York",
        "lat": 41.496, "lon": -81.685,
    },
    # Comerica Park — DET
    2394: {
        "capacity": 41083, "surface": "grass", "roof_type": "open",
        "elevation_ft": 600, "timezone": "America/Detroit",
        "lat": 42.339, "lon": -83.049,
    },
    # Kauffman Stadium — KC
    7: {
        "capacity": 37903, "surface": "grass", "roof_type": "open",
        "elevation_ft": 820, "timezone": "America/Chicago",
        "lat": 39.051, "lon": -94.480,
    },
    # Target Field — MIN
    3312: {
        "capacity": 38544, "surface": "grass", "roof_type": "open",
        "elevation_ft": 841, "timezone": "America/Chicago",
        "lat": 44.982, "lon": -93.278,
    },
    # Guaranteed Rate Field — CWS
    4: {
        "capacity": 40615, "surface": "grass", "roof_type": "open",
        "elevation_ft": 595, "timezone": "America/Chicago",
        "lat": 41.830, "lon": -87.634,
    },

    # ── American League West ──────────────────────────────────────────────
    # Daikin Park — HOU
    2392: {
        "capacity": 41168, "surface": "turf", "roof_type": "retractable",
        "elevation_ft": 42, "timezone": "America/Chicago",
        "lat": 29.757, "lon": -95.355,
    },
    # Angel Stadium — LAA
    1: {
        "capacity": 45517, "surface": "grass", "roof_type": "open",
        "elevation_ft": 160, "timezone": "America/Los_Angeles",
        "lat": 33.800, "lon": -117.883,
    },
    # T-Mobile Park — SEA
    680: {
        "capacity": 47929, "surface": "turf", "roof_type": "retractable",
        "elevation_ft": 22, "timezone": "America/Los_Angeles",
        "lat": 47.591, "lon": -122.332,
    },
    # Globe Life Field — TEX
    5325: {
        "capacity": 40300, "surface": "turf", "roof_type": "retractable",
        "elevation_ft": 551, "timezone": "America/Chicago",
        "lat": 32.747, "lon": -97.084,
    },
    # Sutter Health Park — OAK (verify — A's relocating)
    2529: {
        "capacity": 46847, "surface": "grass", "roof_type": "open",
        "elevation_ft": 3, "timezone": "America/Los_Angeles",
        "lat": 37.751, "lon": -122.201,
    },

    # ── National League East ──────────────────────────────────────────────
    # Citi Field — NYM
    3289: {
        "capacity": 41922, "surface": "grass", "roof_type": "open",
        "elevation_ft": 12, "timezone": "America/New_York",
        "lat": 40.757, "lon": -73.846,
    },
    # Citizens Bank Park — PHI
    2681: {
        "capacity": 42792, "surface": "grass", "roof_type": "open",
        "elevation_ft": 20, "timezone": "America/New_York",
        "lat": 39.906, "lon": -75.167,
    },
    # Truist Park — ATL
    4705: {
        "capacity": 41084, "surface": "grass", "roof_type": "open",
        "elevation_ft": 1050, "timezone": "America/New_York",
        "lat": 33.891, "lon": -84.468,
    },
    # Nationals Park — WSH
    3309: {
        "capacity": 41339, "surface": "grass", "roof_type": "open",
        "elevation_ft": 25, "timezone": "America/New_York",
        "lat": 38.873, "lon": -77.007,
    },
    # loanDepot Park — MIA
    4169: {
        "capacity": 36742, "surface": "grass", "roof_type": "retractable",
        "elevation_ft": 7, "timezone": "America/New_York",
        "lat": 25.778, "lon": -80.220,
    },

    # ── National League Central ───────────────────────────────────────────
    # Wrigley Field — CHC
    17: {
        "capacity": 41649, "surface": "grass", "roof_type": "open",
        "elevation_ft": 600, "timezone": "America/Chicago",
        "lat": 41.948, "lon": -87.656,
    },
    # Busch Stadium — STL
    2889: {
        "capacity": 45494, "surface": "grass", "roof_type": "open",
        "elevation_ft": 455, "timezone": "America/Chicago",
        "lat": 38.623, "lon": -90.193,
    },
    # American Family Field — MIL
    32: {
        "capacity": 41900, "surface": "grass", "roof_type": "retractable",
        "elevation_ft": 635, "timezone": "America/Chicago",
        "lat": 43.028, "lon": -87.971,
    },
    # PNC Park — PIT
    31: {
        "capacity": 38362, "surface": "grass", "roof_type": "open",
        "elevation_ft": 730, "timezone": "America/New_York",
        "lat": 40.447, "lon": -80.006,
    },
    # Great American Ball Park — CIN
    2602: {
        "capacity": 42319, "surface": "grass", "roof_type": "open",
        "elevation_ft": 490, "timezone": "America/New_York",
        "lat": 39.097, "lon": -84.508,
    },

    # ── National League West ──────────────────────────────────────────────
    # UNIQLO Field at Dodger Stadium — LAD
    22: {
        "capacity": 56000, "surface": "grass", "roof_type": "open",
        "elevation_ft": 515, "timezone": "America/Los_Angeles",
        "lat": 34.074, "lon": -118.240,
    },
    # Petco Park — SD
    2680: {
        "capacity": 40209, "surface": "grass", "roof_type": "open",
        "elevation_ft": 13, "timezone": "America/Los_Angeles",
        "lat": 32.707, "lon": -117.157,
    },
    # Oracle Park — SF
    2395: {
        "capacity": 41265, "surface": "grass", "roof_type": "open",
        "elevation_ft": 4, "timezone": "America/Los_Angeles",
        "lat": 37.778, "lon": -122.389,
    },
    # Chase Field — ARI
    15: {
        "capacity": 48519, "surface": "turf", "roof_type": "retractable",
        "elevation_ft": 1082, "timezone": "America/Phoenix",
        "lat": 33.445, "lon": -112.067,
    },
    # Coors Field — COL
    19: {
        "capacity": 50144, "surface": "grass", "roof_type": "open",
        "elevation_ft": 5200, "timezone": "America/Denver",
        "lat": 39.756, "lon": -104.994,
    },
}


async def fetch_venues_from_api() -> list[dict]:
    """Pull deduplicated venue info embedded in the teams endpoint.

    The MLB Stats API exposes venue data hydrated onto each team; this collects
    unique venues across all teams.

    Returns:
        list[dict]: One dict per distinct venue with ``api_id``, name, and location.

    Raises:
        httpx.HTTPStatusError: If the API responds with a non-2xx status.
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get(MLB_API_TEAMS_URL)
        resp.raise_for_status()
        teams = resp.json()["teams"]

    venues = []
    seen_ids: set[int] = set()
    for team in teams:
        v = team.get("venue", {})
        vid = v.get("id")
        if vid and vid not in seen_ids:
            seen_ids.add(vid)
            loc = v.get("location", {})
            venues.append({
                "api_id": vid,
                "name": v.get("name"),
                "city": loc.get("city", ""),
                "state": loc.get("stateAbbrev"),
                "country": loc.get("country", "USA"),
            })
    return venues


def transform_venue(raw: dict) -> dict:
    """Merge API venue data with hardcoded analytics fields into model columns.

    Args:
        raw: A venue dict from :func:`fetch_venues_from_api` (must include ``api_id``).

    Returns:
        dict: Keyword arguments ready to insert/upsert as a ``Venue`` row; the
        analytics fields fall back to ``None``/defaults when the venue id is not
        present in ``VENUE_DETAILS``.
    """
    vid = raw["api_id"]
    details = VENUE_DETAILS.get(vid, {})

    return {
        "external_id": str(vid),
        "sport": Sport.MLB,
        "name": raw["name"],
        "city": raw["city"],
        "state": raw["state"],
        "country": raw["country"],
        "capacity": details.get("capacity"),
        "surface": details.get("surface"),
        "roof_type": details.get("roof_type"),
        "elevation_ft": details.get("elevation_ft"),
        "timezone": details.get("timezone", "America/New_York"),
        "latitude": details.get("lat"),
        "longitude": details.get("lon"),
        "is_active": True,
    }


async def seed_venues(session: AsyncSession) -> int:
    """Fetch venues from the MLB API, enrich with analytics fields, and upsert.

    Performs an idempotent upsert keyed on ``external_id`` so re-running refreshes
    mutable fields without creating duplicates.

    Args:
        session: Active async database session.

    Returns:
        int: The number of venue rows upserted.
    """
    raw = await fetch_venues_from_api()
    venues = [transform_venue(v) for v in raw]

    stmt = insert(Venue).values(venues)
    stmt = stmt.on_conflict_do_update(
        index_elements=["external_id"],
        set_={
            "name": stmt.excluded.name,
            "city": stmt.excluded.city,
            "state": stmt.excluded.state,
            "capacity": stmt.excluded.capacity,
            "surface": stmt.excluded.surface,
            "roof_type": stmt.excluded.roof_type,
            "elevation_ft": stmt.excluded.elevation_ft,
            "timezone": stmt.excluded.timezone,
            "latitude": stmt.excluded.latitude,
            "longitude": stmt.excluded.longitude,
        },
    )
    await session.execute(stmt)
    return len(venues)
