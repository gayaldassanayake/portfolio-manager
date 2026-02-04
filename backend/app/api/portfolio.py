"""Portfolio API endpoints."""

from datetime import date
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.transaction import Transaction
from app.schemas import (
    PerformanceMetrics,
    PortfolioHistory,
    PortfolioPerformance,
    PortfolioSummary,
)
from app.services.performance import PerformanceService

router = APIRouter(prefix='/api/v1/portfolio', tags=['Portfolio'])


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session.

    Yields:
        AsyncSession: Database session.

    """
    async for session in get_db():
        yield session


@router.get('/summary', response_model=PortfolioSummary)
async def get_portfolio_summary(db: AsyncSession = Depends(get_db)):
    """Get portfolio summary.

    Args:
        db: Database session.

    Returns:
        PortfolioSummary: Portfolio summary data.

    """
    return await PerformanceService.get_portfolio_summary(db)


@router.get('/performance', response_model=PortfolioPerformance)
async def get_portfolio_performance(
    days: int = Query(365, ge=1, le=3650), db: AsyncSession = Depends(get_db)
):
    """Get portfolio performance.

    Args:
        days: Number of days to look back.
        db: Database session.

    Returns:
        PortfolioPerformance: Complete performance data.

    """
    return await PerformanceService.get_portfolio_performance(db, days)


@router.get('/history', response_model=list[PortfolioHistory])
async def get_portfolio_history(
    days: int = Query(365, ge=1, le=3650), db: AsyncSession = Depends(get_db)
):
    """Get portfolio value history.

    Args:
        days: Number of days to look back.
        db: Database session.

    Returns:
        List of portfolio values by date.

    """
    return await PerformanceService.get_portfolio_history(db, days)


@router.get('/metrics', response_model=PerformanceMetrics)
async def get_portfolio_metrics(
    days: int = Query(365, ge=1, le=3650), db: AsyncSession = Depends(get_db)
):
    """Get portfolio performance metrics.

    Args:
        days: Number of days to look back.
        db: Database session.

    Returns:
        PerformanceMetrics: Calculated metrics.

    """
    summary = await PerformanceService.get_portfolio_summary(db)
    history = await PerformanceService.get_portfolio_history(db, days)

    # Fetch transaction data for metrics calculation (including unit_trust_id for FIFO)
    txn_query = select(
        Transaction.unit_trust_id,
        Transaction.transaction_type,
        Transaction.units,
        Transaction.price_per_unit,
        Transaction.transaction_date,
    ).order_by(Transaction.transaction_date)
    txn_result = await db.execute(txn_query)
    transactions = txn_result.all()

    # Extract transaction dates
    transaction_dates: list[date] = []
    for t in transactions:
        txn_date = (
            t.transaction_date.date() if hasattr(t.transaction_date, 'date') else t.transaction_date
        )
        transaction_dates.append(txn_date)

    # Build cash flows for IRR calculation
    cash_flows: list[tuple[date, float]] = []
    for t in transactions:
        txn_date = (
            t.transaction_date.date() if hasattr(t.transaction_date, 'date') else t.transaction_date
        )
        amount = t.units * t.price_per_unit
        if t.transaction_type == 'buy':
            cash_flows.append((txn_date, -amount))
        else:
            cash_flows.append((txn_date, amount))

    # Prepare transaction data for FIFO cost basis calculation
    fifo_transactions: list[tuple[int, str, float, float, date]] = []
    for t in transactions:
        txn_date = (
            t.transaction_date.date() if hasattr(t.transaction_date, 'date') else t.transaction_date
        )
        fifo_transactions.append(
            (t.unit_trust_id, t.transaction_type, t.units, t.price_per_unit, txn_date)
        )

    # Calculate FIFO cost basis
    cost_basis, _ = PerformanceService._calculate_fifo_cost_basis(fifo_transactions)

    return PerformanceService.calculate_metrics(
        history=history,
        transaction_dates=transaction_dates,
        cash_flows=cash_flows,
        total_invested=summary.total_invested,
        total_withdrawn=summary.total_withdrawn,
        current_value=summary.current_value,
        cost_basis=cost_basis,
    )
