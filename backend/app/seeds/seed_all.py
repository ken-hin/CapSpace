# backend/app/seeds/seed_all.py
"""Top-level database seeding entrypoint.

Run as a script (``python -m app.seeds.seed_all``) to populate the database with
reference data. It seeds venues first, flushes so they receive primary keys, then
seeds teams (which reference those venue ids), and commits everything in a single
transaction. Ordering matters because teams carry a ``home_venue_id`` foreign key.
"""

import asyncio
from app.db.session import async_session
from app.seeds.sports.mlb.seed_venues import seed_venues
from app.seeds.sports.mlb.seed_teams import seed_teams


async def main():
    """Seed venues then teams within one transaction and report the counts.

    Venues are flushed before teams are seeded so their database ids exist for
    the teams' ``home_venue_id`` foreign keys. Commits once at the end.
    """
    async with async_session() as session:
        venue_count = await seed_venues(session)
        await session.flush()  # venues get DB IDs assigned

        team_count = await seed_teams(session)

        await session.commit()

    print(f"Seeded {venue_count} venues, {team_count} teams")


if __name__ == "__main__":
    # Allow running this module directly as a one-off seeding script.
    asyncio.run(main())
