"""
backend/config.py

Settings are loaded from the .env file via pydantic-settings.
All secrets (API keys, DB URLs) must live in .env — never hardcoded here.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ───────────────────────────────────────────────────────────────────
    app_name: str = "AI Finance Advisor"
    app_env: Literal["development", "production"] = "development"
    debug: bool = True
    secret_key: str = "change-me-to-a-256-bit-random-hex-string"
    allowed_origins: str = "http://localhost:3000,http://localhost:5173"

    # ── Database ──────────────────────────────────────────────────────────────
    # For local dev: sqlite+aiosqlite:///./finance_advisor.db
    # For Supabase:  postgresql+asyncpg://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres
    # Grab the connection string from Supabase dashboard → Settings → Database → URI
    database_url: str = "sqlite+aiosqlite:///./finance_advisor.db"

    # ── Supabase (optional — needed for auth/storage features) ────────────────
    # These are only used if you integrate the supabase-py client for auth/RLS.
    # For plain DB access via SQLAlchemy, just set database_url above.
    supabase_url: str = ""        # e.g. https://xyzxyz.supabase.co
    supabase_anon_key: str = ""   # The public anon key from Supabase dashboard

    # ── Gemini AI ─────────────────────────────────────────────────────────────
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    max_tokens: int = 1024
    temperature: float = 0.4

    # ── Derived ───────────────────────────────────────────────────────────────

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]

    @property
    def using_supabase(self) -> bool:
        """True when the DB URL points at Supabase Postgres (not local SQLite)."""
        return "supabase.co" in self.database_url

    @field_validator("temperature")
    @classmethod
    def _clamp_temp(cls, v: float) -> float:
        return max(0.0, min(v, 2.0))


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached settings singleton — safe to call anywhere including Depends()."""
    return Settings()
