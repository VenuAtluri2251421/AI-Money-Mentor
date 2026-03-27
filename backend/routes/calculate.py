"""
backend/routes/calculate.py — Financial calculation endpoints.

Routes:
  POST /calculate/sip          → SIP maturity value
  POST /calculate/sip/reverse  → Required monthly SIP
  POST /calculate/fire         → FIRE number + projection
  POST /calculate/fire/years   → Years to FIRE given SIP
  POST /calculate/tax          → Indian income tax (old/new regime)
  POST /calculate/tax/compare  → Side-by-side old vs new regime
  POST /calculate/xirr         → XIRR from dated cash-flows
  POST /calculate/portfolio/xirr → XIRR from transaction dicts
  POST /calculate/health       → 6-dimension financial health score
"""
from __future__ import annotations

import datetime
import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field


class LenientModel(BaseModel):
    """
    Base model for all inbound request schemas.

    extra='ignore'        — unknown fields from the frontend are silently dropped.
                           Without this, React sending {"amount": 1000, "currency": "INR"}
                           would produce a 422 on the backend because 'currency' is unknown.
    populate_by_name=True — allows both the field name AND any alias to be used in the payload,
                           important for DeductionsSchema which accepts sec80c AND section_80c.
    """
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

from engine.sip import calculate_sip, required_sip
from engine.fire import calculate_fire, years_to_reach_fire
from engine.tax import (
    Deductions as TaxDeductions,
    TaxRegime,
    calculate_tax,
    compare_regimes,
)
from engine.xirr import calculate_xirr, xirr_from_transactions
from engine.health import (
    HealthInput,
    calculate_overall_health_score,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/calculate", tags=["Financial Calculators"])


# ── SIP ──────────────────────────────────────────────────────────────────────

class SIPRequest(LenientModel):
    monthly_investment: float = Field(..., gt=0, description="Monthly SIP amount (₹)")
    annual_return_pct: float = Field(..., ge=0, le=50, description="Expected annual return %")
    tenure_years: float = Field(..., gt=0, le=50, description="Investment duration in years")


class SIPReverseRequest(LenientModel):
    target_amount: float = Field(..., gt=0, description="Target corpus (₹)")
    annual_return_pct: float = Field(..., ge=0, le=50)
    tenure_years: float = Field(..., gt=0, le=50)


@router.post("/sip", summary="SIP Maturity Calculator")
async def sip_calculate(req: SIPRequest) -> dict[str, Any]:
    try:
        result = calculate_sip(req.monthly_investment, req.annual_return_pct, req.tenure_years)
        return result.__dict__
    except Exception as exc:
        logger.error("sip_calculate error: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/sip/reverse", summary="Reverse SIP — Required Monthly Amount")
async def sip_reverse(req: SIPReverseRequest) -> dict[str, Any]:
    try:
        monthly = required_sip(req.target_amount, req.annual_return_pct, req.tenure_years)
        return {
            "target_amount": req.target_amount,
            "annual_return_pct": req.annual_return_pct,
            "tenure_years": req.tenure_years,
            "required_monthly_sip": monthly,
        }
    except Exception as exc:
        logger.error("sip_reverse error: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc))


# ── FIRE ─────────────────────────────────────────────────────────────────────

class FIRERequest(LenientModel):
    annual_expenses: float = Field(..., gt=0, description="Current annual expenses (₹)")
    inflation_pct: float = Field(6.0, ge=0, le=20)
    expected_return_pct: float = Field(12.0, ge=0, le=50)
    safe_withdrawal_rate: float = Field(4.0, gt=0, le=10)
    current_corpus: float = Field(0.0, ge=0)
    years_to_retirement: float | None = Field(None, gt=0, le=60)


class YearsToFIRERequest(LenientModel):
    fire_number: float = Field(..., gt=0)
    monthly_sip: float = Field(..., gt=0)
    annual_return_pct: float = Field(..., ge=0, le=50)
    current_corpus: float = Field(0.0, ge=0)


@router.post("/fire", summary="FIRE Number Calculator")
async def fire_calculate(req: FIRERequest) -> dict[str, Any]:
    try:
        result = calculate_fire(
            req.annual_expenses,
            req.inflation_pct,
            req.expected_return_pct,
            req.safe_withdrawal_rate,
            req.current_corpus,
            req.years_to_retirement,
        )
        return result.__dict__
    except Exception as exc:
        logger.error("fire_calculate error: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/fire/years", summary="Years to FIRE given monthly SIP")
async def fire_years(req: YearsToFIRERequest) -> dict[str, Any]:
    try:
        years = years_to_reach_fire(
            req.fire_number, req.monthly_sip, req.annual_return_pct, req.current_corpus
        )
        return {"fire_number": req.fire_number, "years_to_fire": years}
    except Exception as exc:
        logger.error("fire_years error: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc))


# ── TAX ───────────────────────────────────────────────────────────────────────

class DeductionsSchema(LenientModel):
    sec80c: float = Field(0.0, alias="sec80c")
    section_80c: float = Field(0.0)
    section_80d: float = Field(0.0)
    hra: float = Field(0.0)
    home_loan_interest: float = Field(0.0)
    nps_80ccd: float = Field(0.0)
    other: float = Field(0.0)

    def to_tax_deductions(self) -> TaxDeductions:
        # Accept both "sec80c" (shorthand from docs) and "section_80c"
        return TaxDeductions(
            section_80c=self.sec80c or self.section_80c,
            section_80d=self.section_80d,
            hra=self.hra,
            home_loan_interest=self.home_loan_interest,
            nps_80ccd=self.nps_80ccd,
            other=self.other,
        )


class TaxRequest(LenientModel):
    gross_income: float = Field(..., ge=0, description="Annual gross income (₹)")
    regime: TaxRegime = TaxRegime.NEW
    age: int = Field(30, ge=18, le=100)
    deductions: DeductionsSchema = Field(default_factory=DeductionsSchema)


@router.post("/tax", summary="Indian Income Tax Calculator (FY 2025-26)")
async def tax_calculate(req: TaxRequest) -> dict[str, Any]:
    try:
        deductions = req.deductions.to_tax_deductions()
        result = calculate_tax(req.gross_income, req.regime, deductions, req.age)
        d = result.__dict__.copy()
        d["regime"] = d["regime"].value
        return d
    except Exception as exc:
        logger.error("tax_calculate error: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/tax/compare", summary="Compare Old vs New Tax Regime (FY 2025-26)")
async def tax_compare(req: TaxRequest) -> dict[str, Any]:
    try:
        deductions = req.deductions.to_tax_deductions()
        comparison = compare_regimes(req.gross_income, deductions, req.age)
        # Serialize TaxResult objects
        for key in ("old_regime", "new_regime"):
            r = comparison[key]
            r_dict = r.__dict__.copy()
            r_dict["regime"] = r_dict["regime"].value
            comparison[key] = r_dict
        return comparison
    except Exception as exc:
        logger.error("tax_compare error: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc))


# ── XIRR ─────────────────────────────────────────────────────────────────────

class CashflowItem(LenientModel):
    date: str = Field(..., description="ISO date YYYY-MM-DD")
    amount: float = Field(..., description="Negative = outflow, Positive = inflow")


class XIRRRequest(LenientModel):
    cashflows: list[CashflowItem] = Field(..., min_length=2)


class TransactionItem(LenientModel):
    date: str = Field(..., description="ISO date YYYY-MM-DD")
    amount: float = Field(..., description="Negative = buy, Positive = sell/redemption")
    units: float | None = Field(None, description="Units (ignored in calculation)")


class PortfolioXIRRRequest(LenientModel):
    transactions: list[TransactionItem] = Field(..., min_length=2)


@router.post("/xirr", summary="XIRR — Annualised Portfolio Return")
async def xirr_calculate(req: XIRRRequest) -> dict[str, Any]:
    try:
        pairs = [(datetime.date.fromisoformat(cf.date), cf.amount) for cf in req.cashflows]
        result = calculate_xirr(pairs)
        return result.__dict__
    except Exception as exc:
        logger.error("xirr_calculate error: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/portfolio/xirr", summary="Portfolio XIRR from transaction list")
async def portfolio_xirr(req: PortfolioXIRRRequest) -> dict[str, Any]:
    try:
        txns = [{"date": t.date, "amount": t.amount} for t in req.transactions]
        result = xirr_from_transactions(txns)
        return result.__dict__
    except Exception as exc:
        logger.error("portfolio_xirr error: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc))


# ── HEALTH ────────────────────────────────────────────────────────────────────

class HealthRequest(LenientModel):
    # Core income/expense
    monthly_income: float = Field(..., gt=0)
    monthly_expenses: float = Field(..., ge=0)
    emergency_fund: float = Field(0.0, ge=0)
    monthly_fixed_expenses: float = Field(0.0, ge=0)

    # Debt
    total_emi: float = Field(0.0, ge=0)
    credit_card_balance: float = Field(0.0, ge=0)

    # Portfolio
    equity_investments: float = Field(0.0, ge=0)
    debt_investments: float = Field(0.0, ge=0)
    gold_investments: float = Field(0.0, ge=0)
    real_estate: float = Field(0.0, ge=0)

    # Insurance
    life_cover: float = Field(0.0, ge=0)
    health_cover: float = Field(0.0, ge=0)

    # Tax efficiency inputs (new — all optional with sensible defaults)
    age: int = Field(30, ge=18, le=100)
    gross_income: float = Field(0.0, ge=0, description="Annual gross income; defaults to monthly_income × 12")
    sec80c_used: float = Field(0.0, ge=0)
    nps_used: float = Field(0.0, ge=0)
    has_elss: bool = Field(False)

    # Retirement readiness inputs (new — optional)
    monthly_sip: float = Field(0.0, ge=0)
    current_corpus: float = Field(0.0, ge=0, description="Total accumulated corpus across all assets")


@router.post("/health", summary="6-Dimension Financial Health Score (0-100)")
async def health_calculate(req: HealthRequest) -> dict[str, Any]:
    try:
        inp = HealthInput(
            monthly_income=req.monthly_income,
            monthly_expenses=req.monthly_expenses,
            emergency_fund=req.emergency_fund,
            monthly_fixed_expenses=req.monthly_fixed_expenses or req.monthly_expenses,
            total_emi=req.total_emi,
            credit_card_balance=req.credit_card_balance,
            equity_investments=req.equity_investments,
            debt_investments=req.debt_investments,
            gold_investments=req.gold_investments,
            real_estate=req.real_estate,
            life_cover=req.life_cover,
            health_cover=req.health_cover,
            age=req.age,
            gross_income=req.gross_income or (req.monthly_income * 12),
            sec80c_used=req.sec80c_used,
            nps_used=req.nps_used,
            has_elss=req.has_elss,
            monthly_sip=req.monthly_sip,
            current_corpus=req.current_corpus,
        )
        result = calculate_overall_health_score(inp)
        return {
            "overall_score": result.overall_score,
            "grade": result.grade,
            "dimensions": [
                {
                    "name": d.name,
                    "score": d.score,
                    "max_score": d.max_score,
                    "pct": d.pct,
                    "insight": d.insight,
                }
                for d in result.dimensions
            ],
            "action_items": result.action_items,
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("health_calculate error: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc))
