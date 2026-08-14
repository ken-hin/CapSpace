"""Centralized application configuration.

Defines the :class:`Settings` model whose fields are populated from environment
variables (or a local ``.env`` file) via pydantic-settings, and exposes a
cached :func:`get_settings` accessor so the same immutable settings instance is
reused everywhere it is dependency-injected.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application configuration loaded from environment variables.

    Each attribute maps to an environment variable of the same name (case
    insensitive). Defaults are development-friendly; production deployments are
    expected to override secrets and connection strings via the environment.

    Attributes:
        APP_NAME: Human-readable service name shown in API docs and health checks.
        DEBUG: When true, enables dev conveniences such as auto-creating tables.
        DATABASE_URL: Async SQLAlchemy DSN for the PostgreSQL/TimescaleDB store.
        REDIS_URL: Connection URL for Redis (caching / pub-sub).
        CORS_ORIGINS: Allowed browser origins for cross-origin requests.
        SECRET_KEY: Signing key for JWT access tokens. MUST be overridden in prod.
        ALGORITHM: JWT signing algorithm.
        ACCESS_TOKEN_EXPIRE_MINUTES: Lifetime of issued access tokens, in minutes.
    """

    APP_NAME: str = "Sports Analytics Platform"
    DEBUG: bool = False

    # Database (Supabase PostgreSQL + TimescaleDB)
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/sports_analytics"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # CORS (SvelteKit frontend)
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    # JWT Auth
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Load environment variables from a local .env file when present.
    model_config = SettingsConfigDict(env_file=".env")


@lru_cache()
def get_settings() -> Settings:
    """Return the application settings as a process-wide singleton.

    The ``lru_cache`` decorator ensures the (relatively expensive) environment
    parsing happens once; every caller receives the same cached instance, which
    is important for consistency and makes the function safe to use as a FastAPI
    dependency.

    Returns:
        Settings: The cached, fully-populated settings object.
    """
    return Settings()
