"""Price management API endpoints."""

import logging
from datetime import date, datetime
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.price import Price
from app.models.unit_trust import UnitTrust
from app.schemas import PriceCreate, PriceResponse, PriceUpdate
from app.schemas.price_fetch import (
    BulkPriceFetchResponse,
    PriceFetchError,
    PriceFetchResult,
)
from app.services.providers import ProviderError, get_available_providers, get_provider

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/api/v1/prices', tags=['Prices'])


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session.

    Yields:
        AsyncSession: Database session.

    """
    async for session in get_db():
        yield session


@router.post('', response_model=PriceResponse, status_code=status.HTTP_201_CREATED)
async def create_price(price: PriceCreate, db: AsyncSession = Depends(get_db)):
    """Create a new price.

    Args:
        price: Price data to create.
        db: Database session.

    Returns:
        PriceResponse: Created price.

    Raises:
        HTTPException: If unit trust not found or price already exists.

    """
    result = await db.execute(select(UnitTrust).where(UnitTrust.id == price.unit_trust_id))
    unit_trust = result.scalar_one_or_none()
    if not unit_trust:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Unit trust not found')

    result = await db.execute(
        select(Price).where(Price.unit_trust_id == price.unit_trust_id, Price.date == price.date)
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Price for this date already exists',
        )

    db_price = Price(**price.model_dump())
    db.add(db_price)
    await db.commit()
    await db.refresh(db_price)
    return db_price


@router.get('', response_model=list[PriceResponse])
async def list_prices(
    unit_trust_id: int | None = Query(None),
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """List prices with optional filters.

    Args:
        unit_trust_id: Filter by unit trust ID.
        start_date: Filter by start date.
        end_date: Filter by end date.
        db: Database session.

    Returns:
        List of prices.

    """
    query = select(Price)
    if unit_trust_id:
        query = query.where(Price.unit_trust_id == unit_trust_id)
    if start_date:
        query = query.where(Price.date >= start_date)
    if end_date:
        query = query.where(Price.date <= end_date)
    query = query.order_by(Price.date.desc())

    result = await db.execute(query)
    prices = result.scalars().all()
    return prices


@router.get('/{price_id}', response_model=PriceResponse)
async def get_price(price_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific price by ID.

    Args:
        price_id: Price ID.
        db: Database session.

    Returns:
        PriceResponse: Price data.

    Raises:
        HTTPException: If price not found.

    """
    result = await db.execute(select(Price).where(Price.id == price_id))
    price = result.scalar_one_or_none()
    if not price:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Price not found')
    return price


@router.put('/{price_id}', response_model=PriceResponse)
async def update_price(price_id: int, price: PriceUpdate, db: AsyncSession = Depends(get_db)):
    """Update a price.

    Args:
        price_id: Price ID.
        price: Updated price data.
        db: Database session.

    Returns:
        PriceResponse: Updated price.

    Raises:
        HTTPException: If price not found.

    """
    result = await db.execute(select(Price).where(Price.id == price_id))
    db_price = result.scalar_one_or_none()
    if not db_price:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Price not found')

    update_data = price.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_price, field, value)

    await db.commit()
    await db.refresh(db_price)
    return db_price


@router.delete('/{price_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_price(price_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a price.

    Args:
        price_id: Price ID.
        db: Database session.

    Raises:
        HTTPException: If price not found.

    """
    result = await db.execute(select(Price).where(Price.id == price_id))
    db_price = result.scalar_one_or_none()
    if not db_price:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Price not found')

    await db.delete(db_price)
    await db.commit()
    return None


@router.post('/bulk', status_code=status.HTTP_201_CREATED)
async def bulk_create_prices(prices: list[PriceCreate], db: AsyncSession = Depends(get_db)):
    """Create multiple prices at once.

    Args:
        prices: List of prices to create.
        db: Database session.

    Returns:
        dict: Number of prices created.

    Raises:
        HTTPException: If unit trust not found.

    """
    unit_trust_ids = {p.unit_trust_id for p in prices}
    result = await db.execute(select(UnitTrust).where(UnitTrust.id.in_(unit_trust_ids)))
    existing_unit_trusts = {ut.id for ut in result.scalars().all()}

    for price in prices:
        if price.unit_trust_id not in existing_unit_trusts:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f'Unit trust {price.unit_trust_id} not found',
            )

    result = await db.execute(
        select(Price).where(
            Price.unit_trust_id.in_(unit_trust_ids),
            Price.date.in_([p.date for p in prices]),
        )
    )
    existing_dates = {(p.unit_trust_id, p.date) for p in result.scalars().all()}

    new_prices = []
    for price in prices:
        if (price.unit_trust_id, price.date) not in existing_dates:
            new_prices.append(Price(**price.model_dump()))

    db.add_all(new_prices)
    await db.commit()
    return {'created': len(new_prices)}


@router.post('/fetch/{unit_trust_id}', response_model=PriceFetchResult)
async def fetch_prices_for_unit_trust(
    unit_trust_id: int,
    start_date: date | None = Query(None, description='Start date (defaults to today)'),
    end_date: date | None = Query(None, description='End date (defaults to today)'),
    db: AsyncSession = Depends(get_db),
):
    """Fetch prices from provider and save to database.

    Args:
        unit_trust_id: ID of the unit trust to fetch prices for.
        start_date: Start of date range (defaults to today).
        end_date: End of date range (defaults to today).
        db: Database session.

    Returns:
        PriceFetchResult: Result of the fetch operation.

    Raises:
        HTTPException: If unit trust not found, no provider configured, or fetch fails.

    """
    # Get unit trust
    result = await db.execute(select(UnitTrust).where(UnitTrust.id == unit_trust_id))
    unit_trust = result.scalar_one_or_none()
    if not unit_trust:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Unit trust not found')

    # Check provider is configured
    if not unit_trust.provider:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'No provider configured for unit trust {unit_trust.symbol}. '
            f'Available providers: {", ".join(get_available_providers())}',
        )

    # Get provider
    provider = get_provider(unit_trust.provider)
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Unknown provider: {unit_trust.provider}. '
            f'Available providers: {", ".join(get_available_providers())}',
        )

    # Use provider_symbol if set, otherwise fall back to symbol
    lookup_symbol = unit_trust.provider_symbol or unit_trust.symbol

    # Fetch prices from provider
    try:
        fetched_prices = await provider.fetch_prices(lookup_symbol, start_date, end_date)
    except ProviderError as e:
        logger.error(f'Provider error for {unit_trust.symbol}: {e}')
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        ) from e

    # Get existing prices for the date range to avoid duplicates
    fetched_dates = [fp.date for fp in fetched_prices]
    result = await db.execute(
        select(Price).where(
            Price.unit_trust_id == unit_trust_id,
            Price.date.in_([datetime.combine(d, datetime.min.time()) for d in fetched_dates]),
        )
    )
    existing_dates = {p.date.date() for p in result.scalars().all()}

    # Save new prices (skip existing dates)
    new_prices = []
    for fp in fetched_prices:
        if fp.date not in existing_dates:
            price = Price(
                unit_trust_id=unit_trust_id,
                date=datetime.combine(fp.date, datetime.min.time()),
                price=fp.price,
            )
            new_prices.append(price)
            db.add(price)

    if new_prices:
        await db.commit()
        for price in new_prices:
            await db.refresh(price)

    return PriceFetchResult(
        unit_trust_id=unit_trust_id,
        symbol=unit_trust.symbol,
        provider=unit_trust.provider,
        prices_fetched=len(fetched_prices),
        prices_saved=len(new_prices),
        prices=[PriceResponse.model_validate(p) for p in new_prices],
    )


@router.post('/fetch', response_model=BulkPriceFetchResponse)
async def fetch_prices_bulk(
    unit_trust_ids: list[int] | None = Query(
        None, description='List of unit trust IDs (fetches all if not provided)'
    ),
    start_date: date | None = Query(None, description='Start date (defaults to today)'),
    end_date: date | None = Query(None, description='End date (defaults to today)'),
    db: AsyncSession = Depends(get_db),
):
    """Fetch prices for multiple unit trusts from their providers.

    Args:
        unit_trust_ids: Optional list of unit trust IDs. If not provided, fetches for all.
        start_date: Start of date range (defaults to today).
        end_date: End of date range (defaults to today).
        db: Database session.

    Returns:
        BulkPriceFetchResponse: Results and errors for each unit trust.

    """
    # Get unit trusts
    query = select(UnitTrust)
    if unit_trust_ids:
        query = query.where(UnitTrust.id.in_(unit_trust_ids))
    result = await db.execute(query)
    unit_trusts = result.scalars().all()

    results: list[PriceFetchResult] = []
    errors: list[PriceFetchError] = []

    for unit_trust in unit_trusts:
        # Check provider is configured
        if not unit_trust.provider:
            errors.append(
                PriceFetchError(
                    unit_trust_id=unit_trust.id,
                    symbol=unit_trust.symbol,
                    provider=None,
                    error='No provider configured',
                )
            )
            continue

        # Get provider
        provider = get_provider(unit_trust.provider)
        if not provider:
            errors.append(
                PriceFetchError(
                    unit_trust_id=unit_trust.id,
                    symbol=unit_trust.symbol,
                    provider=unit_trust.provider,
                    error=f'Unknown provider: {unit_trust.provider}',
                )
            )
            continue

        # Use provider_symbol if set, otherwise fall back to symbol
        lookup_symbol = unit_trust.provider_symbol or unit_trust.symbol

        # Fetch prices from provider
        try:
            fetched_prices = await provider.fetch_prices(lookup_symbol, start_date, end_date)
        except ProviderError as e:
            logger.error(f'Provider error for {unit_trust.symbol}: {e}')
            errors.append(
                PriceFetchError(
                    unit_trust_id=unit_trust.id,
                    symbol=unit_trust.symbol,
                    provider=unit_trust.provider,
                    error=str(e),
                )
            )
            continue

        # Get existing prices for the date range to avoid duplicates
        fetched_dates = [fp.date for fp in fetched_prices]
        result = await db.execute(
            select(Price).where(
                Price.unit_trust_id == unit_trust.id,
                Price.date.in_([datetime.combine(d, datetime.min.time()) for d in fetched_dates]),
            )
        )
        existing_dates = {p.date.date() for p in result.scalars().all()}

        # Save new prices (skip existing dates)
        new_prices = []
        for fp in fetched_prices:
            if fp.date not in existing_dates:
                price = Price(
                    unit_trust_id=unit_trust.id,
                    date=datetime.combine(fp.date, datetime.min.time()),
                    price=fp.price,
                )
                new_prices.append(price)
                db.add(price)

        if new_prices:
            await db.commit()
            for price in new_prices:
                await db.refresh(price)

        results.append(
            PriceFetchResult(
                unit_trust_id=unit_trust.id,
                symbol=unit_trust.symbol,
                provider=unit_trust.provider,
                prices_fetched=len(fetched_prices),
                prices_saved=len(new_prices),
                prices=[PriceResponse.model_validate(p) for p in new_prices],
            )
        )

    return BulkPriceFetchResponse(
        total_requested=len(unit_trusts),
        successful=len(results),
        failed=len(errors),
        results=results,
        errors=errors,
    )
