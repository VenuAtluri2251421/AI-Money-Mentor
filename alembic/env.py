"""
Alembic environment configuration.
Reads DATABASE_URL from environment to support both SQLite (dev) and PostgreSQL (prod).
"""
from __future__ import annotations

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# ── Alembic config object ──────────────────────────────────────────────────────
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import all models so Alembic can detect schema changes
from backend.db import Base  # noqa: E402
from backend.models import orm  # noqa: E402, F401

target_metadata = Base.metadata

# ── Override DB URL from .env ──────────────────────────────────────────────────
import os
from dotenv import load_dotenv

load_dotenv()

db_url = os.getenv("DATABASE_URL", config.get_main_option("sqlalchemy.url"))
# Alembic works with sync drivers; convert async URLs
sync_url = (
    db_url
    .replace("sqlite+aiosqlite", "sqlite")
    .replace("postgresql+asyncpg", "postgresql+psycopg2")
)
config.set_main_option("sqlalchemy.url", sync_url)


def run_migrations_offline() -> None:
    """Run migrations without a live DB connection (generates SQL only)."""
    context.configure(
        url=sync_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    from sqlalchemy.ext.asyncio import create_async_engine

    connectable = async_engine_from_config(
        {"sqlalchemy.url": db_url},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    from sqlalchemy import create_engine

    connectable = create_engine(sync_url, poolclass=pool.NullPool)
    with connectable.connect() as connection:
        do_run_migrations(connection)


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
