"""Unit tests for CAL price provider."""

from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.services.providers.base import ProviderError
from app.services.providers.cal import CALProvider


class TestCALProvider:
    """Tests for CAL provider."""

    def test_cal_provider_name(self):
        """Test CAL provider has correct name."""
        provider = CALProvider()
        assert provider.name == 'cal'

    def test_valid_funds(self):
        """Test that valid fund codes are defined."""
        provider = CALProvider()
        assert 'IGF' in provider.VALID_FUNDS
        assert 'QEF' in provider.VALID_FUNDS
        assert len(provider.VALID_FUNDS) == 13

    @pytest.mark.asyncio
    async def test_fetch_prices_success(self):
        """Test successful price fetch from CAL API."""
        provider = CALProvider()

        # Mock API response
        mock_response = {
            'IGF': [
                {
                    'date': '2026-02-01',
                    'unit_price': '39.1854000000',
                    'red_price': None,
                    'cre_price': None,
                },
                {
                    'date': '2026-02-02',
                    'unit_price': '39.2100000000',
                    'red_price': None,
                    'cre_price': None,
                },
            ]
        }

        with patch.object(provider, '_fetch_from_api', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_response

            prices = await provider.fetch_prices(
                'IGF', start_date=date(2026, 2, 1), end_date=date(2026, 2, 2)
            )

        assert len(prices) == 2
        assert prices[0].date == date(2026, 2, 1)
        assert prices[0].price == pytest.approx(39.1854, rel=1e-4)
        assert prices[1].date == date(2026, 2, 2)
        assert prices[1].price == pytest.approx(39.21, rel=1e-4)

    @pytest.mark.asyncio
    async def test_fetch_prices_filters_by_date_range(self):
        """Test that prices are correctly filtered to requested date range."""
        provider = CALProvider()

        # Mock API returns 5 days of data
        mock_response = {
            'QEF': [
                {'date': '2026-01-28', 'unit_price': '10.00', 'red_price': None, 'cre_price': None},
                {'date': '2026-01-29', 'unit_price': '10.10', 'red_price': None, 'cre_price': None},
                {'date': '2026-01-30', 'unit_price': '10.20', 'red_price': None, 'cre_price': None},
                {'date': '2026-01-31', 'unit_price': '10.30', 'red_price': None, 'cre_price': None},
                {'date': '2026-02-01', 'unit_price': '10.40', 'red_price': None, 'cre_price': None},
            ]
        }

        with patch.object(provider, '_fetch_from_api', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_response

            # Request only Jan 30-31
            prices = await provider.fetch_prices(
                'QEF', start_date=date(2026, 1, 30), end_date=date(2026, 1, 31)
            )

        assert len(prices) == 2
        assert prices[0].date == date(2026, 1, 30)
        assert prices[1].date == date(2026, 1, 31)

    @pytest.mark.asyncio
    async def test_fetch_prices_invalid_symbol(self):
        """Test ProviderError raised for invalid fund code."""
        provider = CALProvider()

        with pytest.raises(ProviderError) as exc_info:
            await provider.fetch_prices('INVALID', start_date=date(2026, 2, 1))

        assert exc_info.value.provider == 'cal'
        assert exc_info.value.symbol == 'INVALID'
        assert 'Unknown fund code' in exc_info.value.message

    @pytest.mark.asyncio
    async def test_fetch_prices_case_insensitive(self):
        """Test that fund codes work regardless of case."""
        provider = CALProvider()

        mock_response = {
            'IGF': [
                {'date': '2026-02-01', 'unit_price': '39.00', 'red_price': None, 'cre_price': None}
            ]
        }

        with patch.object(provider, '_fetch_from_api', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_response

            # Use lowercase symbol
            prices = await provider.fetch_prices('igf', start_date=date(2026, 2, 1))

        assert len(prices) == 1
        assert prices[0].price == 39.0

    @pytest.mark.asyncio
    async def test_fetch_prices_network_error(self):
        """Test ProviderError raised on network failure."""
        provider = CALProvider()

        with patch.object(provider, '_fetch_from_api', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.side_effect = httpx.RequestError('Connection timeout')

            with pytest.raises(ProviderError) as exc_info:
                await provider.fetch_prices('IGF', start_date=date(2026, 2, 1))

        assert exc_info.value.provider == 'cal'
        assert exc_info.value.symbol == 'IGF'
        assert 'Network error' in exc_info.value.message

    @pytest.mark.asyncio
    async def test_fetch_prices_invalid_response_format(self):
        """Test ProviderError raised for malformed JSON."""
        provider = CALProvider()

        # Invalid response - not matching expected schema
        mock_response = {'invalid': 'data'}

        with patch.object(provider, '_fetch_from_api', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_response

            with pytest.raises(ProviderError) as exc_info:
                await provider.fetch_prices('IGF', start_date=date(2026, 2, 1))

        assert exc_info.value.provider == 'cal'
        # Error message will contain either validation error or "not found" message
        assert (
            'Invalid API response format' in exc_info.value.message
            or 'not found' in exc_info.value.message
        )

    @pytest.mark.asyncio
    async def test_fetch_prices_empty_response(self):
        """Test ProviderError raised when API returns empty price array."""
        provider = CALProvider()

        mock_response = {'IGF': []}  # Empty array

        with patch.object(provider, '_fetch_from_api', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_response

            with pytest.raises(ProviderError) as exc_info:
                await provider.fetch_prices('IGF', start_date=date(2026, 2, 1))

        assert 'No price data available' in exc_info.value.message

    @pytest.mark.asyncio
    async def test_fetch_prices_sorts_by_date(self):
        """Test that prices are sorted by date (oldest first)."""
        provider = CALProvider()

        # Return prices in reverse order
        mock_response = {
            'IGF': [
                {'date': '2026-02-03', 'unit_price': '39.30', 'red_price': None, 'cre_price': None},
                {'date': '2026-02-01', 'unit_price': '39.10', 'red_price': None, 'cre_price': None},
                {'date': '2026-02-02', 'unit_price': '39.20', 'red_price': None, 'cre_price': None},
            ]
        }

        with patch.object(provider, '_fetch_from_api', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_response

            prices = await provider.fetch_prices(
                'IGF', start_date=date(2026, 2, 1), end_date=date(2026, 2, 3)
            )

        # Should be sorted oldest to newest
        assert prices[0].date == date(2026, 2, 1)
        assert prices[1].date == date(2026, 2, 2)
        assert prices[2].date == date(2026, 2, 3)

    @pytest.mark.asyncio
    async def test_fetch_prices_uses_unit_price(self):
        """Test that unit_price field is used for NAV."""
        provider = CALProvider()

        # Mock response with all price fields
        mock_response = {
            'QEF': [
                {
                    'date': '2026-02-01',
                    'unit_price': '25.5000',
                    'red_price': '25.3750',  # Redemption (sell) price
                    'cre_price': '25.6250',  # Creation (buy) price
                }
            ]
        }

        with patch.object(provider, '_fetch_from_api', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_response

            prices = await provider.fetch_prices('QEF', start_date=date(2026, 2, 1))

        # Should use unit_price, not red_price or cre_price
        assert prices[0].price == 25.5

    @pytest.mark.asyncio
    async def test_fetch_from_api_correct_params(self):
        """Test that _fetch_from_api sends correct parameters."""
        provider = CALProvider()

        mock_response_json = {'IGF': []}

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.json.return_value = mock_response_json
            mock_response.raise_for_status = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = AsyncMock()
            mock_client_class.return_value = mock_client

            await provider._fetch_from_api('IGF')

            # Verify correct URL and parameters
            mock_client.get.assert_called_once()
            call_args = mock_client.get.call_args
            assert call_args.kwargs['params']['action'] == 'getUTPrices'
            assert call_args.kwargs['params']['fund'] == 'IGF'
            assert 'User-Agent' in call_args.kwargs['headers']
