"""CAL price provider for Capital Alliance Unit Trusts.

This provider fetches historical price data from the CAL (Capital Alliance)
Unit Trust API for Sri Lankan unit trust funds.

Two upstream sources are combined:

- ``getUTPrices`` returns a full daily price series but only for a rolling
  window of roughly the last 90 days.
- ``ut_fundsRates`` (reached through the portal's ``bypass-get-url`` proxy)
  returns the NAV on an arbitrary ``odate`` for every fund, one date per call.
  It is the only way to reach prices older than the getUTPrices window, so it
  is used to backfill the gap below the earliest getUTPrices date.
"""

import asyncio
import logging
from datetime import date, timedelta

import httpx

from app.schemas.providers.cal_api import CALPricesResponse, UTMSFundRatesResponse
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

    # Portal proxy that forwards a request to the analytics host and returns
    # its JSON. Used to reach historical NAVs older than the getUTPrices window.
    PROXY_URL = 'https://portal.cal.lk/api/v1/account/bypass-get-url'
    ANALYTICS_URL = 'http://analytics.cal.lk:8081/MobileappDataService/ut_fundsRates.php'

    # Cap concurrent historical (per-date) proxy requests during a backfill.
    MAX_CONCURRENT_HISTORICAL = 8

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
        known_dates: set[date] | None = None,
    ) -> list[FetchedPrice]:
        """Fetch prices from CAL for a date range.

        Recent dates are served from the getUTPrices daily series; dates older
        than that series' earliest entry are backfilled per-date via the
        analytics proxy. Dates in ``known_dates`` are excluded from that
        per-date backfill so already-persisted history is never re-fetched.

        Args:
            symbol: CAL fund code (e.g., 'IGF', 'QEF').
            start_date: Start of date range (defaults to today).
            end_date: End of date range (defaults to today).
            known_dates: Dates already persisted by the caller; skipped during
                the historical backfill.

        Returns:
            List of FetchedPrice objects containing date and price, oldest first.

        Raises:
            ProviderError: If symbol is invalid, network fails, or API returns invalid data.

        """
        known = known_dates or set()
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

        # Recent window: getUTPrices returns a full daily series for ~90 days,
        # including buy/sell prices for funds that quote them.
        recent = await self._fetch_recent_prices(symbol, symbol_upper)
        recent_by_date = {p.date: p for p in recent}

        prices_by_date: dict[date, FetchedPrice] = {
            d: fp for d, fp in recent_by_date.items() if start <= d <= end
        }

        # Historical backfill: dates in range that fall before the earliest date
        # getUTPrices can serve are fetched per-date via the analytics proxy.
        # That source only returns the NAV, so backfilled dates have no buy/sell.
        earliest_recent = min(recent_by_date)
        missing_dates = [
            d
            for d in self._dates_in_range(start, min(end, earliest_recent - timedelta(days=1)))
            if d not in known
        ]
        if missing_dates:
            logger.info(
                f'[{self.name}] Backfilling {len(missing_dates)} historical dates for '
                f'{symbol_upper} below earliest getUTPrices date {earliest_recent}'
            )
            historical = await self._fetch_historical_prices(symbol_upper, missing_dates)
            for d, price in historical.items():
                prices_by_date[d] = FetchedPrice(date=d, price=price)

        fetched_prices = [fp for _, fp in sorted(prices_by_date.items())]

        logger.info(f'[{self.name}] Returning {len(fetched_prices)} prices for {symbol_upper}')

        return fetched_prices

    async def _fetch_recent_prices(self, symbol: str, symbol_upper: str) -> list[FetchedPrice]:
        """Fetch the recent daily price series from getUTPrices.

        Args:
            symbol: Original (caller-supplied) symbol, used for error reporting.
            symbol_upper: Upper-cased fund code used for the API call and lookup.

        Returns:
            List of FetchedPrice for the rolling getUTPrices window.

        Raises:
            ProviderError: On network failure, malformed response, or no data.

        """
        try:
            prices_data = await self._fetch_from_api(symbol_upper)
        except httpx.HTTPError as e:
            logger.error(f'[{self.name}] HTTP error fetching {symbol_upper}: {e}')
            raise ProviderError(self.name, symbol, f'Network error: {e}') from e
        except Exception as e:
            logger.error(f'[{self.name}] Unexpected error fetching {symbol_upper}: {e}')
            raise ProviderError(self.name, symbol, str(e)) from e

        try:
            response = CALPricesResponse.model_validate(prices_data)
        except Exception as e:
            logger.error(f'[{self.name}] Invalid response format for {symbol_upper}: {e}')
            raise ProviderError(self.name, symbol, f'Invalid API response format: {e}') from e

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

        return [
            FetchedPrice(
                date=e.date,
                price=float(e.unit_price),
                buy_price=float(e.cre_price) if e.cre_price is not None else None,
                sell_price=float(e.red_price) if e.red_price is not None else None,
            )
            for e in price_entries
        ]

    @staticmethod
    def _dates_in_range(start: date, end: date) -> list[date]:
        """Return every calendar date in the inclusive [start, end] range."""
        days = (end - start).days
        if days < 0:
            return []
        return [start + timedelta(days=i) for i in range(days + 1)]

    async def _fetch_historical_prices(
        self, fund_code: str, dates: list[date]
    ) -> dict[date, float]:
        """Fetch the NAV for a fund on each given date via the analytics proxy.

        Each date requires its own proxy request (the source returns one
        ``odate`` per call), so requests are bounded by a semaphore. Individual
        date failures are logged and skipped rather than failing the backfill.

        Args:
            fund_code: Upper-cased CAL fund code (e.g. 'QEF').
            dates: Historical dates to fetch.

        Returns:
            Mapping of date to NAV price for the dates that resolved.

        """
        semaphore = asyncio.Semaphore(self.MAX_CONCURRENT_HISTORICAL)

        async with httpx.AsyncClient(timeout=30.0) as client:

            async def fetch_one(target: date) -> tuple[date, float | None]:
                async with semaphore:
                    try:
                        price = await self._fetch_historical_price(client, fund_code, target)
                    except Exception as e:  # noqa: BLE001 - skip individual bad dates
                        logger.warning(
                            f'[{self.name}] Failed historical fetch for {fund_code} '
                            f'on {target}: {e}'
                        )
                        return target, None
                    return target, price

            results = await asyncio.gather(*(fetch_one(d) for d in dates))

        return {d: price for d, price in results if price is not None}

    async def _fetch_historical_price(
        self, client: httpx.AsyncClient, fund_code: str, odate: date
    ) -> float | None:
        """Fetch a single fund's NAV on a specific date via the proxy.

        Args:
            client: Shared async HTTP client.
            fund_code: Upper-cased CAL fund code.
            odate: The historical date to look up.

        Returns:
            The NAV price, or None if the fund or its OLD_PRICE is absent.

        """
        inner_url = f"{self.ANALYTICS_URL}?odate='{odate.isoformat()}'"
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; PortfolioManager/1.0)',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }

        response = await client.post(self.PROXY_URL, json={'url': inner_url}, headers=headers)
        response.raise_for_status()

        parsed = UTMSFundRatesResponse.model_validate(response.json())
        for entry in parsed.UTMS_FUND:
            if entry.FUND.upper() == fund_code and entry.OLD_PRICE is not None:
                return float(entry.OLD_PRICE)
        return None

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
