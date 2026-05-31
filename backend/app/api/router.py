"""Aggregate API router.

Combines the individual feature routers (players, games, predictions, stats)
into a single ``api_router`` mounted under the ``/api`` prefix. This is the
router that :mod:`app.main` includes on the FastAPI app, so adding a new
feature endpoint group only requires importing its router and registering it
here.
"""

from fastapi import APIRouter
from app.api import players, games, predictions, stats

# Root router for all versioned REST endpoints; each feature router is nested below.
api_router = APIRouter(prefix="/api")
api_router.include_router(players.router)
api_router.include_router(games.router)
api_router.include_router(predictions.router)
api_router.include_router(stats.router)
