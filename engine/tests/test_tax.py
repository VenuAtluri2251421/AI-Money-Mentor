"""engine/tests/test_tax.py — Unit tests for Indian income tax (FY 2025-26).

Judge test cases are verified against Budget 2025 official slabs.
"""
import pytest
from engine.tax import (
    Deductions,
    TaxRegime,
    calculate_tax,
    compare_regimes,
)


# ---------------------------------------------------------------------------
# JUDGE TEST CASES — Do not modify these numbers
# ---------------------------------------------------------------------------

class TestJudgeCases:
    """Four canonical test cases that judges will verify."""

    def test_case1_12L_gross_new_regime(self):
        """
        ₹12,00,000 gross, new regime, no deductions.
        After ₹75K std deduction → taxable = ₹11,25,000
        Tax before rebate = (4L×0) + (4L×5%) + (3.25L×10%) = 52,500
        Net income ≤ ₹12L → 87A rebate = ₹52,500 (capped at ₹60K)
        Tax after rebate = ₹0. Cess = ₹0. Total = ₹0.
        """
        result = calculate_tax(12_00_000, TaxRegime.NEW)
        assert result.taxable_income == pytest.approx(11_25_000, abs=1)
        assert result.total_tax == pytest.approx(0.0, abs=1)

    def test_case2_1275k_gross_new_regime(self):
        """
        ₹12,75,000 gross, new regime.
        After ₹75K → taxable = ₹12,00,000
        Tax before rebate = (4L×0) + (4L×5%) + (4L×10%) = 60,000
        Net income = exactly ₹12L → 87A rebate = ₹60,000
        Tax after rebate = ₹0. Cess = ₹0. Total = ₹0.
        """
        result = calculate_tax(12_75_000, TaxRegime.NEW)
        assert result.taxable_income == pytest.approx(12_00_000, abs=1)
        assert result.total_tax == pytest.approx(0.0, abs=1)

    def test_case3_15L_gross_new_regime(self):
        """
        ₹15,00,000 gross, new regime.
        After ₹75K → taxable = ₹14,25,000
        Tax: (4L×0) + (4L×5%) + (4L×10%) + (2.25L×15%) = 93,750
        Net income > ₹12L → no 87A rebate.
        Cess = ₹93,750 × 4% = ₹3,750. Total = ₹97,500.
        """
        result = calculate_tax(15_00_000, TaxRegime.NEW)
        assert result.taxable_income == pytest.approx(14_25_000, abs=1)
        assert result.base_tax == pytest.approx(93_750, abs=1)
        assert result.health_education_cess == pytest.approx(3_750, abs=1)
        assert result.total_tax == pytest.approx(97_500, abs=1)

    def test_case4_10L_gross_old_regime_no_deductions(self):
        """
        ₹10,00,000 gross, old regime, no deductions.
        After ₹50K std → taxable = ₹9,50,000
        Tax: (2.5L×0) + (2.5L×5%) + (4.5L×20%) = 12,500 + 90,000 = 1,02,500
        Cess = ₹4,100. Total = ₹1,06,600.
        """
        result = calculate_tax(10_00_000, TaxRegime.OLD)
        assert result.taxable_income == pytest.approx(9_50_000, abs=1)
        assert result.base_tax == pytest.approx(1_02_500, abs=1)
        assert result.health_education_cess == pytest.approx(4_100, abs=1)
        assert result.total_tax == pytest.approx(1_06_600, abs=1)


# ---------------------------------------------------------------------------
# Structural / logic tests
# ---------------------------------------------------------------------------

class TestNewRegime:
    def test_income_below_4L_zero_tax(self):
        """Standard deduction alone makes income ≤ 4L taxable → 0 tax."""
        result = calculate_tax(4_75_000, TaxRegime.NEW)
        # Taxable = 4,75,000 - 75,000 = 4,00,000 → 0% slab → 87A rebate (0 tax anyway)
        assert result.total_tax == 0.0

    def test_high_income_positive_tax(self):
        result = calculate_tax(30_00_000, TaxRegime.NEW)
        assert result.total_tax > 0
        assert result.effective_rate_pct > 0

    def test_take_home_consistent(self):
        result = calculate_tax(20_00_000, TaxRegime.NEW)
        assert result.take_home_annual == pytest.approx(result.gross_income - result.total_tax, rel=0.001)

    def test_monthly_take_home(self):
        result = calculate_tax(20_00_000, TaxRegime.NEW)
        assert result.take_home_monthly == pytest.approx(result.take_home_annual / 12, rel=0.001)

    def test_just_above_12L_pays_tax(self):
        """₹12,00,001 net taxable → no rebate → tax > 0."""
        # Need enough gross so taxable > 12L. At 13L gross → taxable = 12.25L
        result = calculate_tax(13_00_000, TaxRegime.NEW)
        assert result.total_tax > 0


class TestOldRegime:
    def test_with_80c_deduction(self):
        deductions = Deductions(section_80c=1_50_000)
        result = calculate_tax(10_00_000, TaxRegime.OLD, deductions)
        assert result.total_deductions > 50_000  # std + 80C

    def test_rebate_old_regime_at_5L(self):
        """Old regime taxable ≤ ₹5L gets full 87A rebate."""
        result = calculate_tax(5_00_000, TaxRegime.OLD)
        assert result.total_tax == 0.0

    def test_old_regime_above_5L_pays_tax(self):
        result = calculate_tax(6_00_000, TaxRegime.OLD)
        assert result.total_tax > 0


class TestCompareRegimes:
    def test_compare_returns_both(self):
        comp = compare_regimes(15_00_000, Deductions(section_80c=1_50_000))
        assert "old_regime" in comp
        assert "new_regime" in comp
        assert comp["recommended"] in ("old", "new")
        assert comp["savings"] >= 0

    def test_savings_is_difference(self):
        comp = compare_regimes(15_00_000)
        old_tax = comp["old_regime"].total_tax
        new_tax = comp["new_regime"].total_tax
        assert comp["savings"] == pytest.approx(abs(old_tax - new_tax), rel=0.001)
