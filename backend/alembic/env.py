"""Alembic migration environment.

Bootstraps Alembic at migration time: puts the project root on ``sys.path``,
imports every ORM model so the full schema is registered on ``Base.metadata``
(the autogenerate target), and runs migrations in either offline (SQL emitting)
or online (async engine) mode. Invoked by the Alembic CLI, not imported by the app.
"""

import asyncio
import sys
from pathlib import Path
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Import every model module so their tables register with Base.metadata before
# autogenerate inspects it.  app.models.__init__ pulls in all sport-agnostic models;
# the sport-specific imports below add MLB (and future sports) to the same metadata.
import app.models  # noqa: F401 — registers all sport-agnostic tables
import app.sports.mlb.models  # noqa: F401 — registers MLB-specific tables

from app.models.base import Base  # noqa: F401

# Alembic Config object providing access to values in alembic.ini.
config = context.config
if config.config_file_name is not None:
    # Configure Python logging from the alembic.ini [logger_*] sections.
    fileConfig(config.config_file_name)

# Schema Alembic compares against when autogenerating migrations.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (emit SQL without a DB connection).

    Configures the context with just the database URL and renders migration
    statements as literal SQL, useful for generating migration scripts to run
    elsewhere.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    """Configure the context against a live connection and run the migrations.

    Args:
        connection: An open synchronous-style DB connection (provided by
            ``run_sync`` over the async connection).
    """
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create an async engine and run migrations within an async connection.

    Uses a ``NullPool`` (no connection pooling) since the engine is short-lived,
    and disposes of it when finished.
    """
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode by driving the async engine via asyncio."""
    asyncio.run(run_async_migrations())


# Entrypoint: choose offline (SQL script) or online (live connection) execution.
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
