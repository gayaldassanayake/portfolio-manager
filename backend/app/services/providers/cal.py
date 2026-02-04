"""CAL price provider (placeholder with random values)."""

import logging
import random
from datetime import date, timedelta

from app.services.providers.base import FetchedPrice, PriceProvider

logger = logging.getLogger(__name__)


class CALProvider(PriceProvider):
    """Placeholder price provider returning random values.

    This provider generates random prices in the 1.0-10.0 range.
    Intended for development/testing until real implementation is added.
    """

    name = 'cal'

    async def fetch_prices(
        self,
        symbol: str,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[FetchedPrice]:
        """Generate random prices for the given date range.

        Args:
            symbol: Symbol (not used, but required by interface).
            start_date: Start of date range (defaults to today).
            end_date: End of date range (defaults to today).

        Returns:
            List of FetchedPrice objects with random prices.

        """
        today = date.today()
        start = start_date or today
        end = end_date or today

        logger.info(f'[{self.name}] Generating random prices for {symbol} from {start} to {end}')

        prices = []
        current_date = start

        while current_date <= end:
            # Generate random price between 1.0 and 10.0
            price = round(random.uniform(1.0, 10.0), 4)
            prices.append(FetchedPrice(date=current_date, price=price))
            current_date += timedelta(days=1)

        logger.info(f'[{self.name}] Generated {len(prices)} prices for {symbol}')
        return prices
