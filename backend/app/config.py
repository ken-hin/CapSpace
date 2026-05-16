from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

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

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
