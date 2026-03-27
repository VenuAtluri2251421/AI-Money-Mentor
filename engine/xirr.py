"""
engine/xirr.py — XIRR (Extended Internal Rate of Return) calculator.

XIRR is the annualised rate that makes NPV of irregular cash-flows = 0.
It's the standard metric for evaluating mutual fund SIP performance because
SIPs don't happen at uniform intervals and amounts vary in practice.

Algorithm: scipy's brentq (bracketed Brent method) with Newton-Raphson fallback.
Brentq is preferred because it's guaranteed to converge if a sign change exists;
Newton-Raphson is faster but can diverge for pathological cash-flow patterns.
"""
from __future__ import annotations

import datetime
from dataclasses import dataclass

from scipy import optimize  # type: ignore


@dataclass
class XIRRResult:
    xirr_pct: float                     # Annualised return as a percentage
    cashflows: list[tuple[str, float]]  # (date_str, amount) for response serialisation


def _years_diff(d1: datetime.date, d0: datetime.date) -> float:
    """ACT/365 day-count convention — industry standard for XIRR."""
    return (d1 - d0).days / 365.0


def _npv(rate: float, dates: list[datetime.date], amounts: list[float]) -> float:
    d0 = dates[0]
    return sum(cf / (1 + rate) ** _years_diff(d, d0) for d, cf in zip(dates, amounts))


def calculate_xirr(cashflows: list[tuple[datetime.date | str, float]]) -> XIRRResult:
    """
    Compute XIRR for a series of dated cash-flows.

    Negative amounts = outflows (investments), positive = inflows (redemptions).
    Dates can be datetime.date objects or ISO strings.

    Raises ValueError if fewer than 2 cash-flows or if all flows are in the same direction
    (XIRR is mathematically undefined in that case).

    TODO: Add a tolerance param so high-frequency traders can tune precision vs speed.
    """
    if len(cashflows) < 2:
        raise ValueError("XIRR requires at least 2 cash-flows")

    parsed: list[tuple[datetime.date, float]] = []
    for raw_date, amount in cashflows:
        if isinstance(raw_date, str):
            raw_date = datetime.date.fromisoformat(raw_date)
        parsed.append((raw_date, amount))

    parsed.sort(key=lambda x: x[0])
    dates, amounts = zip(*parsed)

    if len({1 if a > 0 else -1 for a in amounts}) < 2:
        raise ValueError("XIRR requires both inflows and outflows")

    def f(r: float) -> float:
        return _npv(r, list(dates), list(amounts))

    try:
        rate = optimize.brentq(f, -0.999, 100.0, maxiter=1000, xtol=1e-8)
    except ValueError:
        # brentq can't find a bracket — happens with unusual cash-flow shapes.
        # Fall back to Newton-Raphson; if this also fails, let the exception propagate.
        rate = optimize.newton(f, x0=0.1, tol=1e-8, maxiter=1000)

    return XIRRResult(
        xirr_pct=round(rate * 100, 4),
        cashflows=[(str(d), a) for d, a in zip(dates, amounts)],
    )


def xirr_from_transactions(transactions: list[dict]) -> XIRRResult:
    """
    Convenience wrapper that accepts CAMS/KFintech-style transaction dicts.

    Expected keys: "date" (ISO string), "amount" (float).
    "units" is ignored — only the rupee amount matters for XIRR.
    """
    cashflows = [(txn["date"], float(txn["amount"])) for txn in transactions]
    return calculate_xirr(cashflows)
