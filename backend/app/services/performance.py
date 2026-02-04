"""Performance calculation service."""

from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.price import Price
from app.models.transaction import Transaction
from app.schemas import PerformanceMetrics, PortfolioHistory, PortfolioPerformance, PortfolioSummary


class PerformanceService:
    """Service for calculating portfolio performance metrics."""

    @staticmethod
    async def get_portfolio_summary(db: AsyncSession) -> PortfolioSummary:
        """Calculate portfolio summary.

        Args:
            db: Database session.

        Returns:
            PortfolioSummary: Portfolio summary with invested amount,
                current value, and ROI.

        """
        # Calculate total invested (only buy transactions)
        buy_result = await db.execute(
            select(
                func.sum(Transaction.units * Transaction.price_per_unit).label('total_invested'),
            ).where(Transaction.transaction_type == 'buy')
        )
        buy_row = buy_result.first()
        total_invested = float(buy_row[0]) if buy_row and buy_row[0] else 0.0

        # Calculate net units per fund (buy - sell) and holding count
        # Use CASE to add units for buy, subtract for sell
        net_units_expr = func.sum(
            case(
                (Transaction.transaction_type == 'buy', Transaction.units),
                (Transaction.transaction_type == 'sell', -Transaction.units),
                else_=0,
            )
        )

        holdings_result = await db.execute(
            select(
                Transaction.unit_trust_id,
                net_units_expr.label('net_units'),
            ).group_by(Transaction.unit_trust_id)
        )
        holdings = holdings_result.all()

        # Filter to only positive holdings for counting
        positive_holdings = [(uid, units) for uid, units in holdings if units and units > 0]
        holding_count = len(positive_holdings)
        total_units = sum(units for _, units in positive_holdings)

        # Calculate current value based on net units and latest prices
        current_value = 0.0
        for unit_trust_id, net_units in holdings:
            if net_units and net_units > 0:
                latest_price_result = await db.execute(
                    select(Price.price)
                    .where(Price.unit_trust_id == unit_trust_id)
                    .order_by(Price.date.desc())
                    .limit(1)
                )
                latest_price = latest_price_result.scalar_one_or_none()
                if latest_price:
                    current_value += net_units * latest_price

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
    async def get_portfolio_history(db: AsyncSession, days: int = 365) -> list[PortfolioHistory]:
        """Get portfolio value history as a true equity curve.

        This method computes the portfolio value at each point in time based on
        the holdings that existed at that time (not current holdings applied
        retroactively). When a buy occurs, the portfolio value increases from
        that date forward. When a sell occurs, the value decreases.

        Missing prices are handled via forward-fill: if a price doesn't exist
        for a specific date, the last known price is used.

        Args:
            db: Database session.
            days: Number of days to look back.

        Returns:
            List of portfolio values by date, reflecting true historical holdings.

        """
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)

        # Fetch all transactions (we need the full history to compute holdings at each point)
        txn_query = select(
            Transaction.unit_trust_id,
            Transaction.transaction_type,
            Transaction.units,
            Transaction.transaction_date,
        ).order_by(Transaction.transaction_date)
        txn_result = await db.execute(txn_query)
        transactions = txn_result.all()

        if not transactions:
            return []

        # Build a DataFrame of transactions with signed units
        txn_records = []
        for t in transactions:
            signed_units = t.units if t.transaction_type == 'buy' else -t.units
            txn_records.append(
                {
                    'unit_trust_id': t.unit_trust_id,
                    'date': t.transaction_date.date()
                    if hasattr(t.transaction_date, 'date')
                    else t.transaction_date,
                    'units_change': signed_units,
                }
            )
        txn_df = pd.DataFrame(txn_records)

        # Aggregate transactions by date and fund (multiple transactions same day)
        txn_df = txn_df.groupby(['date', 'unit_trust_id'])['units_change'].sum().reset_index()

        # Pivot to get units change per fund per date
        txn_pivot = txn_df.pivot(index='date', columns='unit_trust_id', values='units_change')
        txn_pivot = txn_pivot.fillna(0)

        # Cumulative sum to get holdings at each date
        holdings_over_time = txn_pivot.cumsum()

        # Fetch all prices (including before start_date for forward-fill)
        # We need prices from the earliest transaction date
        earliest_txn_date = min(t.transaction_date for t in transactions)
        price_query = (
            select(Price.unit_trust_id, Price.date, Price.price)
            .where(Price.date >= earliest_txn_date)
            .order_by(Price.date)
        )
        price_result = await db.execute(price_query)
        prices = price_result.all()

        if not prices:
            return []

        prices_df = pd.DataFrame(
            [
                {
                    'unit_trust_id': p.unit_trust_id,
                    'date': p.date.date() if hasattr(p.date, 'date') else p.date,
                    'price': p.price,
                }
                for p in prices
            ]
        )

        # Pivot prices: rows=dates, columns=unit_trust_id
        prices_pivot = prices_df.pivot(index='date', columns='unit_trust_id', values='price')

        # Create a complete date range from start of history to end
        all_dates = pd.date_range(
            start=min(holdings_over_time.index.min(), prices_pivot.index.min()),
            end=max(holdings_over_time.index.max(), prices_pivot.index.max(), end_date.date()),
            freq='D',
        ).date

        # Reindex both DataFrames to the complete date range
        holdings_over_time = holdings_over_time.reindex(all_dates).ffill().fillna(0)
        prices_pivot = prices_pivot.reindex(all_dates).ffill()

        # Ensure columns match (only funds that appear in both)
        common_funds = holdings_over_time.columns.intersection(prices_pivot.columns)
        holdings_over_time = holdings_over_time[common_funds]
        prices_pivot = prices_pivot[common_funds]

        # Calculate portfolio value: holdings * prices, summed across funds
        # Only count positive holdings (can't have negative shares)
        positive_holdings = holdings_over_time.clip(lower=0)
        portfolio_values = (positive_holdings * prices_pivot).fillna(0).sum(axis=1)

        # Filter to the requested date range
        start_date_date = start_date.date() if hasattr(start_date, 'date') else start_date
        portfolio_values = portfolio_values[portfolio_values.index >= start_date_date]

        from app.schemas import PortfolioHistory

        return [
            PortfolioHistory(
                date=datetime.combine(date, datetime.min.time(), tzinfo=timezone.utc),
                value=float(value),
            )
            for date, value in portfolio_values.items()
        ]

    @staticmethod
    def calculate_metrics(
        history: list[PortfolioHistory], risk_free_rate: float = 0.02
    ) -> PerformanceMetrics:
        """Calculate performance metrics from history.

        Args:
            history: List of portfolio history data.
            risk_free_rate: Risk-free rate for Sharpe ratio.

        Returns:
            PerformanceMetrics: Calculated performance metrics.

        """
        if len(history) < 2:
            return PerformanceMetrics(
                daily_return=0.0,
                volatility=0.0,
                annualized_return=0.0,
                max_drawdown=0.0,
                sharpe_ratio=None,
            )

        df = pd.DataFrame([{'date': h.date, 'value': h.value} for h in history])
        df = df.sort_values('date')

        # Filter to only days with positive value (before any holdings, there's no
        # meaningful return to calculate). This avoids infinite returns from 0→positive.
        df_positive = df[df['value'] > 0].copy()

        if len(df_positive) < 2:
            return PerformanceMetrics(
                daily_return=0.0,
                volatility=0.0,
                annualized_return=0.0,
                max_drawdown=0.0,
                sharpe_ratio=None,
            )

        df_positive['daily_return'] = df_positive['value'].pct_change()

        # Replace any remaining inf/-inf values with NaN (edge case protection)
        df_positive['daily_return'] = df_positive['daily_return'].replace([np.inf, -np.inf], np.nan)

        is_all_na = bool(df_positive['daily_return'].isna().all())
        daily_return = float(df_positive['daily_return'].mean()) if not is_all_na else 0.0
        volatility = (
            float(df_positive['daily_return'].std()) * np.sqrt(252) if not is_all_na else 0.0
        )

        total_return = (
            (df_positive['value'].iloc[-1] / df_positive['value'].iloc[0]) - 1
            if df_positive['value'].iloc[0] > 0
            else 0.0
        )
        days_held = (df_positive['date'].iloc[-1] - df_positive['date'].iloc[0]).days
        annualized_return = (1 + total_return) ** (365 / days_held) - 1 if days_held > 0 else 0.0

        rolling_max = df_positive['value'].expanding().max()
        drawdown = (df_positive['value'] - rolling_max) / rolling_max
        max_drawdown = float(drawdown.min())

        sharpe_ratio = (
            ((daily_return * 252 - risk_free_rate) / volatility) if volatility > 0 else None
        )

        return PerformanceMetrics(
            daily_return=daily_return,
            volatility=volatility,
            annualized_return=annualized_return,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
        )

    @staticmethod
    async def get_portfolio_performance(db: AsyncSession, days: int = 365) -> PortfolioPerformance:
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

        return PortfolioPerformance(summary=summary, metrics=metrics, history=history)
