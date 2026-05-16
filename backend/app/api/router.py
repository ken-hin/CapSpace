from fastapi import APIRouter
from app.api import players, games, predictions, stats

api_router = APIRouter(prefix="/api")
api_router.include_router(players.router)
api_router.include_router(games.router)
api_router.include_router(predictions.router)
api_router.include_router(stats.router)
