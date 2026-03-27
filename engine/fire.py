"""
engine/fire.py — FIRE (Financial Independence, Retire Early) calculator.

Uses the 4% Safe Withdrawal Rate from the Trinity Study (1998).
The SWR says: if your portfolio generates X% annually, you can withdraw X% of the corpus
forever without depleting it. At 4% SWR, you need 25× your annual expenses as the corpus.

We use real return (after inflation) only for projecting how long existing corpus grows,
but FIRE number itself is calculated at nominal expenses × 25 — this is intentional
because the SWR already accounts for inflation in its 30-year historical back-tests.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FIREResult:
    annual_expenses: float
    inflation_pct: float
    expected_return_pct: float
    real_return_pct: float
    fire_number: float           # Total corpus needed at retirement
    monthly_sip_needed: float    # What you need to invest monthly to get there
    years_to_fire: float | None  # None means we don't have enough info yet
    safe_withdrawal_rate: float


def calculate_fire(
    annual_expenses: float,
    inflation_pct: float = 6.0,
    expected_return_pct: float = 12.0,
    safe_withdrawal_rate: float = 4.0,
    current_corpus: float = 0.0,
    years_to_retirement: float | None = None,
) -> FIREResult:
    """
    Compute FIRE number and required monthly SIP.

    If years_to_retirement is provided, we calculate what monthly SIP you need starting today.
    If not provided, monthly_sip_needed will be 0.0 — call years_to_reach_fire() separately.

    TODO: Add lumpsum + SIP hybrid mode — most real users have both.
    """
    if annual_expenses <= 0:
        raise ValueError("annual_expenses must be positive")
    if safe_withdrawal_rate <= 0:
        raise ValueError("safe_withdrawal_rate must be positive")
    if expected_return_pct < inflation_pct:
        raise ValueError("expected_return_pct should exceed inflation_pct to achieve real growth")

    # Fisher equation approximation for real return
    real_return = ((1 + expected_return_pct / 100) / (1 + inflation_pct / 100) - 1) * 100

    fire_number = annual_expenses / (safe_withdrawal_rate / 100)
    remaining_corpus = max(fire_number - current_corpus, 0)

    monthly_sip = 0.0
    years_to_fire: float | None = None

    if years_to_retirement and years_to_retirement > 0 and remaining_corpus > 0:
        from engine.sip import required_sip
        monthly_sip = required_sip(remaining_corpus, expected_return_pct, years_to_retirement)
    elif remaining_corpus == 0:
        years_to_fire = 0.0

    return FIREResult(
        annual_expenses=round(annual_expenses, 2),
        inflation_pct=inflation_pct,
        expected_return_pct=expected_return_pct,
        real_return_pct=round(real_return, 4),
        fire_number=round(fire_number, 2),
        monthly_sip_needed=round(monthly_sip, 2),
        years_to_fire=years_to_fire,
        safe_withdrawal_rate=safe_withdrawal_rate,
    )


def years_to_reach_fire(
    fire_number: float,
    monthly_sip: float,
    annual_return_pct: float,
    current_corpus: float = 0.0,
) -> float:
    """
    Binary search for how many years it takes to accumulate fire_number
    given a fixed monthly SIP and an existing corpus.

    Returns 0.0 immediately if corpus already meets the target.
    Searched up to 100 years — if it takes longer, something's off with the inputs.
    """
    from engine.sip import calculate_sip

    if fire_number <= current_corpus:
        return 0.0

    lo, hi = 0.1, 100.0
    for _ in range(60):  # 60 iterations gives sub-millisecond precision
        mid = (lo + hi) / 2
        sip_result = calculate_sip(monthly_sip, annual_return_pct, mid)
        # Corpus grows too, not just new SIP contributions
        corpus_growth = current_corpus * ((1 + annual_return_pct / 100 / 12) ** (mid * 12))
        total = sip_result.maturity_amount + corpus_growth
        if total >= fire_number:
            hi = mid
        else:
            lo = mid

    return round((lo + hi) / 2, 2)
