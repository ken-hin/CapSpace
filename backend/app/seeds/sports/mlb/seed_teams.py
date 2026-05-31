"""Seed all 30 MLB teams from the MLB Stats API.

Fetches the team list from the public MLB Stats API, maps each team to our
:class:`~app.models.team.Team` columns (resolving the home-venue foreign key
from previously-seeded venues and adding hardcoded brand colors the API omits),
and upserts on ``external_id``. Designed to run after :mod:`seed_venues`.
"""

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert
from app.models.team import Team
from app.models.venue import Venue
from app.models.enums import Sport

# Public MLB Stats API endpoint returning all MLB (sportId=1) teams.
MLB_API_TEAMS_URL = "https://statsapi.mlb.com/api/v1/teams?sportId=1"

# Hardcoded primary/secondary brand colors keyed by MLB Stats API team id
# (the API does not expose team colors). Comment marks each team's abbreviation.
TEAM_COLORS: dict[int, dict] = {
    108: {"primary": "#BA0021", "secondary": "#003263"},  # LAA
    109: {"primary": "#A71930", "secondary": "#E3D4AD"},  # ARI
    110: {"primary": "#DF4601", "secondary": "#000000"},  # BAL
    111: {"primary": "#BD3039", "secondary": "#0C2340"},  # BOS
    112: {"primary": "#CC3433", "secondary": "#0E3386"},  # CHC
    113: {"primary": "#C6011F", "secondary": "#000000"},  # CIN
    114: {"primary": "#C6011F", "secondary": "#000000"},  # CLE
    115: {"primary": "#33006F", "secondary": "#C4CED4"},  # COL
    116: {"primary": "#0C2340", "secondary": "#FA4616"},  # DET
    117: {"primary": "#002D62", "secondary": "#FF6600"},  # HOU
    118: {"primary": "#004687", "secondary": "#7AB2DD"},  # KC
    119: {"primary": "#005A9C", "secondary": "#A71930"},  # LAD
    120: {"primary": "#AB0003", "secondary": "#14225A"},  # WSH
    121: {"primary": "#FF5910", "secondary": "#002D72"},  # NYM
    133: {"primary": "#003831", "secondary": "#EFB21E"},  # OAK
    134: {"primary": "#27251F", "secondary": "#FDB827"},  # PIT
    135: {"primary": "#2F241D", "secondary": "#FFC425"},  # SD
    136: {"primary": "#0C2C56", "secondary": "#005C5C"},  # SEA
    137: {"primary": "#FD5A1E", "secondary": "#27251F"},  # SF
    138: {"primary": "#C41E3A", "secondary": "#0C2340"},  # STL
    139: {"primary": "#092C5C", "secondary": "#8FBCE6"},  # TB
    140: {"primary": "#003278", "secondary": "#C0111F"},  # TEX
    141: {"primary": "#134A8E", "secondary": "#1D2D5C"},  # TOR
    142: {"primary": "#002B5C", "secondary": "#D31145"},  # MIN
    143: {"primary": "#E81828", "secondary": "#002D72"},  # PHI
    144: {"primary": "#CE1141", "secondary": "#13274F"},  # ATL
    145: {"primary": "#27251F", "secondary": "#C4CED4"},  # CWS
    146: {"primary": "#00A3E0", "secondary": "#EF3340"},  # MIA
    147: {"primary": "#003087", "secondary": "#E4002C"},  # NYY
    158: {"primary": "#12284B", "secondary": "#FFC52F"},  # MIL
}


async def fetch_mlb_teams() -> list[dict]:
    """Fetch the raw team list from the MLB Stats API.

    Returns:
        list[dict]: The provider's raw team objects.

    Raises:
        httpx.HTTPStatusError: If the API responds with a non-2xx status.
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get(MLB_API_TEAMS_URL)
        resp.raise_for_status()
        return resp.json()["teams"]


def transform_team(raw: dict, venue_lookup: dict[str, int]) -> dict:
    """Map a raw MLB Stats API team object to ``Team`` model columns.

    Resolves the home-venue foreign key via ``venue_lookup``, attaches hardcoded
    brand colors, and normalizes league/division names to short codes.

    Args:
        raw: A single raw team object from the MLB Stats API.
        venue_lookup: Mapping of venue ``external_id`` (API id as str) to the
            seeded venue's database id.

    Returns:
        dict: Keyword arguments ready to insert/upsert as a ``Team`` row.
    """
    team_id = raw["id"]
    colors = TEAM_COLORS.get(team_id, {})
    venue_api_id = str(raw.get("venue", {}).get("id", ""))

    # Normalize league/division to short codes
    league_name = raw.get("league", {}).get("name", "")
    division_name = raw.get("division", {}).get("name", "")

    return {
        "external_id": str(team_id),
        "sport": Sport.MLB,
        "name": raw["name"],
        "abbreviation": raw["abbreviation"],
        "city": raw.get("locationName", ""),
        "founded_year": int(raw["firstYearOfPlay"]) if raw.get("firstYearOfPlay") else None,
        "league": "AL" if "American" in league_name else "NL" if "National" in league_name else None,
        "conference": None,
        "division": division_name.split()[-1] if division_name else None,  # "American League East" → "East"
        "primary_color": colors.get("primary"),
        "secondary_color": colors.get("secondary"),
        "home_venue_id": venue_lookup.get(venue_api_id),  # FK from venues seeded earlier
    }


async def seed_teams(session: AsyncSession) -> int:
    """Fetch teams from the MLB API, resolve venue FKs, and upsert them.

    Performs an idempotent upsert keyed on ``external_id`` so re-running refreshes
    mutable fields (name, colors, division, home venue) without creating
    duplicates.

    Args:
        session: Active async database session (venues must already be seeded).

    Returns:
        int: The number of team rows upserted.
    """
    # Build venue external_id → DB id lookup
    result = await session.execute(select(Venue.id, Venue.external_id))
    venue_lookup = {row.external_id: row.id for row in result}

    raw_teams = await fetch_mlb_teams()
    teams = [transform_team(t, venue_lookup) for t in raw_teams]

    stmt = insert(Team).values(teams)
    stmt = stmt.on_conflict_do_update(
        index_elements=["external_id"],
        set_={
            "name": stmt.excluded.name,
            "abbreviation": stmt.excluded.abbreviation,
            "city": stmt.excluded.city,
            "league": stmt.excluded.league,
            "division": stmt.excluded.division,
            "primary_color": stmt.excluded.primary_color,
            "secondary_color": stmt.excluded.secondary_color,
            "home_venue_id": stmt.excluded.home_venue_id,
        },
    )
    await session.execute(stmt)
    return len(teams)
