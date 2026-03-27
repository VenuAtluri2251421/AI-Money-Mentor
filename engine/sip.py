"""
engine/sip.py — SIP (Systematic Investment Plan) calculations.

Uses the standard future-value-of-annuity-due formula:
  M = P × {[(1 + r)^n − 1] / r} × (1 + r)

The (1 + r) at the end accounts for SIPs being invested at the START of each month,
which is how most Indian mutual fund platforms process them.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SIPResult:
    monthly_investment: float
    annual_return_pct: float
    tenure_months: int
    total_invested: float
    maturity_amount: float
    wealth_gained: float
    absolute_return_pct: float  # Simple return, not annualised — use XIRR for that


def calculate_sip(
    monthly_investment: float,
    annual_return_pct: float,
    tenure_years: float,
) -> SIPResult:
    """
    Calculate SIP maturity value.

    Returns a SIPResult with invested amount, maturity value, and wealth gained.
    Raises ValueError on invalid inputs — callers should handle this at the route level.

    TODO: Add step-up SIP variant (annual increment %) — common UX request.
    """
    if monthly_investment <= 0:
        raise ValueError("monthly_investment must be positive")
    if annual_return_pct < 0:
        raise ValueError("annual_return_pct must be >= 0")
    if tenure_years <= 0:
        raise ValueError("tenure_years must be positive")

    r = annual_return_pct / 100 / 12
    n = int(tenure_years * 12)

    if r == 0:
        # Edge case: if return is literally 0%, it's just a savings jar
        maturity = monthly_investment * n
    else:
        maturity = monthly_investment * (((1 + r) ** n - 1) / r) * (1 + r)

    total_invested = monthly_investment * n
    wealth_gained = maturity - total_invested
    absolute_return_pct = (wealth_gained / total_invested * 100) if total_invested else 0.0

    return SIPResult(
        monthly_investment=round(monthly_investment, 2),
        annual_return_pct=annual_return_pct,
        tenure_months=n,
        total_invested=round(total_invested, 2),
        maturity_amount=round(maturity, 2),
        wealth_gained=round(wealth_gained, 2),
        absolute_return_pct=round(absolute_return_pct, 2),
    )


def required_sip(
    target_amount: float,
    annual_return_pct: float,
    tenure_years: float,
) -> float:
    """
    Reverse-engineer the monthly SIP needed to reach target_amount in tenure_years.
    Returns monthly investment (₹), rounded to 2 decimal places.
    """
    if target_amount <= 0:
        raise ValueError("target_amount must be positive")
    if annual_return_pct < 0:
        raise ValueError("annual_return_pct must be >= 0")
    if tenure_years <= 0:
        raise ValueError("tenure_years must be positive")

    r = annual_return_pct / 100 / 12
    n = int(tenure_years * 12)

    if r == 0:
        return round(target_amount / n, 2)

    denom = (((1 + r) ** n - 1) / r) * (1 + r)
    return round(target_amount / denom, 2)
