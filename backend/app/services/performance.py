"""Performance calculation service."""

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.price import Price
from app.models.transaction import Transaction

if TYPE_CHECKING:
    from app.schemas import (
        PerformanceMetrics,
        PortfolioHistory,
        PortfolioPerformance,
        PortfolioSummary,
    )


class PerformanceService:
    """Service for calculating portfolio performance metrics."""

    @staticmethod
    async def get_portfolio_summary(db: AsyncSession) -> 'PortfolioSummary':
        """Calculate portfolio summary.

        Args:
            db: Database session.

        Returns:
            PortfolioSummary: Portfolio summary with invested amount,
                current value, and ROI.

        """
        result = await db.execute(
            select(
                func.sum(Transaction.units * Transaction.price_per_unit).label('total_invested'),
                func.sum(Transaction.units).label('total_units'),
                func.count(func.distinct(Transaction.unit_trust_id)).label('holding_count'),
            )
        )
        summary_row = result.first()
        if not summary_row:
            from app.schemas import PortfolioSummary

            return PortfolioSummary(
                total_invested=0.0,
                current_value=0.0,
                total_gain_loss=0.0,
                roi_percentage=0.0,
                total_units=0,
                holding_count=0,
            )

        total_invested = float(summary_row[0]) if summary_row[0] else 0.0
        total_units = float(summary_row[1]) if summary_row[1] else 0.0
        holding_count = int(summary_row[2]) if summary_row[2] else 0

        current_value = 0.0
        if total_units > 0:
            holdings_result = await db.execute(
                select(
                    Transaction.unit_trust_id,
                    func.sum(Transaction.units).label('units'),
                ).group_by(Transaction.unit_trust_id)
            )
            holdings = holdings_result.all()
            for unit_trust_id, units in holdings:
                latest_price_result = await db.execute(
                    select(Price.price)
                    .where(Price.unit_trust_id == unit_trust_id)
                    .order_by(Price.date.desc())
                    .limit(1)
                )
                latest_price = latest_price_result.scalar_one_or_none()
                if latest_price:
                    current_value += units * latest_price

        total_gain_loss = current_value - total_invested
        roi_percentage = (total_gain_loss / total_invested * 100) if total_invested > 0 else 0.0

        from app.schemas import PortfolioSummary

        return PortfolioSummary(
            total_invested=total_invested,
            current_value=current_value,
            total_gain_loss=total_gain_loss,
            roi_percentage=roi_percentage,
            total_units=int(total_units),
            holding_count=holding_count,
        )

    @staticmethod
    async def get_portfolio_history(db: AsyncSession, days: int = 365) -> list['PortfolioHistory']:
        """Get portfolio value history.

        Args:
            db: Database session.
            days: Number of days to look back.

        Returns:
            List of portfolio values by date.

        """
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)

        price_query = (
            select(Price.unit_trust_id, Price.date, Price.price)
            .where(Price.date >= start_date)
            .order_by(Price.date)
        )
        price_result = await db.execute(price_query)
        prices_df = pd.DataFrame(
            [{'unit_trust_id': p[0], 'date': p[1], 'price': p[2]} for p in price_result.all()]
        )

        if prices_df.empty:
            return []

        holdings_result = await db.execute(
            select(Transaction.unit_trust_id, func.sum(Transaction.units).label('units')).group_by(
                Transaction.unit_trust_id
            )
        )
        holdings = {row.unit_trust_id: row.units for row in holdings_result}

        prices_pivot = prices_df.pivot(index='date', columns='unit_trust_id', values='price')
        portfolio_values = (prices_pivot * pd.Series(holdings)).fillna(0).sum(axis=1)

        from app.schemas import PortfolioHistory

        return [
            PortfolioHistory(date=date, value=value) for date, value in portfolio_values.items()
        ]

    @staticmethod
    def calculate_metrics(
        history: list['PortfolioHistory'], risk_free_rate: float = 0.02
    ) -> 'PerformanceMetrics':
        """Calculate performance metrics from history.

        Args:
            history: List of portfolio history data.
            risk_free_rate: Risk-free rate for Sharpe ratio.

        Returns:
            PerformanceMetrics: Calculated performance metrics.

        """
        if len(history) < 2:
            from app.schemas import PerformanceMetrics

            return PerformanceMetrics(
                daily_return=0.0,
                volatility=0.0,
                annualized_return=0.0,
                max_drawdown=0.0,
                sharpe_ratio=None,
            )

        df = pd.DataFrame([{'date': h.date, 'value': h.value} for h in history])
        df = df.sort_values('date')
        df['daily_return'] = df['value'].pct_change()

        is_all_na = bool(df['daily_return'].isna().all())
        daily_return = float(df['daily_return'].mean()) if not is_all_na else 0.0
        volatility = float(df['daily_return'].std()) * np.sqrt(252) if not is_all_na else 0.0

        total_return = (
            (df['value'].iloc[-1] / df['value'].iloc[0]) - 1 if df['value'].iloc[0] > 0 else 0.0
        )
        days_held = (df['date'].iloc[-1] - df['date'].iloc[0]).days
        annualized_return = (1 + total_return) ** (365 / days_held) - 1 if days_held > 0 else 0.0

        rolling_max = df['value'].expanding().max()
        drawdown = (df['value'] - rolling_max) / rolling_max
        max_drawdown = drawdown.min()

        sharpe_ratio = (
            ((daily_return * 252 - risk_free_rate) / volatility) if volatility > 0 else None
        )

        from app.schemas import PerformanceMetrics

        return PerformanceMetrics(
            daily_return=daily_return,
            volatility=volatility,
            annualized_return=annualized_return,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
        )

    @staticmethod
    async def get_portfolio_performance(
        db: AsyncSession, days: int = 365
    ) -> 'PortfolioPerformance':
        """Get complete portfolio performance data.

        Args:
            db: Database session.
            days: Number of days to look back.

        Returns:
            PortfolioPerformance: Summary, metrics, and history.

        """
        summary = await PerformanceService.get_portfolio_summary(db)
        history = await PerformanceService.get_portfolio_history(db, days)
        metrics = PerformanceService.calculate_metrics(history)

        from app.schemas import PortfolioPerformance

        return PortfolioPerformance(summary=summary, metrics=metrics, history=history)
