"""engine/tests/test_health.py — Unit tests for the 6-dimension financial health scorer."""
import pytest
from engine.health import (
    HealthInput,
    calculate_health,
    calculate_overall_health_score,
    score_emergency_fund,
    score_insurance,
    score_debt,
    score_investment_diversification,
    score_tax_efficiency,
    score_retirement_readiness,
)


def _base_input(**overrides) -> HealthInput:
    defaults = dict(
        monthly_income=100_000,
        monthly_expenses=60_000,
        emergency_fund=360_000,        # 6 months of 60k fixed
        monthly_fixed_expenses=60_000,
        total_emi=15_000,
        equity_investments=500_000,
        debt_investments=200_000,
        gold_investments=50_000,
        real_estate=0,
        life_cover=12_000_000,          # 10× annual income
        health_cover=1_000_000,
        age=30,
        gross_income=1_200_000,
        sec80c_used=100_000,
        nps_used=50_000,
        has_elss=True,
        monthly_sip=10_000,
        current_corpus=1_200_000,
    )
    defaults.update(overrides)
    return HealthInput(**defaults)


# ---------------------------------------------------------------------------
# Overall health score
# ---------------------------------------------------------------------------

class TestOverallHealth:
    def test_score_in_range(self):
        result = calculate_health(_base_input())
        assert 0 <= result.overall_score <= 100

    def test_six_dimensions(self):
        result = calculate_health(_base_input())
        assert len(result.dimensions) == 6

    def test_dimension_names(self):
        result = calculate_health(_base_input())
        names = {d.name for d in result.dimensions}
        assert "emergency_fund" in names
        assert "insurance" in names
        assert "debt" in names
        assert "investment_diversification" in names
        assert "tax_efficiency" in names
        assert "retirement_readiness" in names

    def test_grade_values(self):
        result = calculate_health(_base_input())
        assert result.grade in ("Poor", "Fair", "Good", "Very Good", "Excellent")

    def test_label_is_grade_alias(self):
        result = calculate_health(_base_input())
        assert result.label == result.grade

    def test_total_score_is_overall_alias(self):
        result = calculate_health(_base_input())
        assert result.total_score == result.overall_score

    def test_action_items_are_list(self):
        result = calculate_health(_base_input(emergency_fund=0, total_emi=80_000))
        assert isinstance(result.action_items, list)

    def test_invalid_income_raises(self):
        with pytest.raises(ValueError, match="monthly_income"):
            calculate_health(_base_input(monthly_income=0))

    def test_good_profile_scores_above_50(self):
        result = calculate_health(_base_input())
        assert result.overall_score >= 50


# ---------------------------------------------------------------------------
# Emergency Fund
# ---------------------------------------------------------------------------

class TestEmergencyFund:
    def test_six_months_is_full_score(self):
        r = score_emergency_fund(360_000, 60_000)
        assert r["score"] == 100

    def test_zero_fund_zero_score(self):
        r = score_emergency_fund(0, 60_000)
        assert r["score"] == 0

    def test_three_months_half_score(self):
        r = score_emergency_fund(180_000, 60_000)
        assert r["score"] == pytest.approx(50, abs=1)

    def test_zero_expenses_no_crash(self):
        r = score_emergency_fund(100_000, 0)
        assert r["score"] == 0


# ---------------------------------------------------------------------------
# Insurance
# ---------------------------------------------------------------------------

class TestInsurance:
    def test_both_adequate_full_score(self):
        r = score_insurance(100_000, 12_000_000, 1_000_000)
        assert r["score"] == 100

    def test_no_life_cover_low_score(self):
        r = score_insurance(100_000, 0, 1_000_000)
        assert r["score"] == 40   # only health component

    def test_no_health_cover_low_score(self):
        r = score_insurance(100_000, 12_000_000, 0)
        assert r["score"] == 60   # only life component

    def test_inadequate_life_cover(self):
        r = score_insurance(100_000, 5_000_000, 1_000_000)
        assert not r["life_adequate"]


# ---------------------------------------------------------------------------
# Debt
# ---------------------------------------------------------------------------

class TestDebt:
    def test_low_emi_full_score(self):
        r = score_debt(100_000, 20_000)  # 20% DTI
        assert r["score"] == 100

    def test_moderate_emi_partial_score(self):
        r = score_debt(100_000, 40_000)  # 40% DTI
        assert r["score"] == 60

    def test_high_emi_low_score(self):
        r = score_debt(100_000, 70_000)  # 70% DTI
        assert r["score"] == 10


# ---------------------------------------------------------------------------
# Investment Diversification
# ---------------------------------------------------------------------------

class TestDiversification:
    def test_no_investments_zero_score(self):
        r = score_investment_diversification({}, age=30)
        assert r["score"] == 0

    def test_age_lt35_equity_heavy_target(self):
        r = score_investment_diversification(
            {"equity": 650, "debt": 200, "gold": 100, "other": 50}, age=28
        )
        assert r["target_allocation"]["equity"] == 65

    def test_age_gte50_debt_heavy_target(self):
        r = score_investment_diversification(
            {"equity": 300, "debt": 500, "gold": 100, "other": 100}, age=55
        )
        assert r["target_allocation"]["debt"] == 50

    def test_perfect_allocation_high_score(self):
        r = score_investment_diversification(
            {"equity": 650, "debt": 200, "gold": 100, "other": 50}, age=28
        )
        assert r["score"] >= 90

    def test_suggestions_when_off(self):
        r = score_investment_diversification(
            {"equity": 1000, "debt": 0, "gold": 0, "other": 0}, age=30
        )
        assert len(r["rebalancing_suggestions"]) > 0


# ---------------------------------------------------------------------------
# Tax Efficiency
# ---------------------------------------------------------------------------

class TestTaxEfficiency:
    def test_all_maxed_full_score(self):
        r = score_tax_efficiency(1_200_000, 150_000, 50_000, True)
        assert r["score"] == 100

    def test_nothing_used_zero_score(self):
        r = score_tax_efficiency(1_200_000, 0, 0, False)
        assert r["score"] == 0

    def test_80c_only_proportional(self):
        r = score_tax_efficiency(600_000, 75_000, 0, False)
        # 80C: 50% util → 20 pts, no NPS, no ELSS → 20 total
        assert r["score"] == pytest.approx(20, abs=1)

    def test_potential_saving_calculated(self):
        r = score_tax_efficiency(1_200_000, 0, 0, False)
        # 30% of ₹1.5L unused 80C = ₹45,000
        assert r["potential_saving"] == pytest.approx(45_000, abs=100)

    def test_utilization_pct(self):
        r = score_tax_efficiency(800_000, 150_000, 0, False)
        assert r["sec80c_utilization_pct"] == pytest.approx(100.0, abs=0.1)


# ---------------------------------------------------------------------------
# Retirement Readiness
# ---------------------------------------------------------------------------

class TestRetirementReadiness:
    def test_at_milestone_full_score(self):
        """Age 30 with corpus = 1× salary → score 100."""
        r = score_retirement_readiness(30, 10_000, 1_000_000, 1_000_000)
        assert r["score"] == 100

    def test_zero_corpus_zero_score(self):
        r = score_retirement_readiness(30, 0, 0, 1_000_000)
        assert r["score"] == 0

    def test_gap_computed_correctly(self):
        r = score_retirement_readiness(30, 0, 500_000, 1_000_000)
        # Target = 1× 10L = 10L; corpus = 5L; gap = 5L
        assert r["gap"] == pytest.approx(500_000, abs=100)

    def test_interpolation_age_35(self):
        """Age 35 should target between 1× and 3× = 2×."""
        r = score_retirement_readiness(35, 0, 2_000_000, 1_000_000)
        assert r["target_corpus"] == pytest.approx(2_000_000, abs=1000)

    def test_beyond_target_capped_at_100(self):
        r = score_retirement_readiness(30, 10_000, 5_000_000, 1_000_000)
        assert r["score"] == 100
