"""
backend/models/orm.py — SQLAlchemy ORM table definitions.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> str:
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------

class UserORM(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    profile: Mapped["UserProfileORM | None"] = relationship(
        "UserProfileORM", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    portfolios: Mapped[list["PortfolioORM"]] = relationship(
        "PortfolioORM", back_populates="user", cascade="all, delete-orphan"
    )
    advisor_chats: Mapped[list["AdvisorChatORM"]] = relationship(
        "AdvisorChatORM", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User id={self.id} email={self.email}>"


# ---------------------------------------------------------------------------
# User Profile (financial snapshot)
# ---------------------------------------------------------------------------

class UserProfileORM(Base):
    __tablename__ = "user_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)

    # Personal
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    risk_profile: Mapped[str | None] = mapped_column(String(20), nullable=True)  # conservative/moderate/aggressive

    # Income & expenses (monthly, ₹)
    monthly_income: Mapped[float | None] = mapped_column(Float, nullable=True)
    monthly_expenses: Mapped[float | None] = mapped_column(Float, nullable=True)
    monthly_fixed_expenses: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_emi: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Goals
    retirement_age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fire_target: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Emergency & insurance
    emergency_fund: Mapped[float | None] = mapped_column(Float, nullable=True)
    life_cover: Mapped[float | None] = mapped_column(Float, nullable=True)
    health_cover: Mapped[float | None] = mapped_column(Float, nullable=True)

    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    user: Mapped["UserORM"] = relationship("UserORM", back_populates="profile")


# ---------------------------------------------------------------------------
# Portfolio (holdings)
# ---------------------------------------------------------------------------

class PortfolioORM(Base):
    __tablename__ = "portfolios"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    user: Mapped["UserORM"] = relationship("UserORM", back_populates="portfolios")
    holdings: Mapped[list["HoldingORM"]] = relationship(
        "HoldingORM", back_populates="portfolio", cascade="all, delete-orphan"
    )


class HoldingORM(Base):
    __tablename__ = "holdings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    portfolio_id: Mapped[str] = mapped_column(ForeignKey("portfolios.id", ondelete="CASCADE"))

    # Asset details
    asset_type: Mapped[str] = mapped_column(String(50), nullable=False)  # equity/debt/gold/real_estate/fd/crypto
    symbol: Mapped[str | None] = mapped_column(String(50), nullable=True)   # ISIN, ticker, or fund code
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    avg_buy_price: Mapped[float] = mapped_column(Float, nullable=False)
    current_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    buy_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    portfolio: Mapped["PortfolioORM"] = relationship("PortfolioORM", back_populates="holdings")


# ---------------------------------------------------------------------------
# SIP Tracker
# ---------------------------------------------------------------------------

class SIPTrackerORM(Base):
    __tablename__ = "sip_trackers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    holding_id: Mapped[str | None] = mapped_column(ForeignKey("holdings.id", ondelete="SET NULL"), nullable=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    frequency: Mapped[str] = mapped_column(String(20), default="monthly")  # monthly/weekly
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    cashflows: Mapped[list | None] = mapped_column(JSON, nullable=True)   # [{date, amount}]

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


# ---------------------------------------------------------------------------
# Advisor Chat Log
# ---------------------------------------------------------------------------

class AdvisorChatORM(Base):
    __tablename__ = "advisor_chats"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    role: Mapped[str] = mapped_column(String(20), nullable=False)   # user / assistant
    content: Mapped[str] = mapped_column(Text, nullable=False)
    context_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    user: Mapped["UserORM"] = relationship("UserORM", back_populates="advisor_chats")
