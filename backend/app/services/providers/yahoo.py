"""Yahoo Finance price provider."""

import asyncio
import logging
from datetime import date

import yfinance as yf

from app.services.providers.base import FetchedPrice, PriceProvider, ProviderError

logger = logging.getLogger(__name__)


class YahooProvider(PriceProvider):
    """Price provider using Yahoo Finance API.

    Fetches historical price data using the yfinance library.
    """

    name = 'yahoo'

    async def fetch_prices(
        self,
        symbol: str,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[FetchedPrice]:
        """Fetch prices from Yahoo Finance.

        Args:
            symbol: Yahoo Finance ticker symbol.
            start_date: Start of date range (defaults to today).
            end_date: End of date range (defaults to today).

        Returns:
            List of FetchedPrice objects.

        Raises:
            ProviderError: If fetching fails.

        """
        today = date.today()
        start = start_date or today
        end = end_date or today

        logger.info(f'[{self.name}] Fetching prices for {symbol} from {start} to {end}')

        try:
            # yfinance is synchronous, run in thread pool
            prices = await asyncio.to_thread(self._fetch_sync, symbol, start, end)
            logger.info(f'[{self.name}] Fetched {len(prices)} prices for {symbol}')
            return prices
        except ProviderError:
            raise
        except Exception as e:
            logger.error(f'[{self.name}] Error fetching {symbol}: {e}')
            raise ProviderError(self.name, symbol, str(e)) from e

    def _fetch_sync(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
    ) -> list[FetchedPrice]:
        """Fetch prices synchronously from Yahoo Finance.

        Args:
            symbol: Yahoo Finance ticker symbol.
            start_date: Start of date range.
            end_date: End of date range.

        Returns:
            List of FetchedPrice objects.

        Raises:
            ProviderError: If no data is returned.

        """
        ticker = yf.Ticker(symbol)

        # yfinance end date is exclusive, so add one day
        from datetime import timedelta

        end_inclusive = end_date + timedelta(days=1)

        hist = ticker.history(start=start_date, end=end_inclusive)

        if hist.empty:
            raise ProviderError(
                self.name,
                symbol,
                f'No price data found for date range {start_date} to {end_date}',
            )

        prices = []
        for idx, row in hist.iterrows():
            # Use Close price as the daily price
            price_date = idx.date() if hasattr(idx, 'date') else idx
            prices.append(
                FetchedPrice(
                    date=price_date,
                    price=float(row['Close']),
                )
            )

        return prices
