"""Price management API endpoints."""

from datetime import datetime
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.price import Price
from app.models.unit_trust import UnitTrust
from app.schemas import PriceCreate, PriceResponse, PriceUpdate

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
