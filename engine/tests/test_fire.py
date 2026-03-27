"""engine/tests/test_fire.py — Unit tests for the FIRE calculator."""
import pytest
from engine.fire import calculate_fire, years_to_reach_fire


class TestCalculateFIRE:
    def test_fire_number_4pct_rule(self):
        """FIRE number = annual_expenses / 0.04 = 25× annual expenses."""
        result = calculate_fire(annual_expenses=12_00_000, safe_withdrawal_rate=4.0)
        assert result.fire_number == pytest.approx(3_00_00_000, rel=0.001)

    def test_real_return_positive(self):
        result = calculate_fire(12_00_000, inflation_pct=6.0, expected_return_pct=12.0)
        assert result.real_return_pct > 0

    def test_monthly_sip_calculated(self):
        result = calculate_fire(
            annual_expenses=10_00_000,
            current_corpus=0,
            years_to_retirement=20,
        )
        assert result.monthly_sip_needed > 0

    def test_zero_remaining_corpus(self):
        """If existing corpus >= FIRE number, monthly SIP should be 0."""
        result = calculate_fire(
            annual_expenses=10_00_000,
            current_corpus=3_00_00_000,  # Already reached FIRE
            years_to_retirement=10,
        )
        # SIP needed is 0 since remaining = 0
        assert result.monthly_sip_needed == 0.0

    def test_invalid_return_lt_inflation(self):
        with pytest.raises(ValueError, match="exceed inflation"):
            calculate_fire(10_00_000, inflation_pct=10.0, expected_return_pct=5.0)


class TestYearsToFIRE:
    def test_returns_float(self):
        years = years_to_reach_fire(
            fire_number=3_00_00_000,
            monthly_sip=30_000,
            annual_return_pct=12.0,
            current_corpus=0,
        )
        assert isinstance(years, float)
        assert 0 < years < 100

    def test_already_at_fire(self):
        years = years_to_reach_fire(
            fire_number=1_00_000,
            monthly_sip=10_000,
            annual_return_pct=12.0,
            current_corpus=1_00_000,
        )
        assert years == 0.0
