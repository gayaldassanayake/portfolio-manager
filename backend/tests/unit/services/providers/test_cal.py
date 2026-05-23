"""Unit tests for CAL price provider."""

from datetime import date
from unittest.mock import AsyncMock, Mock, patch

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
        """unit_price is the NAV; cre_price/red_price map to buy/sell."""
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

        # NAV comes from unit_price; buy from cre_price, sell from red_price.
        assert prices[0].price == 25.5
        assert prices[0].buy_price == pytest.approx(25.625)
        assert prices[0].sell_price == pytest.approx(25.375)

    @pytest.mark.asyncio
    async def test_fetch_prices_buy_sell_absent_for_non_equity(self):
        """Funds without a spread report None buy/sell prices."""
        provider = CALProvider()

        mock_response = {
            'IGF': [
                {
                    'date': '2026-02-01',
                    'unit_price': '39.1854000000',
                    'red_price': None,
                    'cre_price': None,
                }
            ]
        }

        with patch.object(provider, '_fetch_from_api', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_response

            prices = await provider.fetch_prices('IGF', start_date=date(2026, 2, 1))

        assert prices[0].buy_price is None
        assert prices[0].sell_price is None

    @pytest.mark.asyncio
    async def test_fetch_prices_backfills_below_recent_window(self):
        """Dates older than the earliest getUTPrices date are backfilled via proxy."""
        provider = CALProvider()

        # getUTPrices recent window starts 2026-05-01.
        recent_response = {
            'QEF': [
                {'date': '2026-05-01', 'unit_price': '50.00', 'red_price': None, 'cre_price': None},
                {'date': '2026-05-02', 'unit_price': '50.10', 'red_price': None, 'cre_price': None},
            ]
        }

        with (
            patch.object(provider, '_fetch_from_api', new_callable=AsyncMock) as mock_recent,
            patch.object(provider, '_fetch_historical_prices', new_callable=AsyncMock) as mock_hist,
        ):
            mock_recent.return_value = recent_response
            mock_hist.return_value = {
                date(2026, 4, 29): 49.0,
                date(2026, 4, 30): 49.5,
            }

            prices = await provider.fetch_prices(
                'QEF', start_date=date(2026, 4, 29), end_date=date(2026, 5, 2)
            )

        # Backfill called only with the dates below the recent window's earliest date.
        mock_hist.assert_awaited_once()
        _, missing = mock_hist.await_args.args
        assert missing == [date(2026, 4, 29), date(2026, 4, 30)]

        # Result merges backfill + recent, sorted oldest first.
        assert [p.date for p in prices] == [
            date(2026, 4, 29),
            date(2026, 4, 30),
            date(2026, 5, 1),
            date(2026, 5, 2),
        ]
        assert prices[0].price == 49.0
        assert prices[-1].price == pytest.approx(50.10)
        # The proxy backfill only returns a NAV, so it carries no buy/sell.
        assert prices[0].buy_price is None
        assert prices[0].sell_price is None

    @pytest.mark.asyncio
    async def test_fetch_prices_skips_known_dates_in_backfill(self):
        """known_dates are excluded from the per-date historical backfill."""
        provider = CALProvider()

        recent_response = {
            'QEF': [
                {'date': '2026-05-01', 'unit_price': '50.00', 'red_price': None, 'cre_price': None},
            ]
        }

        with (
            patch.object(provider, '_fetch_from_api', new_callable=AsyncMock) as mock_recent,
            patch.object(provider, '_fetch_historical_prices', new_callable=AsyncMock) as mock_hist,
        ):
            mock_recent.return_value = recent_response
            mock_hist.return_value = {date(2026, 4, 30): 49.5}

            await provider.fetch_prices(
                'QEF',
                start_date=date(2026, 4, 28),
                end_date=date(2026, 5, 1),
                known_dates={date(2026, 4, 28), date(2026, 4, 29)},
            )

        # Apr 28/29 already persisted -> only Apr 30 is backfilled.
        _, missing = mock_hist.await_args.args
        assert missing == [date(2026, 4, 30)]

    @pytest.mark.asyncio
    async def test_fetch_prices_no_backfill_within_window(self):
        """No proxy backfill when the whole range is within the getUTPrices window."""
        provider = CALProvider()

        recent_response = {
            'IGF': [
                {'date': '2026-05-01', 'unit_price': '39.00', 'red_price': None, 'cre_price': None},
                {'date': '2026-05-02', 'unit_price': '39.10', 'red_price': None, 'cre_price': None},
            ]
        }

        with (
            patch.object(provider, '_fetch_from_api', new_callable=AsyncMock) as mock_recent,
            patch.object(provider, '_fetch_historical_prices', new_callable=AsyncMock) as mock_hist,
        ):
            mock_recent.return_value = recent_response

            prices = await provider.fetch_prices(
                'IGF', start_date=date(2026, 5, 1), end_date=date(2026, 5, 2)
            )

        mock_hist.assert_not_awaited()
        assert len(prices) == 2

    @pytest.mark.asyncio
    async def test_fetch_historical_prices_skips_failures(self):
        """A failed/missing single date is skipped, not fatal to the backfill."""
        provider = CALProvider()

        async def fake_single(client, fund_code, odate):
            if odate == date(2024, 6, 2):
                raise httpx.RequestError('boom')
            if odate == date(2024, 6, 3):
                return None  # fund/OLD_PRICE absent
            return 43.0

        with patch.object(provider, '_fetch_historical_price', side_effect=fake_single):
            result = await provider._fetch_historical_prices(
                'QEF', [date(2024, 6, 1), date(2024, 6, 2), date(2024, 6, 3)]
            )

        assert result == {date(2024, 6, 1): 43.0}

    @pytest.mark.asyncio
    async def test_fetch_historical_price_extracts_old_price(self):
        """_fetch_historical_price returns the matching fund's OLD_PRICE."""
        provider = CALProvider()

        payload = {
            'UTMS_FUND': [
                {'FUND': 'IGF', 'OLD_DATE': '2024-06-01', 'OLD_PRICE': '36.50'},
                {'FUND': 'QEF', 'OLD_DATE': '2024-06-01', 'OLD_PRICE': '43.2661000000'},
            ]
        }
        mock_response = Mock()
        mock_response.json.return_value = payload
        mock_response.raise_for_status = Mock()
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response

        price = await provider._fetch_historical_price(mock_client, 'QEF', date(2024, 6, 1))

        assert price == pytest.approx(43.2661)
        # Proxy receives the analytics URL with the requested odate.
        sent_url = mock_client.post.call_args.kwargs['json']['url']
        assert "odate='2024-06-01'" in sent_url

    @pytest.mark.asyncio
    async def test_fetch_from_api_correct_params(self):
        """Test that _fetch_from_api sends correct parameters."""
        provider = CALProvider()

        mock_response_json = {'IGF': []}

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_response.json.return_value = AsyncMock(return_value=mock_response_json)
            mock_response.raise_for_status = Mock()
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
