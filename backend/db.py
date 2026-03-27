"""
backend/db.py

Async SQLAlchemy engine + session wiring.

Works with both local SQLite (dev) and Supabase Postgres (prod).
For Supabase, set DATABASE_URL to the asyncpg URI from Supabase dashboard
→ Settings → Database → Connection string → URI (swap 'postgresql' with 'postgresql+asyncpg').

We deliberately keep the ORM thin here — business logic belongs in services,
not in the session lifecycle.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from backend.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# pool_pre_ping catches stale connections after Supabase's idle-timeout drops them.
# echo=True only in local dev — Supabase has its own query logging.
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True,
    pool_pre_ping=True,
    # Supabase Postgres works best with a small pool on the free tier (max 20 conns shared).
    pool_size=5 if settings.using_supabase else 10,
    max_overflow=5,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    """All ORM models inherit from this."""


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields an async session.

    Rolls back automatically on error so callers don't have to think about it.
    Usage: ``db: AsyncSession = Depends(get_db)``
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except SQLAlchemyError as exc:
            await session.rollback()
            logger.error("DB session error, rolled back: %s", exc)
            raise


async def init_db() -> None:
    """
    Create all tables at startup (dev/staging only).
    In production, prefer Alembic migrations over this — create_all is not safe
    once you have real data and schema changes that need ordering.

    TODO: Wire up Alembic before going to production on Supabase.
    """
    from backend.models import orm  # noqa: F401 — imports register ORM models with Base

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables initialised (engine: %s)", settings.database_url.split("://")[0])
    except OperationalError as exc:
        # Likely a bad DATABASE_URL or the Supabase project is paused.
        logger.error(
            "Failed to initialise DB — check DATABASE_URL and Supabase project status: %s", exc
        )
        raise


async def close_db() -> None:
    """Dispose connection pool on app shutdown."""
    await engine.dispose()
    logger.info("DB connection pool disposed.")


@asynccontextmanager
async def db_context():
    """Context manager for scripts / background tasks that run outside FastAPI."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except SQLAlchemyError as exc:
            await session.rollback()
            logger.error("Script DB error, rolled back: %s", exc)
            raise
