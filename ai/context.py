"""
ai/context.py — Build the financial context string injected into every Gemini call.

Kept under 500 tokens because Gemini's context window is large but every token
in the system prompt is a token that can't be used for the actual conversation.
Numbers not prose — the model doesn't need ₹1,25,000 explained in a sentence.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class FinancialContext:
    """Legacy return type for build_context(). Use build_user_context() for new code."""
    profile_section: str
    portfolio_section: str
    calculations_section: str


def _fmt_inr(val: float | None) -> str:
    """Format a rupee amount in the most readable scale (Cr/L/raw)."""
    if val is None:
        return "N/A"
    if val >= 1_00_00_000:
        return f"₹{val/1_00_00_000:.2f} Cr"
    if val >= 1_00_000:
        return f"₹{val/1_00_000:.2f} L"
    return f"₹{val:,.0f}"


def build_user_context(profile: dict, calculated_results: dict) -> str:
    """
    Format profile + calculator outputs into a concise context block for Gemini.

    Sections with no data are marked 'Not yet calculated' rather than omitted —
    this signals to Artha that the data doesn't exist yet, vs the user not sending it.
    Missing keys use .get() with None fallback throughout to avoid KeyErrors on partial profiles.

    TODO: Add goals[] section once the goal-tracking feature is live.
    """
    lines: list[str] = ["=== USER FINANCIAL CONTEXT ===\n[Profile]"]

    age = profile.get("age")
    income = profile.get("monthly_income")
    expenses = profile.get("monthly_expenses")

    if age:
        lines.append(f"Age: {age}")
    if income:
        lines.append(f"Monthly Income: {_fmt_inr(income)}")
    if expenses:
        lines.append(f"Monthly Expenses: {_fmt_inr(expenses)}")
    if income and expenses:
        savings = income - expenses
        savings_rate = savings / income * 100
        lines.append(f"Monthly Savings: {_fmt_inr(savings)} ({savings_rate:.1f}%)")
    if profile.get("gross_income"):
        lines.append(f"Annual Gross: {_fmt_inr(profile['gross_income'])}")
    if profile.get("existing_savings"):
        lines.append(f"Current Corpus: {_fmt_inr(profile['existing_savings'])}")
    if profile.get("monthly_sip"):
        lines.append(f"Monthly SIP: {_fmt_inr(profile['monthly_sip'])}")
    if profile.get("retirement_age"):
        lines.append(f"Target Retirement Age: {profile['retirement_age']}")
    if profile.get("risk_profile"):
        lines.append(f"Risk Profile: {profile['risk_profile']}")

    # Health Score
    health = calculated_results.get("health_score")
    if health:
        lines.append("\n[Health Score]")
        lines.append(f"Overall: {health.get('overall_score', 'N/A')}/100 — {health.get('grade', '')}")
        dims = health.get("dimensions", [])
        if dims:
            weakest = min(dims, key=lambda d: d.get("score", 100))
            lines.append(f"Weakest: {weakest.get('name')} ({weakest.get('score')}/100)")
    else:
        lines.append("\n[Health Score] Not yet calculated.")

    # FIRE
    fire = calculated_results.get("fire_result")
    if fire:
        lines.append("\n[FIRE Status]")
        if fire.get("fire_number"):
            lines.append(f"FIRE Number: {_fmt_inr(fire['fire_number'])}")
        if fire.get("years_to_fire") is not None:
            lines.append(f"Years to FIRE: {fire['years_to_fire']:.1f}")
        if fire.get("monthly_sip_needed"):
            lines.append(f"SIP Needed: {_fmt_inr(fire['monthly_sip_needed'])}/mo")
    else:
        lines.append("\n[FIRE Status] Not yet calculated.")

    # Tax
    tax = calculated_results.get("tax_result")
    if tax:
        new_r = tax.get("new_regime", {})
        old_r = tax.get("old_regime", {})
        lines.append("\n[Tax Situation]")
        lines.append(f"New Regime: {_fmt_inr(new_r.get('total_tax'))}")
        lines.append(f"Old Regime: {_fmt_inr(old_r.get('total_tax'))}")
        lines.append(f"Recommended: {tax.get('recommended', 'N/A')}")
        if tax.get("savings"):
            lines.append(f"Switching saves: {_fmt_inr(tax['savings'])}")
    else:
        lines.append("\n[Tax Situation] Not yet calculated.")

    # XIRR
    xirr = calculated_results.get("portfolio_xirr")
    if xirr:
        lines.append(f"\n[Portfolio XIRR] {xirr.get('xirr_pct', 'N/A')}%")
    else:
        lines.append("\n[Portfolio XIRR] Not yet calculated.")

    lines.append("\n=== END CONTEXT ===")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Legacy API — kept for backward compat with older route handlers
# ---------------------------------------------------------------------------

def build_profile_section(profile: dict[str, Any] | None) -> str:
    if not profile:
        return "No profile data provided."
    fields = [
        ("age", "Age"), ("risk_profile", "Risk Profile"),
        ("monthly_income", "Monthly Income"), ("monthly_expenses", "Monthly Expenses"),
        ("retirement_age", "Target Retirement Age"),
    ]
    lines = [f"{label}: {profile[key]}" for key, label in fields if profile.get(key) is not None]
    return "\n".join(lines) if lines else "Profile incomplete."


def build_portfolio_section(portfolios: list[dict[str, Any]] | None) -> str:
    if not portfolios:
        return "No portfolio data available."
    lines = []
    for p in portfolios:
        lines.append(f"Portfolio: {p.get('name', 'unnamed')}")
        if p.get("current_value"):
            lines.append(f"  Value: {_fmt_inr(p['current_value'])}")
    return "\n".join(lines)


def build_calculations_section(recent_calcs: list[dict[str, Any]] | None) -> str:
    if not recent_calcs:
        return "None"
    lines = []
    # Only show the last 5 — older results aren't relevant to the current conversation
    for calc in recent_calcs[-5:]:
        lines.append(f"[{calc.get('type', 'calculation').upper()}]")
        for k, v in calc.get("result", {}).items():
            if k not in ("slab_breakdown", "cashflows", "dimensions"):
                lines.append(f"  {k}: {v}")
    return "\n".join(lines)


def build_context(
    profile: dict[str, Any] | None = None,
    portfolios: list[dict[str, Any]] | None = None,
    recent_calculations: list[dict[str, Any]] | None = None,
) -> FinancialContext:
    """Legacy wrapper. New code should use build_user_context() directly."""
    return FinancialContext(
        profile_section=build_profile_section(profile),
        portfolio_section=build_portfolio_section(portfolios),
        calculations_section=build_calculations_section(recent_calculations),
    )
