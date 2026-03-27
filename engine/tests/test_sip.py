"""engine/tests/test_sip.py — Unit tests for the SIP calculator."""
import pytest
from engine.sip import calculate_sip, required_sip


class TestCalculateSIP:
    def test_basic_returns(self):
        """Standard 12% for 10 years — maturity should be ~₹23.23 lakh."""
        result = calculate_sip(10_000, 12.0, 10)
        assert result.maturity_amount == pytest.approx(23_23_391, rel=0.01)
        assert result.total_invested == 12_00_000
        assert result.wealth_gained > 0

    def test_zero_return(self):
        """At 0% return, maturity == total invested."""
        result = calculate_sip(5_000, 0.0, 5)
        assert result.maturity_amount == pytest.approx(3_00_000, rel=0.001)
        assert result.maturity_amount == pytest.approx(result.total_invested, rel=0.001)

    def test_absolute_return_pct(self):
        result = calculate_sip(10_000, 12.0, 10)
        expected = (result.wealth_gained / result.total_invested) * 100
        assert result.absolute_return_pct == pytest.approx(expected, rel=0.001)

    def test_invalid_monthly_investment(self):
        with pytest.raises(ValueError, match="monthly_investment"):
            calculate_sip(-100, 12.0, 5)

    def test_invalid_tenure(self):
        with pytest.raises(ValueError, match="tenure_years"):
            calculate_sip(1000, 12.0, 0)

    def test_negative_return_raises(self):
        with pytest.raises(ValueError, match="annual_return_pct"):
            calculate_sip(1000, -1.0, 5)


class TestRequiredSIP:
    def test_reverse_sip_roundtrip(self):
        """required_sip → calculate_sip should recover the target amount."""
        target = 50_00_000
        rate = 12.0
        years = 15
        monthly = required_sip(target, rate, years)
        result = calculate_sip(monthly, rate, years)
        assert result.maturity_amount == pytest.approx(target, rel=0.01)

    def test_zero_return_reverse(self):
        monthly = required_sip(1_00_000, 0.0, 10)
        assert monthly == pytest.approx(1_00_000 / 120, rel=0.001)

    def test_invalid_target(self):
        with pytest.raises(ValueError):
            required_sip(-1000, 12, 5)
