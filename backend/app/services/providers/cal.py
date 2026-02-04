"""CAL price provider for Capital Alliance Unit Trusts.

This provider fetches historical price data from the CAL (Capital Alliance)
Unit Trust API for Sri Lankan unit trust funds.
"""

import logging
from datetime import date

import httpx

from app.schemas.providers.cal_api import CALPricesResponse
from app.services.providers.base import FetchedPrice, PriceProvider, ProviderError

logger = logging.getLogger(__name__)


class CALProvider(PriceProvider):
    """Price provider for Capital Alliance Unit Trusts.

    Fetches historical price data from CAL's unofficial API endpoint.
    The API returns approximately 90 days of historical price data.

    Supported fund codes:
        - IGF: Capital Alliance Investment Grade Fund
        - CDGTF: CAL Fixed Income Opportunities Fund
        - GMMF: CAL Money Market Fund
        - IF: Capital Alliance Income Fund
        - QEF: Capital Alliance Quantitative Equity Fund
        - BF: Capital Alliance Balanced Fund
        - CAHYF: Capital Alliance High Yield Fund
        - CTF: CAL Corporate Treasury Fund
        - MRDF: CAL Medium Risk Debt Fund
        - GF: Capital Alliance Gilt Fund
        - GTF: Capital Alliance Gilt Trading Fund
        - FYOF: CAL Five Year Optimum Fund
        - FYCF: CAL Five Year Corporate Fund

    """

    name = 'cal'
    BASE_URL = 'https://cal.lk/wp-admin/admin-ajax.php'

    # Valid fund codes from CAL API documentation
    VALID_FUNDS = {
        'IGF',
        'CDGTF',
        'GMMF',
        'IF',
        'QEF',
        'BF',
        'CAHYF',
        'CTF',
        'MRDF',
        'GF',
        'GTF',
        'FYOF',
        'FYCF',
    }

    async def fetch_prices(
        self,
        symbol: str,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[FetchedPrice]:
        """Fetch prices from CAL API.

        Args:
            symbol: CAL fund code (e.g., 'IGF', 'QEF').
            start_date: Start of date range (defaults to today).
            end_date: End of date range (defaults to today).

        Returns:
            List of FetchedPrice objects containing date and price.

        Raises:
            ProviderError: If symbol is invalid, network fails, or API returns invalid data.

        """
        today = date.today()
        start = start_date or today
        end = end_date or today

        # Validate symbol early
        symbol_upper = symbol.upper()
        if symbol_upper not in self.VALID_FUNDS:
            raise ProviderError(
                self.name,
                symbol,
                f'Unknown fund code. Valid codes: {", ".join(sorted(self.VALID_FUNDS))}',
            )

        logger.info(f'[{self.name}] Fetching prices for {symbol_upper} from {start} to {end}')

        # Fetch from API
        try:
            prices_data = await self._fetch_from_api(symbol_upper)
        except httpx.HTTPError as e:
            logger.error(f'[{self.name}] HTTP error fetching {symbol_upper}: {e}')
            raise ProviderError(self.name, symbol, f'Network error: {e}') from e
        except Exception as e:
            logger.error(f'[{self.name}] Unexpected error fetching {symbol_upper}: {e}')
            raise ProviderError(self.name, symbol, str(e)) from e

        # Parse response using Pydantic model
        try:
            response = CALPricesResponse.model_validate(prices_data)
        except Exception as e:
            logger.error(f'[{self.name}] Invalid response format for {symbol_upper}: {e}')
            raise ProviderError(self.name, symbol, f'Invalid API response format: {e}') from e

        # Extract prices for the requested fund
        if symbol_upper not in response.root:
            raise ProviderError(
                self.name,
                symbol,
                f'Fund {symbol_upper} not found in API response',
            )

        price_entries = response.root[symbol_upper]

        if not price_entries:
            raise ProviderError(
                self.name,
                symbol,
                f'No price data available for {symbol_upper}',
            )

        # Convert to FetchedPrice and filter by date range
        fetched_prices = []
        for entry in price_entries:
            # Filter to requested date range
            if entry.date < start or entry.date > end:
                continue

            # Use unit_price (NAV) as the price
            fetched_prices.append(
                FetchedPrice(
                    date=entry.date,
                    price=float(entry.unit_price),
                )
            )

        # Sort by date (oldest first)
        fetched_prices.sort(key=lambda p: p.date)

        logger.info(
            f'[{self.name}] Fetched {len(fetched_prices)} prices for {symbol_upper} '
            f'(filtered from {len(price_entries)} total)'
        )

        return fetched_prices

    async def _fetch_from_api(self, fund_code: str) -> dict:
        """Fetch raw price data from CAL API.

        Args:
            fund_code: The fund code to fetch (e.g., 'IGF').

        Returns:
            Raw JSON response from the API.

        Raises:
            httpx.HTTPError: If the HTTP request fails.
            Exception: For other errors (JSON parsing, etc.).

        """
        params = {
            'action': 'getUTPrices',
            'fund': fund_code,
        }

        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; PortfolioManager/1.0)',
            'Accept': 'application/json',
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                self.BASE_URL,
                params=params,
                headers=headers,
            )
            response.raise_for_status()

            # Parse JSON response
            return response.json()
