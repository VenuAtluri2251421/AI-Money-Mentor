"""engine/tests/test_xirr.py — Unit tests for the XIRR calculator."""
import datetime
import pytest
from engine.xirr import calculate_xirr, xirr_from_transactions


class TestXIRR:
    def test_simple_annual_investment(self):
        """
        Invest ₹1,00,000 today, receive ₹1,12,000 in exactly one year.
        Expected XIRR ≈ 12%.
        """
        cashflows = [
            (datetime.date(2024, 1, 1), -1_00_000),
            (datetime.date(2025, 1, 1),  1_12_000),
        ]
        result = calculate_xirr(cashflows)
        assert result.xirr_pct == pytest.approx(12.0, abs=0.1)

    def test_sip_style_cashflows(self):
        """12 monthly SIP payments of ₹10,000 → redemption at some amount."""
        cashflows = []
        start = datetime.date(2023, 1, 1)
        for i in range(12):
            d = datetime.date(start.year + (start.month + i - 1) // 12,
                              (start.month + i - 1) % 12 + 1, 1)
            cashflows.append((d, -10_000))
        # Lump-sum redemption at month 13
        cashflows.append((datetime.date(2024, 1, 1), 1_35_000))
        result = calculate_xirr(cashflows)
        assert result.xirr_pct > 0   # positive return

    def test_string_dates_accepted(self):
        cashflows = [
            ("2024-01-01", -50_000),
            ("2025-01-01",  56_000),
        ]
        result = calculate_xirr(cashflows)
        assert result.xirr_pct == pytest.approx(12.0, abs=0.5)

    def test_too_few_cashflows(self):
        with pytest.raises(ValueError, match="at least 2"):
            calculate_xirr([(datetime.date(2024, 1, 1), -1_000)])

    def test_no_sign_change_raises(self):
        cashflows = [
            (datetime.date(2024, 1, 1), -1_000),
            (datetime.date(2024, 6, 1), -2_000),
        ]
        with pytest.raises(ValueError, match="inflows and outflows"):
            calculate_xirr(cashflows)

    def test_result_has_cashflows(self):
        cashflows = [
            (datetime.date(2024, 1, 1), -1_00_000),
            (datetime.date(2025, 1, 1),  1_12_000),
        ]
        result = calculate_xirr(cashflows)
        assert len(result.cashflows) == 2


class TestXIRRFromTransactions:
    def test_basic_dict_format(self):
        """xirr_from_transactions should match calculate_xirr for same data."""
        txns = [
            {"date": "2024-01-01", "amount": -100_000},
            {"date": "2025-01-01", "amount":  112_000},
        ]
        result = xirr_from_transactions(txns)
        assert result.xirr_pct == pytest.approx(12.0, abs=0.1)

    def test_units_field_ignored(self):
        """The 'units' field must be accepted and silently ignored."""
        txns = [
            {"date": "2024-01-01", "amount": -100_000, "units": 50.123},
            {"date": "2025-01-01", "amount":  112_000, "units": 0},
        ]
        result = xirr_from_transactions(txns)
        assert result.xirr_pct == pytest.approx(12.0, abs=0.1)

    def test_raises_with_single_transaction(self):
        txns = [{"date": "2024-01-01", "amount": -1000}]
        with pytest.raises(ValueError, match="at least 2"):
            xirr_from_transactions(txns)
