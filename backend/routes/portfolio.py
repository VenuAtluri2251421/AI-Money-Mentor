"""
backend/routes/portfolio.py — Portfolio, Holding, and SIP Tracker CRUD (protected).

All queries are ownership-scoped: they filter by the JWT user's ID and return 404
if the resource belongs to a different user (never leaks the existence of others' data).
"""
from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.db import get_db
from backend.models.orm import HoldingORM, PortfolioORM, SIPTrackerORM, UserORM
from backend.models.portfolio import (
    HoldingCreate,
    HoldingRead,
    PortfolioCreate,
    PortfolioRead,
    SIPTrackerCreate,
    SIPTrackerRead,
)
from backend.security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Portfolio & Holdings"])


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _get_user_portfolio(
    portfolio_id: str, user_id: str, db: AsyncSession
) -> PortfolioORM:
    """Fetch a portfolio only if it belongs to the requesting user."""
    result = await db.execute(
        select(PortfolioORM)
        .options(selectinload(PortfolioORM.holdings))
        .where(PortfolioORM.id == portfolio_id, PortfolioORM.user_id == user_id)
    )
    portfolio = result.scalar_one_or_none()
    if not portfolio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found")
    return portfolio


def _enrich_holding(h: HoldingORM) -> HoldingRead:
    """Compute derived fields (invested_value, current_value, gain/loss)."""
    invested = h.quantity * h.avg_buy_price
    current = h.quantity * h.current_price if h.current_price is not None else None
    gain = (current - invested) if current is not None else None
    gain_pct = (gain / invested * 100) if gain is not None and invested > 0 else None

    read = HoldingRead.model_validate(h)
    read.invested_value = round(invested, 2)
    read.current_value = round(current, 2) if current is not None else None
    read.gain_loss = round(gain, 2) if gain is not None else None
    read.gain_loss_pct = round(gain_pct, 2) if gain_pct is not None else None
    return read


def _enrich_portfolio(p: PortfolioORM) -> PortfolioRead:
    """Compute aggregate stats for a portfolio."""
    holdings = [_enrich_holding(h) for h in p.holdings]

    total_invested = sum(h.invested_value or 0 for h in holdings)
    current_value = sum(h.current_value or 0 for h in holdings) if any(h.current_value for h in holdings) else None
    total_gl = (current_value - total_invested) if current_value is not None else None
    total_gl_pct = (total_gl / total_invested * 100) if total_gl is not None and total_invested > 0 else None

    # Asset allocation by type
    allocation: dict[str, float] = {}
    if current_value and current_value > 0:
        for h in holdings:
            if h.current_value:
                allocation[h.asset_type] = allocation.get(h.asset_type, 0) + h.current_value
        allocation = {k: round(v / current_value * 100, 1) for k, v in allocation.items()}

    read = PortfolioRead.model_validate(p)
    read.holdings = holdings
    read.total_invested = round(total_invested, 2) if total_invested else None
    read.current_value = round(current_value, 2) if current_value is not None else None
    read.total_gain_loss = round(total_gl, 2) if total_gl is not None else None
    read.total_gain_loss_pct = round(total_gl_pct, 2) if total_gl_pct is not None else None
    read.asset_allocation = allocation or None
    return read


# ── Portfolio CRUD ────────────────────────────────────────────────────────────

@router.post(
    "/portfolios",
    response_model=PortfolioRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a portfolio with optional holdings",
)
async def create_portfolio(
    body: PortfolioCreate,
    current_user: Annotated[UserORM, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PortfolioRead:
    portfolio = PortfolioORM(
        user_id=current_user.id,
        name=body.name,
        description=body.description,
    )
    db.add(portfolio)
    await db.flush()

    for h in body.holdings:
        holding = HoldingORM(portfolio_id=portfolio.id, **h.model_dump())
        db.add(holding)

    await db.flush()
    await db.refresh(portfolio)
    # Reload with holdings
    portfolio = await _get_user_portfolio(portfolio.id, current_user.id, db)
    return _enrich_portfolio(portfolio)


@router.get(
    "/portfolios",
    response_model=list[PortfolioRead],
    summary="List your portfolios",
)
async def list_portfolios(
    current_user: Annotated[UserORM, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[PortfolioRead]:
    result = await db.execute(
        select(PortfolioORM)
        .options(selectinload(PortfolioORM.holdings))
        .where(PortfolioORM.user_id == current_user.id)
        .order_by(PortfolioORM.created_at.desc())
    )
    portfolios = result.scalars().all()
    return [_enrich_portfolio(p) for p in portfolios]


@router.get(
    "/portfolios/{portfolio_id}",
    response_model=PortfolioRead,
    summary="Get a single portfolio",
)
async def get_portfolio(
    portfolio_id: str,
    current_user: Annotated[UserORM, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PortfolioRead:
    portfolio = await _get_user_portfolio(portfolio_id, current_user.id, db)
    return _enrich_portfolio(portfolio)


@router.put(
    "/portfolios/{portfolio_id}",
    response_model=PortfolioRead,
    summary="Update portfolio name/description",
)
async def update_portfolio(
    portfolio_id: str,
    body: PortfolioCreate,
    current_user: Annotated[UserORM, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PortfolioRead:
    portfolio = await _get_user_portfolio(portfolio_id, current_user.id, db)
    portfolio.name = body.name
    portfolio.description = body.description
    await db.flush()
    await db.refresh(portfolio)
    return _enrich_portfolio(portfolio)


@router.delete(
    "/portfolios/{portfolio_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a portfolio and all its holdings",
)
async def delete_portfolio(
    portfolio_id: str,
    current_user: Annotated[UserORM, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    portfolio = await _get_user_portfolio(portfolio_id, current_user.id, db)
    await db.delete(portfolio)


# ── Holdings ──────────────────────────────────────────────────────────────────

@router.post(
    "/portfolios/{portfolio_id}/holdings",
    response_model=HoldingRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add a holding to a portfolio",
)
async def add_holding(
    portfolio_id: str,
    body: HoldingCreate,
    current_user: Annotated[UserORM, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> HoldingRead:
    # Ownership check via portfolio lookup
    await _get_user_portfolio(portfolio_id, current_user.id, db)

    holding = HoldingORM(portfolio_id=portfolio_id, **body.model_dump())
    db.add(holding)
    await db.flush()
    await db.refresh(holding)
    return _enrich_holding(holding)


@router.delete(
    "/portfolios/{portfolio_id}/holdings/{holding_id}",
    status_code=status.HTTP_200_OK,
    summary="Remove a holding from a portfolio",
)
async def remove_holding(
    portfolio_id: str,
    holding_id: str,
    current_user: Annotated[UserORM, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    # Ownership check via portfolio lookup
    await _get_user_portfolio(portfolio_id, current_user.id, db)

    result = await db.execute(
        select(HoldingORM).where(
            HoldingORM.id == holding_id,
            HoldingORM.portfolio_id == portfolio_id,
        )
    )
    holding = result.scalar_one_or_none()
    if not holding:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Holding not found")
    await db.delete(holding)


# ── SIP Trackers ──────────────────────────────────────────────────────────────

@router.post(
    "/sip-trackers",
    response_model=SIPTrackerRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a SIP tracker",
)
async def create_sip_tracker(
    body: SIPTrackerCreate,
    current_user: Annotated[UserORM, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SIPTrackerRead:
    tracker = SIPTrackerORM(
        user_id=current_user.id,
        holding_id=body.holding_id,
        amount=body.amount,
        frequency=body.frequency,
        start_date=body.start_date,
        cashflows=[c.model_dump() for c in body.cashflows] if body.cashflows else None,
    )
    db.add(tracker)
    await db.flush()
    await db.refresh(tracker)
    return SIPTrackerRead.model_validate(tracker)


@router.get(
    "/sip-trackers",
    response_model=list[SIPTrackerRead],
    summary="List your SIP trackers",
)
async def list_sip_trackers(
    current_user: Annotated[UserORM, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[SIPTrackerRead]:
    result = await db.execute(
        select(SIPTrackerORM)
        .where(SIPTrackerORM.user_id == current_user.id)
        .order_by(SIPTrackerORM.created_at.desc())
    )
    trackers = result.scalars().all()
    return [SIPTrackerRead.model_validate(t) for t in trackers]
