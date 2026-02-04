"""Base price provider interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date


@dataclass
class FetchedPrice:
    """Represents a price fetched from a provider.

    Attributes:
        date: The date of the price.
        price: The price value.

    """

    date: date
    price: float


class PriceProvider(ABC):
    """Abstract base class for price providers.

    All price providers must implement the fetch_prices method.

    Attributes:
        name: Unique identifier for the provider.

    """

    name: str

    @abstractmethod
    async def fetch_prices(
        self,
        symbol: str,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[FetchedPrice]:
        """Fetch prices for a symbol within a date range.

        Args:
            symbol: The ticker/symbol to fetch prices for.
            start_date: Start of date range (defaults to today).
            end_date: End of date range (defaults to today).

        Returns:
            List of FetchedPrice objects containing date and price.

        Raises:
            ProviderError: If fetching fails.

        """


class ProviderError(Exception):
    """Exception raised when a provider fails to fetch prices."""

    def __init__(self, provider: str, symbol: str, message: str) -> None:
        """Initialize ProviderError.

        Args:
            provider: Name of the provider that failed.
            symbol: Symbol that was being fetched.
            message: Error description.

        """
        self.provider = provider
        self.symbol = symbol
        self.message = message
        super().__init__(f'[{provider}] Failed to fetch {symbol}: {message}')
