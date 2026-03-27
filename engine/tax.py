"""
engine/tax.py — Indian Income Tax Calculator (FY 2025-26).

Covers both old and new regime, 87A rebate (Budget 2025), surcharge, and 4% cess.
The logic here follows the Income Tax Act literally — refer to Budget 2025 Finance Bill
for the slab changes. This is the single source of truth for all tax calculations in the app.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class TaxRegime(str, Enum):
    OLD = "old"
    NEW = "new"


# Budget 2025 revised new regime slabs — effective FY 2025-26.
# Old regime slabs haven't changed since FY 2017-18.
_OLD_SLABS = [
    (250_000,   0),
    (500_000,   5),
    (1_000_000, 20),
    (None,      30),
]

_NEW_SLABS_FY2526 = [
    (400_000,    0),
    (800_000,    5),
    (1_200_000, 10),
    (1_600_000, 15),
    (2_000_000, 20),
    (2_400_000, 25),
    (None,      30),
]

# Surcharge kicks in above ₹50L. New regime caps at 25% (capped via Finance Act 2023).
_SURCHARGE_RATES = [
    (5_000_000,   0),
    (10_000_000, 10),
    (20_000_000, 15),
    (50_000_000, 25),
    (None,       37),  # 37% only applies to old regime earners above ₹5Cr
]


@dataclass
class Deductions:
    """Deductions applicable under old regime. New regime ignores most of these."""
    section_80c: float = 0.0          # Capped at ₹1.5L (ELSS, PPF, LIC, etc.)
    section_80d: float = 0.0          # Medical insurance premium
    hra: float = 0.0                  # Already computed exemption, not gross HRA
    home_loan_interest: float = 0.0   # Section 24(b), capped at ₹2L for self-occupied
    nps_80ccd: float = 0.0            # Employer NPS contribution — allowed in new regime too
    other: float = 0.0

    @property
    def total_old(self) -> float:
        return (
            min(self.section_80c, 150_000)
            + self.section_80d
            + self.hra
            + min(self.home_loan_interest, 200_000)
            + self.nps_80ccd
            + self.other
        )

    @property
    def total_new(self) -> float:
        # Only employer NPS (80CCD(2)) is allowed under new regime.
        # Personal NPS (80CCD(1B)) is NOT deductible in new regime.
        return self.nps_80ccd


@dataclass
class TaxResult:
    regime: TaxRegime
    gross_income: float
    standard_deduction: float
    total_deductions: float
    taxable_income: float
    base_tax: float
    surcharge: float
    health_education_cess: float   # 4% on (base_tax + surcharge), mandatory since FY 2018-19
    total_tax: float
    effective_rate_pct: float
    take_home_annual: float
    take_home_monthly: float
    slab_breakdown: list[dict] = field(default_factory=list)


def _slab_tax(income: float, slabs: list) -> tuple[float, list[dict]]:
    """Compute tax against a slab table. Returns (total_tax, per-slab breakdown)."""
    tax = 0.0
    breakdown = []
    prev = 0.0
    for upper, rate in slabs:
        if income <= prev:
            break
        taxable_in_slab = min(income, upper if upper else income) - prev
        slab_tax = taxable_in_slab * rate / 100
        if taxable_in_slab > 0:
            breakdown.append({
                "slab": f"₹{int(prev):,} – {'₹' + f'{int(upper):,}' if upper else 'above'}",
                "income_in_slab": round(taxable_in_slab, 2),
                "rate_pct": rate,
                "tax": round(slab_tax, 2),
            })
        tax += slab_tax
        if upper is None:
            break
        prev = upper
    return tax, breakdown


def _surcharge(income: float, base_tax: float, regime: TaxRegime) -> float:
    """
    Marginal relief isn't implemented — we use the standard stepped rate.
    New regime caps surcharge at 25% per Finance Act 2023 amendment.
    """
    rate = 0
    for threshold, r in _SURCHARGE_RATES:
        if threshold is None or income > threshold:
            rate = r
        else:
            break
    if regime == TaxRegime.NEW:
        rate = min(rate, 25)
    return base_tax * rate / 100


def calculate_tax(
    gross_income: float,
    regime: TaxRegime = TaxRegime.NEW,
    deductions: Deductions | None = None,
    age: int = 30,
) -> TaxResult:
    """
    Compute income tax for a resident individual for FY 2025-26.

    Does NOT handle NRI taxation, capital gains (STCG/LTCG), or presumptive income.
    Those are separate regimes outside the scope of this function.

    TODO: Add marginal relief computation for edge cases just above ₹50L/₹1Cr.
    """
    if gross_income < 0:
        raise ValueError("gross_income must be >= 0")

    deductions = deductions or Deductions()

    std_deduction = 75_000 if regime == TaxRegime.NEW else 50_000
    regime_deductions = deductions.total_new if regime == TaxRegime.NEW else deductions.total_old
    taxable_income = max(gross_income - std_deduction - regime_deductions, 0)

    slabs = _NEW_SLABS_FY2526 if regime == TaxRegime.NEW else _OLD_SLABS
    base_tax, breakdown = _slab_tax(taxable_income, slabs)

    # 87A rebate (FY 2025-26):
    # New regime: net taxable ≤ ₹12L → rebate capped at ₹60,000 (so income up to ₹12.75L nets zero tax)
    # Old regime: net taxable ≤ ₹5L  → full rebate (all tax wiped)
    if regime == TaxRegime.NEW and taxable_income <= 1_200_000:
        rebate = min(base_tax, 60_000)
        base_tax = max(base_tax - rebate, 0.0)
        if rebate > 0:
            breakdown = [{**b, "rebate_applied": True} for b in breakdown]
    elif regime == TaxRegime.OLD and taxable_income <= 500_000:
        base_tax = 0.0
        breakdown = [{**b, "rebate_applied": True} for b in breakdown]

    surcharge = _surcharge(gross_income, base_tax, regime)
    cess = (base_tax + surcharge) * 0.04
    total_tax = base_tax + surcharge + cess
    effective_rate = (total_tax / gross_income * 100) if gross_income else 0.0

    return TaxResult(
        regime=regime,
        gross_income=round(gross_income, 2),
        standard_deduction=std_deduction,
        total_deductions=round(std_deduction + regime_deductions, 2),
        taxable_income=round(taxable_income, 2),
        base_tax=round(base_tax, 2),
        surcharge=round(surcharge, 2),
        health_education_cess=round(cess, 2),
        total_tax=round(total_tax, 2),
        effective_rate_pct=round(effective_rate, 4),
        take_home_annual=round(gross_income - total_tax, 2),
        take_home_monthly=round((gross_income - total_tax) / 12, 2),
        slab_breakdown=breakdown,
    )


def compare_regimes(
    gross_income: float,
    deductions: Deductions | None = None,
    age: int = 30,
) -> dict:
    """Side-by-side old vs new regime comparison. Returns the recommended regime and savings."""
    old = calculate_tax(gross_income, TaxRegime.OLD, deductions, age)
    new = calculate_tax(gross_income, TaxRegime.NEW, deductions, age)
    better = "old" if old.total_tax < new.total_tax else "new"
    return {
        "old_regime": old,
        "new_regime": new,
        "recommended": better,
        "savings": round(abs(old.total_tax - new.total_tax), 2),
    }
