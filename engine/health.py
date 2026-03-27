"""
engine/health.py — Financial Health Score Engine (FY 2025-26).

6-dimension composite score (0-100):
  1. Emergency Fund       (20%)
  2. Insurance            (20%)
  3. Debt Management      (15%)
  4. Diversification      (15%)  — age-aware targets, not one-size-fits-all
  5. Tax Efficiency       (15%)
  6. Retirement Readiness (15%)

Weights deliberately leave 10% unallocated — that slack lets us add a 7th
dimension (e.g., goal-based saving) without reshuffling everything.
"""
from __future__ import annotations

import math
import logging
from dataclasses import dataclass, field
from typing import Literal

logger = logging.getLogger(__name__)

ScoreLabel = Literal["Poor", "Fair", "Good", "Very Good", "Excellent"]


@dataclass
class HealthInput:
    # Core cashflow
    monthly_income: float
    monthly_expenses: float

    # Emergency fund
    emergency_fund: float          # Current liquid savings (₹)
    monthly_fixed_expenses: float  # Fixed outflows: rent + EMI + utilities

    # Debt
    total_emi: float = 0.0
    credit_card_balance: float = 0.0

    # Portfolio (current market value in ₹)
    equity_investments: float = 0.0
    debt_investments: float = 0.0
    gold_investments: float = 0.0
    real_estate: float = 0.0

    # Insurance
    life_cover: float = 0.0    # Sum assured (₹)
    health_cover: float = 0.0  # Health insurance cover (₹)

    # Tax efficiency inputs
    age: int = 30
    gross_income: float = 0.0    # Annual gross — defaults to monthly_income × 12 if 0
    sec80c_used: float = 0.0
    nps_used: float = 0.0        # 80CCD(1B) personal NPS contribution
    has_elss: bool = False

    # Retirement readiness inputs
    monthly_sip: float = 0.0
    current_corpus: float = 0.0  # Total across all invested assets


@dataclass
class DimensionScore:
    name: str
    score: float      # 0–100
    max_score: float  # Always 100
    pct: float        # Same as score, kept for API consistency
    insight: str      # Human-readable interpretation


@dataclass
class HealthResult:
    overall_score: float
    total_score: float    # backward-compat alias
    grade: ScoreLabel
    label: ScoreLabel     # backward-compat alias
    dimensions: list[DimensionScore] = field(default_factory=list)
    action_items: list[str] = field(default_factory=list)


def score_emergency_fund(emergency_fund: float, monthly_fixed_expenses: float) -> dict:
    """
    Target: 6 months of fixed expenses in liquid savings.
    We use fixed expenses (not total expenses) because discretionary spending
    can be cut in an emergency — rent and EMI cannot.
    """
    ideal = monthly_fixed_expenses * 6
    months = (emergency_fund / monthly_fixed_expenses) if monthly_fixed_expenses > 0 else 0.0
    score = round(min(emergency_fund / ideal, 1.0) * 100) if ideal > 0 else 0

    if months >= 6:
        msg = f"Emergency fund covers {months:.1f} months — on target."
    elif months >= 3:
        msg = f"Fund covers {months:.1f} months. Build to 6 months before investing more."
    else:
        msg = f"Only {months:.1f} months covered. This needs to be your #1 priority."

    return {
        "score": score,
        "months_covered": round(months, 1),
        "ideal_months": 6,
        "emergency_fund": emergency_fund,
        "ideal_corpus": ideal,
        "message": msg,
    }


def score_insurance(monthly_income: float, life_cover: float, health_cover: float) -> dict:
    """
    Life cover benchmark: 10-15× annual income (HDFC/LIC industry thumb rule).
    Health cover minimum: ₹5L for a single person, more for family floater.
    We score life (60 pts) heavier than health (40 pts) because term life
    is chronically under-owned in India vs health insurance.

    TODO: Add family floater scoring — ₹5L floor is too low for 4+ member families.
    """
    annual_income = monthly_income * 12
    life_multiple = (life_cover / annual_income) if annual_income > 0 else 0.0
    life_ok = life_multiple >= 10
    health_ok = health_cover >= 500_000

    pts = (60 if life_ok else 0) + (40 if health_ok else 0)
    notes = []
    notes.append(
        f"Life cover {life_multiple:.1f}× income {'(adequate)' if life_ok else '(need 10×+)'}"
    )
    notes.append(
        f"Health cover ₹{health_cover/100_000:.1f}L {'(adequate)' if health_ok else '(need ₹5L+)'}"
    )

    return {
        "score": pts,
        "life_multiple": round(life_multiple, 1),
        "life_cover": life_cover,
        "health_cover": health_cover,
        "life_adequate": life_ok,
        "health_adequate": health_ok,
        "message": " | ".join(notes),
    }


def score_debt(monthly_income: float, total_emi: float) -> dict:
    """
    Debt-to-income ratio. RBI and most banks use 40-50% as the danger threshold;
    we're stricter at 30% because that includes buffer for unexpected expenses.
    """
    dti = (total_emi / monthly_income) if monthly_income > 0 else 1.0
    dti_pct = dti * 100

    if dti <= 0.30:
        score, msg = 100, f"EMI/income ratio {dti_pct:.1f}% — healthy."
    elif dti <= 0.45:
        score, msg = 60, f"EMI/income ratio {dti_pct:.1f}% — manageable but avoid new loans."
    else:
        score, msg = 10, f"EMI/income ratio {dti_pct:.1f}% — over-leveraged. Prioritise debt payoff."

    return {
        "score": score,
        "dti_pct": round(dti_pct, 1),
        "total_emi": total_emi,
        "monthly_income": monthly_income,
        "message": msg,
    }


def score_investment_diversification(portfolio: dict, age: int = 30) -> dict:
    """
    Score against age-appropriate target allocation.

    Targets (Equity/Debt/Gold):
      < 35:   65/20/10  — growth phase, can ride volatility
      35-49:  50/30/10  — accumulation, start de-risking
      ≥ 50:   30/50/10  — capital preservation before retirement

    Deviation penalty: 1.5 pts per percentage point of deviation from target.
    A perfectly allocated portfolio scores 100; 33 pp total deviation = 50.

    FIXME: Real estate is lumped into 'other' which undersells its diversification
           benefit — it's actually a decent inflation hedge.
    """
    equity = portfolio.get("equity", 0.0)
    debt = portfolio.get("debt", 0.0)
    gold = portfolio.get("gold", 0.0)
    other = portfolio.get("other", 0.0)
    total = equity + debt + gold + other

    if total == 0:
        return {
            "score": 0,
            "actual_allocation": {"equity": 0, "debt": 0, "gold": 0, "other": 0},
            "target_allocation": {},
            "rebalancing_suggestions": ["Start investing to build a diversified portfolio."],
            "message": "No investments detected. Start building a portfolio.",
        }

    actual = {k: round(v / total * 100, 1) for k, v in
              [("equity", equity), ("debt", debt), ("gold", gold), ("other", other)]}

    if age < 35:
        target = {"equity": 65, "debt": 20, "gold": 10, "other": 5}
    elif age < 50:
        target = {"equity": 50, "debt": 30, "gold": 10, "other": 10}
    else:
        target = {"equity": 30, "debt": 50, "gold": 10, "other": 10}

    deviation = sum(abs(actual[k] - target[k]) for k in target)
    score = max(0, math.floor(100 - deviation * 1.5))

    suggestions = []
    for asset, tgt in target.items():
        diff = actual[asset] - tgt
        if diff > 5:
            suggestions.append(
                f"Reduce {asset} by ~{diff:.0f}% (at {actual[asset]:.0f}%, target {tgt}%)"
            )
        elif diff < -5:
            suggestions.append(
                f"Increase {asset} by ~{-diff:.0f}% (at {actual[asset]:.0f}%, target {tgt}%)"
            )

    msg = (
        f"Portfolio well-aligned for age {age}."
        if not suggestions
        else f"Portfolio needs rebalancing for age {age}."
    )

    return {
        "score": score,
        "actual_allocation": actual,
        "target_allocation": target,
        "rebalancing_suggestions": suggestions,
        "message": msg,
    }


def score_tax_efficiency(
    gross_income: float,
    sec80c_used: float,
    nps_used: float,
    has_elss: bool,
) -> dict:
    """
    Scoring: 80C utilisation (40 pts) + NPS (30 pts) + ELSS (30 pts).
    ELSS gets its own bucket because it's the only tax-saving instrument
    that also gives equity market exposure — a qualitative bonus over plain FDs.

    Potential saving estimate uses 30% marginal rate above ₹10L, 20% below —
    a rough heuristic. Doesn't account for surcharge or actual slab position.
    """
    limit_80c = 150_000
    util_80c = min(sec80c_used / limit_80c, 1.0) if limit_80c > 0 else 0.0
    score = min(100, int(util_80c * 40 + (30 if nps_used > 0 else 0) + (30 if has_elss else 0)))

    marginal_rate = 0.30 if gross_income > 1_000_000 else 0.20
    unused_80c = max(limit_80c - sec80c_used, 0)
    potential_saving = round(unused_80c * marginal_rate)

    if score >= 80:
        msg = "Excellent tax planning — maximising available deductions."
    elif score >= 50:
        msg = "Good but room to improve. Consider maxing 80C and NPS before March 31."
    else:
        msg = "Significant tax-saving opportunities unused. Act before March 31."

    return {
        "score": score,
        "sec80c_utilization_pct": round(util_80c * 100, 1),
        "nps_contributed": nps_used > 0,
        "has_elss": has_elss,
        "potential_saving": potential_saving,
        "message": msg,
    }


def score_retirement_readiness(
    age: int,
    monthly_sip: float,
    current_corpus: float,
    annual_income: float,
) -> dict:
    """
    Benchmarks against Fidelity's rule-of-thumb corpus milestones (multiples of annual salary):
      30 → 1×,  40 → 3×,  50 → 6×,  60 → 10×

    Interpolated linearly between age bands. This isn't a perfect model —
    it ignores EPF, gratuity, and real estate equity — but it's a useful proxy
    for the advisor to flag severe under-saving.

    TODO: Add EPF corpus input once user onboarding captures it. EPF alone can
          account for 3-5× salary by age 60 for salaried employees.
    """
    MILESTONES = [(30, 1), (40, 3), (50, 6), (60, 10)]

    def _target_multiple(a: int) -> float:
        if a <= 30:
            return 1.0
        if a >= 60:
            return 10.0
        for i in range(len(MILESTONES) - 1):
            lo_age, lo_mul = MILESTONES[i]
            hi_age, hi_mul = MILESTONES[i + 1]
            if lo_age <= a < hi_age:
                frac = (a - lo_age) / (hi_age - lo_age)
                return lo_mul + frac * (hi_mul - lo_mul)
        return 10.0

    multiple = _target_multiple(age)
    target_corpus = multiple * annual_income
    score = min(100, int(current_corpus / target_corpus * 100)) if target_corpus > 0 else 0
    gap = max(target_corpus - current_corpus, 0)

    if score >= 100:
        msg = "On track or ahead of retirement milestone."
    elif score >= 70:
        msg = f"Slightly below milestone. Increase SIP to close the ₹{gap:,.0f} gap."
    else:
        msg = f"Significantly behind. Need ₹{gap:,.0f} more — increase monthly SIP urgently."

    return {
        "score": score,
        "current_corpus": current_corpus,
        "target_corpus": round(target_corpus),
        "gap": round(gap),
        "age": age,
        "milestone_description": f"Age {age} target = {multiple:.1f}× annual salary",
        "message": msg,
    }


# Weights sum to 0.90, not 1.0 — the 10% slack is intentional (see module docstring).
_WEIGHTS = {
    "emergency_fund":           0.20,
    "insurance":                0.20,
    "debt":                     0.15,
    "investment_diversification": 0.15,
    "tax_efficiency":           0.15,
    "retirement_readiness":     0.15,
}


def calculate_overall_health_score(inp: HealthInput) -> HealthResult:
    """
    Compute the composite 6-dimension financial health score.

    Each dimension scores 0–100 independently. Overall is the weighted average,
    normalised against the actual sum of weights (not 1.0) so adding a new
    dimension with a new weight doesn't silently change every existing score.
    """
    if inp.monthly_income <= 0:
        raise ValueError("monthly_income must be positive")

    annual_income = inp.gross_income if inp.gross_income > 0 else inp.monthly_income * 12

    ef = score_emergency_fund(inp.emergency_fund, inp.monthly_fixed_expenses)
    ins = score_insurance(inp.monthly_income, inp.life_cover, inp.health_cover)
    dbt = score_debt(inp.monthly_income, inp.total_emi)
    div = score_investment_diversification({
        "equity": inp.equity_investments,
        "debt": inp.debt_investments,
        "gold": inp.gold_investments,
        "other": inp.real_estate,
    }, inp.age)
    te = score_tax_efficiency(annual_income, inp.sec80c_used, inp.nps_used, inp.has_elss)
    rr = score_retirement_readiness(inp.age, inp.monthly_sip, inp.current_corpus, annual_income)

    dim_map = [
        ("emergency_fund",           ef,  ef["message"]),
        ("insurance",                ins, ins["message"]),
        ("debt",                     dbt, dbt["message"]),
        ("investment_diversification", div, div["message"]),
        ("tax_efficiency",           te,  te["message"]),
        ("retirement_readiness",     rr,  rr["message"]),
    ]
    dimensions = [
        DimensionScore(name, result["score"], 100, result["score"], msg)
        for name, result, msg in dim_map
    ]

    weight_sum = sum(_WEIGHTS.values())
    overall = sum(dim.score * _WEIGHTS[name] for dim, (name, _, _) in zip(dimensions, dim_map))
    overall_score = round(overall / weight_sum, 2)
    grade = _label(overall_score)

    # Surface the worst-performing dimensions as actionable items (max 5)
    action_items = [
        f"Improve {dim.name}: {dim.insight}"
        for dim in sorted(dimensions, key=lambda d: d.score)
        if dim.score < 50
    ][:5]

    return HealthResult(
        overall_score=overall_score,
        total_score=overall_score,
        grade=grade,
        label=grade,
        dimensions=dimensions,
        action_items=action_items,
    )


def calculate_health(inp: HealthInput) -> HealthResult:
    """Backward-compat alias for calculate_overall_health_score."""
    return calculate_overall_health_score(inp)


def _label(score: float) -> ScoreLabel:
    if score >= 85:
        return "Excellent"
    if score >= 70:
        return "Very Good"
    if score >= 55:
        return "Good"
    if score >= 40:
        return "Fair"
    return "Poor"
