"""Schemas for price fetching operations."""

from datetime import date

from pydantic import BaseModel

from app.schemas.price import PriceResponse


class PriceFetchRequest(BaseModel):
    """Request schema for fetching prices.

    Attributes:
        start_date: Start of date range (defaults to today if not provided).
        end_date: End of date range (defaults to today if not provided).

    """

    start_date: date | None = None
    end_date: date | None = None


class PriceFetchResult(BaseModel):
    """Result of a price fetch operation for a single unit trust.

    Attributes:
        unit_trust_id: ID of the unit trust.
        symbol: Symbol of the unit trust.
        provider: Provider used to fetch prices.
        prices_fetched: Number of prices fetched from provider.
        prices_saved: Number of new prices saved to database.
        prices: List of saved price records.

    """

    unit_trust_id: int
    symbol: str
    provider: str
    prices_fetched: int
    prices_saved: int
    prices: list[PriceResponse]


class PriceFetchError(BaseModel):
    """Error details for a failed price fetch.

    Attributes:
        unit_trust_id: ID of the unit trust that failed.
        symbol: Symbol of the unit trust.
        provider: Provider that was attempted.
        error: Error message.

    """

    unit_trust_id: int
    symbol: str
    provider: str | None
    error: str


class BulkPriceFetchResponse(BaseModel):
    """Response for bulk price fetch operation.

    Attributes:
        total_requested: Total number of unit trusts requested.
        successful: Number of successful fetches.
        failed: Number of failed fetches.
        results: List of successful fetch results.
        errors: List of fetch errors.

    """

    total_requested: int
    successful: int
    failed: int
    results: list[PriceFetchResult]
    errors: list[PriceFetchError]
