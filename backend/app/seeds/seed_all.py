# backend/app/seeds/seed_all.py

import asyncio
from app.db.session import async_session
from app.seeds.sports.mlb.seed_venues import seed_venues
from app.seeds.sports.mlb.seed_teams import seed_teams


async def main():
    async with async_session() as session:
        venue_count = await seed_venues(session)
        await session.flush()  # venues get DB IDs assigned

        team_count = await seed_teams(session)

        await session.commit()

    print(f"Seeded {venue_count} venues, {team_count} teams")


if __name__ == "__main__":
    asyncio.run(main())
