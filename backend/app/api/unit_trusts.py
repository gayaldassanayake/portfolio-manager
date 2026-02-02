"""Unit trust management API endpoints."""

from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.price import Price
from app.models.transaction import Transaction
from app.models.unit_trust import UnitTrust
from app.schemas import (
    UnitTrustCreate,
    UnitTrustResponse,
    UnitTrustUpdate,
    UnitTrustWithStats,
)

router = APIRouter(prefix='/api/v1/unit-trusts', tags=['Unit Trusts'])


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session.

    Yields:
        AsyncSession: Database session.

    """
    async for session in get_db():
        yield session


@router.post('', response_model=UnitTrustResponse, status_code=status.HTTP_201_CREATED)
async def create_unit_trust(unit_trust: UnitTrustCreate, db: AsyncSession = Depends(get_db)):
    """Create a new unit trust.

    Args:
        unit_trust: Unit trust data to create.
        db: Database session.

    Returns:
        UnitTrustResponse: Created unit trust.

    Raises:
        HTTPException: If symbol already exists.

    """
    result = await db.execute(select(UnitTrust).where(UnitTrust.symbol == unit_trust.symbol))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Unit trust with this symbol already exists',
        )

    db_unit_trust = UnitTrust(**unit_trust.model_dump())
    db.add(db_unit_trust)
    await db.commit()
    await db.refresh(db_unit_trust)
    return db_unit_trust


@router.get('', response_model=list[UnitTrustResponse])
async def list_unit_trusts(db: AsyncSession = Depends(get_db)):
    """List all unit trusts.

    Args:
        db: Database session.

    Returns:
        List of unit trusts.

    """
    result = await db.execute(select(UnitTrust))
    unit_trusts = result.scalars().all()
    return unit_trusts


@router.get('/{unit_trust_id}', response_model=UnitTrustResponse)
async def get_unit_trust(unit_trust_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific unit trust by ID.

    Args:
        unit_trust_id: Unit trust ID.
        db: Database session.

    Returns:
        UnitTrustResponse: Unit trust data.

    Raises:
        HTTPException: If unit trust not found.

    """
    result = await db.execute(select(UnitTrust).where(UnitTrust.id == unit_trust_id))
    unit_trust = result.scalar_one_or_none()
    if not unit_trust:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Unit trust not found')
    return unit_trust


@router.put('/{unit_trust_id}', response_model=UnitTrustResponse)
async def update_unit_trust(
    unit_trust_id: int, unit_trust: UnitTrustUpdate, db: AsyncSession = Depends(get_db)
):
    """Update a unit trust.

    Args:
        unit_trust_id: Unit trust ID.
        unit_trust: Updated unit trust data.
        db: Database session.

    Returns:
        UnitTrustResponse: Updated unit trust.

    Raises:
        HTTPException: If unit trust not found.

    """
    result = await db.execute(select(UnitTrust).where(UnitTrust.id == unit_trust_id))
    db_unit_trust = result.scalar_one_or_none()
    if not db_unit_trust:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Unit trust not found')

    update_data = unit_trust.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_unit_trust, field, value)

    await db.commit()
    await db.refresh(db_unit_trust)
    return db_unit_trust


@router.delete('/{unit_trust_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_unit_trust(unit_trust_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a unit trust.

    Args:
        unit_trust_id: Unit trust ID.
        db: Database session.

    Raises:
        HTTPException: If unit trust not found.

    """
    result = await db.execute(select(UnitTrust).where(UnitTrust.id == unit_trust_id))
    db_unit_trust = result.scalar_one_or_none()
    if not db_unit_trust:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Unit trust not found')

    await db.delete(db_unit_trust)
    await db.commit()
    return None


@router.get('/{unit_trust_id}/with-stats', response_model=UnitTrustWithStats)
async def get_unit_trust_with_stats(unit_trust_id: int, db: AsyncSession = Depends(get_db)):
    """Get a unit trust with statistics.

    Args:
        unit_trust_id: Unit trust ID.
        db: Database session.

    Returns:
        UnitTrustWithStats: Unit trust data with statistics.

    Raises:
        HTTPException: If unit trust not found.

    """
    result = await db.execute(select(UnitTrust).where(UnitTrust.id == unit_trust_id))
    unit_trust = result.scalar_one_or_none()
    if not unit_trust:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Unit trust not found')

    # Calculate net units (buy - sell)
    net_units_expr = func.sum(
        case(
            (Transaction.transaction_type == 'buy', Transaction.units),
            (Transaction.transaction_type == 'sell', -Transaction.units),
            else_=0,
        )
    )
    total_units_result = await db.execute(
        select(net_units_expr).where(Transaction.unit_trust_id == unit_trust_id)
    )
    total_units = total_units_result.scalar() or 0.0

    # Calculate average purchase price (only from buy transactions)
    avg_price_result = await db.execute(
        select(func.avg(Transaction.price_per_unit)).where(
            Transaction.unit_trust_id == unit_trust_id,
            Transaction.transaction_type == 'buy',
        )
    )
    avg_price = avg_price_result.scalar() or 0.0

    latest_price_result = await db.execute(
        select(Price.price)
        .where(Price.unit_trust_id == unit_trust_id)
        .order_by(Price.date.desc())
        .limit(1)
    )
    latest_price = latest_price_result.scalar_one_or_none()

    return UnitTrustWithStats(
        id=unit_trust.id,
        name=unit_trust.name,
        symbol=unit_trust.symbol,
        description=unit_trust.description,
        created_at=unit_trust.created_at,
        total_units=total_units,
        avg_purchase_price=avg_price,
        latest_price=latest_price,
    )
