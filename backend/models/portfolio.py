"""
backend/models/portfolio.py — Pydantic schemas for portfolios and holdings.
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

AssetType = Literal["equity", "debt", "gold", "real_estate", "fd", "crypto", "other"]


# ── Holding ───────────────────────────────────────────────────────────────────

class HoldingCreate(BaseModel):
    asset_type: AssetType
    symbol: str | None = None
    name: str = Field(..., min_length=1, max_length=255)
    quantity: float = Field(..., gt=0)
    avg_buy_price: float = Field(..., gt=0)
    current_price: float | None = Field(None, ge=0)
    buy_date: datetime | None = None


class HoldingRead(HoldingCreate):
    id: str
    portfolio_id: str
    created_at: datetime

    # Derived fields (computed in service layer)
    invested_value: float | None = None
    current_value: float | None = None
    gain_loss: float | None = None
    gain_loss_pct: float | None = None

    model_config = {"from_attributes": True}


# ── Portfolio ──────────────────────────────────────────────────────────────────

class PortfolioCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    holdings: list[HoldingCreate] = Field(default_factory=list)


class PortfolioRead(BaseModel):
    id: str
    user_id: str
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime
    holdings: list[HoldingRead] = Field(default_factory=list)

    # Aggregate stats
    total_invested: float | None = None
    current_value: float | None = None
    total_gain_loss: float | None = None
    total_gain_loss_pct: float | None = None
    asset_allocation: dict[str, float] | None = None  # {asset_type: pct}

    model_config = {"from_attributes": True}


# ── SIP Tracker ───────────────────────────────────────────────────────────────

class SIPCashflow(BaseModel):
    date: str      # ISO format YYYY-MM-DD
    amount: float  # negative = investment, positive = redemption


class SIPTrackerCreate(BaseModel):
    holding_id: str | None = None
    amount: float = Field(..., gt=0)
    frequency: Literal["monthly", "weekly"] = "monthly"
    start_date: datetime
    cashflows: list[SIPCashflow] | None = None


class SIPTrackerRead(SIPTrackerCreate):
    id: str
    user_id: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
