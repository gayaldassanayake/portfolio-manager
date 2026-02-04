"""Tests for interest calculator service."""

from datetime import datetime, timedelta, timezone

import pytest

from app.services.interest_calculator import (
    calculate_compound_interest,
    calculate_current_value,
    calculate_simple_interest,
)


class TestSimpleInterest:
    """Tests for simple interest calculation."""

    def test_calculate_simple_interest_1_year(self):
        """Test simple interest for 1 year."""
        # 10000 at 8% for 365 days = 800
        interest = calculate_simple_interest(10000, 8, 365)
        assert interest == 800.0

    def test_calculate_simple_interest_6_months(self):
        """Test simple interest for 6 months."""
        # 10000 at 8% for 182.5 days (half year) = 400
        interest = calculate_simple_interest(10000, 8, 182)
        assert interest == 398.90  # 10000 * 0.08 * (182/365) = 398.90

    def test_calculate_simple_interest_high_rate(self):
        """Test simple interest with high rate."""
        # 5000 at 12.5% for 365 days = 625
        interest = calculate_simple_interest(5000, 12.5, 365)
        assert interest == 625.0

    def test_calculate_simple_interest_partial_year(self):
        """Test simple interest for 90 days."""
        # 20000 at 7.5% for 90 days
        interest = calculate_simple_interest(20000, 7.5, 90)
        expected = 20000 * 0.075 * (90 / 365)
        assert interest == round(expected, 2)

    def test_calculate_simple_interest_same_day(self):
        """Test simple interest for 0 days."""
        interest = calculate_simple_interest(10000, 8, 0)
        assert interest == 0.0

    def test_calculate_simple_interest_negative_principal(self):
        """Test simple interest with negative principal."""
        interest = calculate_simple_interest(-10000, 8, 365)
        assert interest == 0.0

    def test_calculate_simple_interest_negative_rate(self):
        """Test simple interest with negative rate."""
        interest = calculate_simple_interest(10000, -8, 365)
        assert interest == 0.0

    def test_calculate_simple_interest_zero_principal(self):
        """Test simple interest with zero principal."""
        interest = calculate_simple_interest(0, 8, 365)
        assert interest == 0.0


class TestCompoundInterest:
    """Tests for compound interest calculation."""

    def test_calculate_compound_interest_annually_1_year(self):
        """Test compound interest annually for 1 year."""
        # 10000 at 8% compounded annually for 365 days
        # A = 10000 * (1 + 0.08/1)^(1*1) = 10800
        interest = calculate_compound_interest(10000, 8, 365, 'annually')
        assert interest == 800.0

    def test_calculate_compound_interest_monthly(self):
        """Test compound interest monthly for 1 year."""
        # 10000 at 8% compounded monthly for 365 days
        # A = 10000 * (1 + 0.08/12)^(12*1) = 10830 approx
        interest = calculate_compound_interest(10000, 8, 365, 'monthly')
        assert interest == pytest.approx(830.0, rel=1e-2)

    def test_calculate_compound_interest_quarterly(self):
        """Test compound interest quarterly for 1 year."""
        # 10000 at 8% compounded quarterly for 365 days
        # A = 10000 * (1 + 0.08/4)^(4*1) = 10824.32
        interest = calculate_compound_interest(10000, 8, 365, 'quarterly')
        assert interest == pytest.approx(824.32, rel=1e-2)

    def test_calculate_compound_interest_at_maturity(self):
        """Test compound interest at maturity (same as annually)."""
        interest = calculate_compound_interest(10000, 8, 365, 'at_maturity')
        assert interest == 800.0

    def test_calculate_compound_interest_6_months(self):
        """Test compound interest for 6 months."""
        # 10000 at 8% compounded monthly for 182 days (approx 0.5 years)
        interest = calculate_compound_interest(10000, 8, 182, 'monthly')
        # Should be less than 400 (simple) but more due to compounding
        assert 390 < interest < 410

    def test_calculate_compound_interest_high_rate(self):
        """Test compound interest with high rate."""
        # 5000 at 12.5% compounded monthly for 365 days
        interest = calculate_compound_interest(5000, 12.5, 365, 'monthly')
        # Should be more than simple (625)
        assert interest > 625

    def test_calculate_compound_interest_zero_days(self):
        """Test compound interest for 0 days."""
        interest = calculate_compound_interest(10000, 8, 0, 'monthly')
        assert interest == 0.0

    def test_calculate_compound_interest_negative_principal(self):
        """Test compound interest with negative principal."""
        interest = calculate_compound_interest(-10000, 8, 365, 'monthly')
        assert interest == 0.0

    def test_calculate_compound_interest_2_years_monthly(self):
        """Test compound interest for 2 years with monthly compounding."""
        # 10000 at 8% for 730 days (2 years)
        interest = calculate_compound_interest(10000, 8, 730, 'monthly')
        # A = 10000 * (1 + 0.08/12)^(12*2) ≈ 11,728
        assert interest == pytest.approx(1728.0, rel=1e-1)


class TestCurrentValue:
    """Tests for current value calculation."""

    def test_current_value_simple_active_fd(self):
        """Test current value for active FD with simple interest."""
        start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        maturity_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
        as_of_date = datetime(2024, 7, 1, tzinfo=timezone.utc)  # 6 months in

        current_value, accrued, days_to_maturity = calculate_current_value(
            principal=10000,
            annual_rate=8,
            start_date=start_date,
            maturity_date=maturity_date,
            calculation_type='simple',
            payout_frequency='at_maturity',
            as_of_date=as_of_date,
        )

        # 181 days elapsed (Jan 1 to Jul 1)
        expected_interest = calculate_simple_interest(10000, 8, 181)
        assert accrued == pytest.approx(expected_interest, rel=1e-2)
        assert current_value == pytest.approx(10000 + expected_interest, rel=1e-2)
        assert 180 < days_to_maturity < 186  # approximately 6 months remaining

    def test_current_value_compound_active_fd(self):
        """Test current value for active FD with compound interest."""
        start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        maturity_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
        as_of_date = datetime(2024, 7, 1, tzinfo=timezone.utc)

        current_value, accrued, days_to_maturity = calculate_current_value(
            principal=10000,
            annual_rate=8,
            start_date=start_date,
            maturity_date=maturity_date,
            calculation_type='compound',
            payout_frequency='monthly',
            as_of_date=as_of_date,
        )

        # Should have more interest than simple due to compounding
        simple_interest = calculate_simple_interest(10000, 8, 181)
        assert accrued > simple_interest
        assert current_value == 10000 + accrued
        assert 180 < days_to_maturity < 186

    def test_current_value_matured_fd(self):
        """Test current value for matured FD (should cap at maturity)."""
        start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        maturity_date = datetime(2024, 7, 1, tzinfo=timezone.utc)
        as_of_date = datetime(2024, 12, 31, tzinfo=timezone.utc)  # After maturity

        current_value, accrued, days_to_maturity = calculate_current_value(
            principal=10000,
            annual_rate=8,
            start_date=start_date,
            maturity_date=maturity_date,
            calculation_type='simple',
            payout_frequency='at_maturity',
            as_of_date=as_of_date,
        )

        # Interest should be calculated only up to maturity (181 days)
        expected_interest = calculate_simple_interest(10000, 8, 181)
        assert accrued == pytest.approx(expected_interest, rel=1e-2)
        assert current_value == pytest.approx(10000 + expected_interest, rel=1e-2)
        assert days_to_maturity < 0  # Negative indicates matured

    def test_current_value_on_maturity_date(self):
        """Test current value exactly on maturity date."""
        start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        maturity_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
        as_of_date = datetime(2025, 1, 1, tzinfo=timezone.utc)

        current_value, accrued, days_to_maturity = calculate_current_value(
            principal=10000,
            annual_rate=8,
            start_date=start_date,
            maturity_date=maturity_date,
            calculation_type='simple',
            payout_frequency='at_maturity',
            as_of_date=as_of_date,
        )

        # Full year of interest
        expected_interest = calculate_simple_interest(10000, 8, 365)
        assert accrued == pytest.approx(expected_interest, rel=1e-2)
        assert current_value == pytest.approx(10000 + expected_interest, rel=1e-2)
        assert days_to_maturity == 0

    def test_current_value_before_start_date(self):
        """Test current value before start date (edge case)."""
        start_date = datetime(2024, 7, 1, tzinfo=timezone.utc)
        maturity_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
        as_of_date = datetime(2024, 1, 1, tzinfo=timezone.utc)  # Before start

        current_value, accrued, days_to_maturity = calculate_current_value(
            principal=10000,
            annual_rate=8,
            start_date=start_date,
            maturity_date=maturity_date,
            calculation_type='simple',
            payout_frequency='at_maturity',
            as_of_date=as_of_date,
        )

        # No interest should accrue before start date
        assert accrued == 0.0
        assert current_value == 10000
        assert days_to_maturity > 0

    def test_current_value_defaults_to_now(self):
        """Test current value defaults to current time."""
        start_date = datetime.now(timezone.utc) - timedelta(days=100)
        maturity_date = datetime.now(timezone.utc) + timedelta(days=100)

        current_value, accrued, days_to_maturity = calculate_current_value(
            principal=10000,
            annual_rate=8,
            start_date=start_date,
            maturity_date=maturity_date,
            calculation_type='simple',
            payout_frequency='at_maturity',
        )

        # Should have some interest accrued
        assert accrued > 0
        assert current_value > 10000
        assert 95 < days_to_maturity < 105  # Approximately 100 days

    def test_current_value_naive_datetime_handling(self):
        """Test current value handles naive datetimes."""
        # Naive datetimes (no timezone)
        start_date = datetime(2024, 1, 1)
        maturity_date = datetime(2025, 1, 1)
        as_of_date = datetime(2024, 7, 1)

        current_value, accrued, days_to_maturity = calculate_current_value(
            principal=10000,
            annual_rate=8,
            start_date=start_date,
            maturity_date=maturity_date,
            calculation_type='simple',
            payout_frequency='at_maturity',
            as_of_date=as_of_date,
        )

        # Should work without errors
        assert accrued > 0
        assert current_value > 10000
        assert days_to_maturity > 0

    def test_current_value_same_start_and_maturity(self):
        """Test current value when start and maturity are same (edge case)."""
        start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        maturity_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        as_of_date = datetime(2024, 1, 1, tzinfo=timezone.utc)

        current_value, accrued, days_to_maturity = calculate_current_value(
            principal=10000,
            annual_rate=8,
            start_date=start_date,
            maturity_date=maturity_date,
            calculation_type='simple',
            payout_frequency='at_maturity',
            as_of_date=as_of_date,
        )

        # Zero days means zero interest
        assert accrued == 0.0
        assert current_value == 10000
        assert days_to_maturity == 0
