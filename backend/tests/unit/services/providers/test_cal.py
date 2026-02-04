"""Unit tests for CAL price provider."""

from datetime import date, timedelta

import pytest

from app.services.providers.cal import CALProvider


class TestCALProvider:
    """Tests for CAL provider."""

    def test_cal_provider_name(self):
        """Test CAL provider has correct name."""
        provider = CALProvider()
        assert provider.name == 'cal'

    @pytest.mark.asyncio
    async def test_fetch_prices_single_day(self):
        """Test fetching prices for a single day."""
        provider = CALProvider()
        today = date.today()

        prices = await provider.fetch_prices('TEST', start_date=today, end_date=today)

        assert len(prices) == 1
        assert prices[0].date == today

    @pytest.mark.asyncio
    async def test_fetch_prices_date_range(self):
        """Test fetching prices for a date range returns correct number of prices."""
        provider = CALProvider()
        start = date(2026, 1, 1)
        end = date(2026, 1, 10)  # 10 days

        prices = await provider.fetch_prices('TEST', start_date=start, end_date=end)

        assert len(prices) == 10
        assert prices[0].date == start
        assert prices[-1].date == end

    @pytest.mark.asyncio
    async def test_fetch_prices_defaults_to_today(self):
        """Test fetching without dates defaults to today only."""
        provider = CALProvider()
        today = date.today()

        prices = await provider.fetch_prices('TEST')

        assert len(prices) == 1
        assert prices[0].date == today

    @pytest.mark.asyncio
    async def test_prices_in_valid_range(self):
        """Test all generated prices are between 1.0 and 10.0."""
        provider = CALProvider()
        start = date(2026, 1, 1)
        end = date(2026, 1, 31)

        prices = await provider.fetch_prices('TEST', start_date=start, end_date=end)

        for price in prices:
            assert 1.0 <= price.price <= 10.0

    @pytest.mark.asyncio
    async def test_prices_have_correct_dates(self):
        """Test prices have sequential dates."""
        provider = CALProvider()
        start = date(2026, 1, 1)
        end = date(2026, 1, 5)

        prices = await provider.fetch_prices('TEST', start_date=start, end_date=end)

        expected_date = start
        for price in prices:
            assert price.date == expected_date
            expected_date += timedelta(days=1)
