"""Application entrypoint for the Sports Analytics Platform API.

Constructs and configures the FastAPI application: wires up the lifespan
handler (startup/shutdown), CORS middleware, the versioned REST API router,
and the WebSocket router for live stats. Exposes the ASGI ``app`` object that
the ASGI server (e.g. uvicorn) imports and serves, plus a simple ``/health``
endpoint for liveness checks.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.api.router import api_router
from app.websockets.live_stats import router as ws_router
from app.db.session import engine
from app.models.base import Base

# Cached application settings loaded once at import time.
settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown side effects.

    On startup (only when ``DEBUG`` is enabled) it auto-creates all database
    tables from the SQLAlchemy metadata, which is convenient for local
    development where migrations may not have been run. On shutdown it disposes
    of the async engine so pooled database connections are released cleanly.

    Args:
        app: The FastAPI application instance (required by the lifespan
            protocol; unused here).

    Yields:
        None: Control is yielded back to FastAPI while the app is running.
    """
    if settings.DEBUG:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()

app = FastAPI(title=settings.APP_NAME, lifespan=lifespan, docs_url="/docs", redoc_url="/redoc")
app.add_middleware(CORSMiddleware, allow_origins=settings.CORS_ORIGINS, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(api_router)
app.include_router(ws_router)

@app.get("/health")
async def health_check():
    """Liveness probe endpoint.

    Returns:
        dict: A small payload reporting service health and the app name,
        used by load balancers / uptime monitors to confirm the API is up.
    """
    return {"status": "healthy", "app": settings.APP_NAME}
