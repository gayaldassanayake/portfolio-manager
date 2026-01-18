"""Portfolio API endpoints."""

from typing import AsyncGenerator

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
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
    history = await PerformanceService.get_portfolio_history(db, days)
    return PerformanceService.calculate_metrics(history)
