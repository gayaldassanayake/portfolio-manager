"""Transaction management API endpoints."""

from datetime import datetime
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.price import Price
from app.models.transaction import Transaction
from app.models.unit_trust import UnitTrust
from app.schemas import (
    TransactionCreate,
    TransactionResponse,
    TransactionUpdate,
    TransactionWithUnitTrust,
)

router = APIRouter(prefix='/api/v1/transactions', tags=['Transactions'])


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session.

    Yields:
        AsyncSession: Database session.

    """
    async for session in get_db():
        yield session


@router.post('', response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(transaction: TransactionCreate, db: AsyncSession = Depends(get_db)):
    """Create a new transaction.

    Args:
        transaction: Transaction data to create.
        db: Database session.

    Returns:
        TransactionResponse: Created transaction.

    Raises:
        HTTPException: If unit trust not found or price not available.

    """
    result = await db.execute(select(UnitTrust).where(UnitTrust.id == transaction.unit_trust_id))
    unit_trust = result.scalar_one_or_none()
    if not unit_trust:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Unit trust not found')

    result = await db.execute(
        select(Price).where(
            Price.unit_trust_id == transaction.unit_trust_id,
            Price.date == transaction.transaction_date,
        )
    )
    price = result.scalar_one_or_none()
    if not price:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Price not available for the transaction date',
        )

    db_transaction = Transaction(
        unit_trust_id=transaction.unit_trust_id,
        units=transaction.units,
        price_per_unit=price.price,
        transaction_date=transaction.transaction_date,
    )
    db.add(db_transaction)
    await db.commit()
    await db.refresh(db_transaction)
    return db_transaction


@router.get('', response_model=list[TransactionWithUnitTrust])
async def list_transactions(
    unit_trust_id: int | None = Query(None),
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """List transactions with optional filters.

    Args:
        unit_trust_id: Filter by unit trust ID.
        start_date: Filter by start date.
        end_date: Filter by end date.
        db: Database session.

    Returns:
        List of transactions with unit trust details.

    """
    query = select(Transaction).options(selectinload(Transaction.unit_trust))
    if unit_trust_id:
        query = query.where(Transaction.unit_trust_id == unit_trust_id)
    if start_date:
        query = query.where(Transaction.transaction_date >= start_date)
    if end_date:
        query = query.where(Transaction.transaction_date <= end_date)
    query = query.order_by(Transaction.transaction_date.desc())

    result = await db.execute(query)
    transactions = result.scalars().all()
    return [
        TransactionWithUnitTrust(
            id=t.id,
            unit_trust_id=t.unit_trust_id,
            units=t.units,
            price_per_unit=t.price_per_unit,
            transaction_date=t.transaction_date,
            created_at=t.created_at,
            unit_trust_name=t.unit_trust.name,
            unit_trust_symbol=t.unit_trust.symbol,
        )
        for t in transactions
    ]


@router.get('/{transaction_id}', response_model=TransactionWithUnitTrust)
async def get_transaction(transaction_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific transaction by ID.

    Args:
        transaction_id: Transaction ID.
        db: Database session.

    Returns:
        TransactionWithUnitTrust: Transaction data with unit trust details.

    Raises:
        HTTPException: If transaction not found.

    """
    result = await db.execute(
        select(Transaction)
        .options(selectinload(Transaction.unit_trust))
        .where(Transaction.id == transaction_id)
    )
    transaction = result.scalar_one_or_none()
    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Transaction not found')

    return TransactionWithUnitTrust(
        id=transaction.id,
        unit_trust_id=transaction.unit_trust_id,
        units=transaction.units,
        price_per_unit=transaction.price_per_unit,
        transaction_date=transaction.transaction_date,
        created_at=transaction.created_at,
        unit_trust_name=transaction.unit_trust.name,
        unit_trust_symbol=transaction.unit_trust.symbol,
    )


@router.put('/{transaction_id}', response_model=TransactionResponse)
async def update_transaction(
    transaction_id: int,
    transaction: TransactionUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a transaction.

    Args:
        transaction_id: Transaction ID.
        transaction: Updated transaction data.
        db: Database session.

    Returns:
        TransactionResponse: Updated transaction.

    Raises:
        HTTPException: If transaction not found.

    """
    result = await db.execute(select(Transaction).where(Transaction.id == transaction_id))
    db_transaction = result.scalar_one_or_none()
    if not db_transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Transaction not found')

    update_data = transaction.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_transaction, field, value)

    await db.commit()
    await db.refresh(db_transaction)
    return db_transaction


@router.delete('/{transaction_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(transaction_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a transaction.

    Args:
        transaction_id: Transaction ID.
        db: Database session.

    Raises:
        HTTPException: If transaction not found.

    """
    result = await db.execute(select(Transaction).where(Transaction.id == transaction_id))
    db_transaction = result.scalar_one_or_none()
    if not db_transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Transaction not found')

    await db.delete(db_transaction)
    await db.commit()
    return None
