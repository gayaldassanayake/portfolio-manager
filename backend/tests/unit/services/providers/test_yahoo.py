"""Unit tests for Yahoo Finance price provider."""

from datetime import date
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from app.services.providers.base import ProviderError
from app.services.providers.yahoo import YahooProvider


class TestYahooProvider:
    """Tests for Yahoo Finance provider."""

    def test_yahoo_provider_name(self):
        """Test Yahoo provider has correct name."""
        provider = YahooProvider()
        assert provider.name == 'yahoo'

    @pytest.mark.asyncio
    async def test_fetch_prices_success(self):
        """Test successful price fetch from Yahoo Finance."""
        provider = YahooProvider()

        # Create mock DataFrame mimicking yfinance response
        mock_data = pd.DataFrame(
            {
                'Open': [150.0, 151.0],
                'High': [152.0, 153.0],
                'Low': [149.0, 150.0],
                'Close': [151.50, 152.25],
                'Volume': [1000000, 1100000],
            },
            index=pd.to_datetime(['2026-01-15', '2026-01-16']),
        )

        with patch('app.services.providers.yahoo.yf.Ticker') as mock_ticker_class:
            mock_ticker = MagicMock()
            mock_ticker.history.return_value = mock_data
            mock_ticker_class.return_value = mock_ticker

            prices = await provider.fetch_prices(
                'AAPL', start_date=date(2026, 1, 15), end_date=date(2026, 1, 16)
            )

        assert len(prices) == 2
        assert prices[0].date == date(2026, 1, 15)
        assert prices[0].price == 151.50
        assert prices[1].date == date(2026, 1, 16)
        assert prices[1].price == 152.25

    @pytest.mark.asyncio
    async def test_fetch_prices_empty_result(self):
        """Test ProviderError raised when no data returned."""
        provider = YahooProvider()

        # Create empty DataFrame
        mock_data = pd.DataFrame()

        with patch('app.services.providers.yahoo.yf.Ticker') as mock_ticker_class:
            mock_ticker = MagicMock()
            mock_ticker.history.return_value = mock_data
            mock_ticker_class.return_value = mock_ticker

            with pytest.raises(ProviderError) as exc_info:
                await provider.fetch_prices(
                    'INVALID', start_date=date(2026, 1, 15), end_date=date(2026, 1, 16)
                )

        assert exc_info.value.provider == 'yahoo'
        assert exc_info.value.symbol == 'INVALID'
        assert 'No price data found' in exc_info.value.message

    @pytest.mark.asyncio
    async def test_fetch_prices_api_error(self):
        """Test ProviderError wraps API exceptions."""
        provider = YahooProvider()

        with patch('app.services.providers.yahoo.yf.Ticker') as mock_ticker_class:
            mock_ticker = MagicMock()
            mock_ticker.history.side_effect = Exception('Network error')
            mock_ticker_class.return_value = mock_ticker

            with pytest.raises(ProviderError) as exc_info:
                await provider.fetch_prices(
                    'AAPL', start_date=date(2026, 1, 15), end_date=date(2026, 1, 16)
                )

        assert exc_info.value.provider == 'yahoo'
        assert 'Network error' in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_fetch_prices_uses_close_price(self):
        """Test that Close price is used as the daily price."""
        provider = YahooProvider()

        mock_data = pd.DataFrame(
            {
                'Open': [100.0],
                'High': [110.0],
                'Low': [95.0],
                'Close': [105.0],  # This should be used
                'Volume': [1000000],
            },
            index=pd.to_datetime(['2026-01-15']),
        )

        with patch('app.services.providers.yahoo.yf.Ticker') as mock_ticker_class:
            mock_ticker = MagicMock()
            mock_ticker.history.return_value = mock_data
            mock_ticker_class.return_value = mock_ticker

            prices = await provider.fetch_prices(
                'AAPL', start_date=date(2026, 1, 15), end_date=date(2026, 1, 15)
            )

        assert prices[0].price == 105.0
