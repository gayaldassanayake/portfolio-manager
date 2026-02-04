"""Performance calculation service."""

from datetime import date, datetime, timedelta, timezone

import numpy as np
import pandas as pd
import pyxirr
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.price import Price
from app.models.transaction import Transaction
from app.schemas import PerformanceMetrics, PortfolioHistory, PortfolioPerformance, PortfolioSummary


class PerformanceService:
    """Service for calculating portfolio performance metrics."""

    @staticmethod
    def _calculate_fifo_cost_basis(
        transactions: list[tuple[int, str, float, float, date]],
    ) -> tuple[float, dict[int, float]]:
        """Calculate cost basis of remaining holdings using FIFO accounting.

        For each fund, maintains a queue of buy lots. When sells occur, units
        are removed from the oldest lots first (First In, First Out).

        Args:
            transactions: List of (unit_trust_id, transaction_type, units, price_per_unit, date)
                tuples, sorted by date.

        Returns:
            Tuple of (total_cost_basis, per_fund_cost_basis_dict).

        """
        from collections import defaultdict, deque

        # buy_lots[fund_id] = deque of (units_remaining, price_per_unit)
        buy_lots: dict[int, deque[list[float]]] = defaultdict(deque)

        for unit_trust_id, txn_type, units, price_per_unit, _txn_date in transactions:
            if txn_type == 'buy':
                # Add a new lot
                buy_lots[unit_trust_id].append([units, price_per_unit])
            else:  # sell
                # Remove units from oldest lots first (FIFO)
                remaining_to_sell = units
                while remaining_to_sell > 0 and buy_lots[unit_trust_id]:
                    oldest_lot = buy_lots[unit_trust_id][0]
                    lot_units = oldest_lot[0]

                    if lot_units <= remaining_to_sell:
                        # Consume entire lot
                        remaining_to_sell -= lot_units
                        buy_lots[unit_trust_id].popleft()
                    else:
                        # Partial consumption
                        oldest_lot[0] -= remaining_to_sell
                        remaining_to_sell = 0

        # Calculate total cost basis from remaining lots
        total_cost_basis = 0.0
        per_fund_cost_basis: dict[int, float] = {}

        for fund_id, lots in buy_lots.items():
            fund_cost = sum(lot_units * lot_price for lot_units, lot_price in lots)
            per_fund_cost_basis[fund_id] = fund_cost
            total_cost_basis += fund_cost

        return total_cost_basis, per_fund_cost_basis

    @staticmethod
    async def get_portfolio_summary(db: AsyncSession) -> PortfolioSummary:
        """Calculate portfolio summary.

        Args:
            db: Database session.

        Returns:
            PortfolioSummary: Portfolio summary with invested amount,
                withdrawn amount, current value, and net ROI.

        """
        # Calculate total invested (only buy transactions)
        buy_result = await db.execute(
            select(
                func.sum(Transaction.units * Transaction.price_per_unit).label('total_invested'),
            ).where(Transaction.transaction_type == 'buy')
        )
        buy_row = buy_result.first()
        total_invested = float(buy_row[0]) if buy_row and buy_row[0] else 0.0

        # Calculate total withdrawn (sell proceeds)
        sell_result = await db.execute(
            select(
                func.sum(Transaction.units * Transaction.price_per_unit).label('total_withdrawn'),
            ).where(Transaction.transaction_type == 'sell')
        )
        sell_row = sell_result.first()
        total_withdrawn = float(sell_row[0]) if sell_row and sell_row[0] else 0.0

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

        # Net return: (current_value + total_withdrawn - total_invested) / total_invested
        # This accounts for money already taken out
        total_gain_loss = current_value + total_withdrawn - total_invested
        roi_percentage = (total_gain_loss / total_invested * 100) if total_invested > 0 else 0.0

        from app.schemas import PortfolioSummary

        return PortfolioSummary(
            total_invested=total_invested,
            total_withdrawn=total_withdrawn,
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
        history: list[PortfolioHistory],
        transaction_dates: list[date],
        cash_flows: list[tuple[date, float]],
        total_invested: float,
        total_withdrawn: float,
        current_value: float,
        cost_basis: float,
        risk_free_rate: float = 0.02,
    ) -> PerformanceMetrics:
        """Calculate comprehensive performance metrics.

        This method calculates multiple return metrics:
        - Net Return: (current_value + total_withdrawn - total_invested) / total_invested
        - Unrealized ROI: (current_value - cost_basis) / cost_basis (FIFO)
        - Time-Weighted Return (TWR): Measures investment selection performance
        - Money-Weighted Return (MWR/IRR): Measures actual investor experience

        Volatility and daily returns exclude transaction days to avoid
        deposit/withdrawal-driven jumps affecting the calculation.

        Args:
            history: List of portfolio history data.
            transaction_dates: List of dates when transactions occurred.
            cash_flows: List of (date, amount) tuples. Negative = outflow (buy),
                positive = inflow (sell proceeds or final value).
            total_invested: Total amount invested (sum of buy transactions).
            total_withdrawn: Total amount withdrawn (sum of sell proceeds).
            current_value: Current portfolio value.
            cost_basis: FIFO cost basis of remaining holdings.
            risk_free_rate: Risk-free rate for Sharpe ratio calculation.

        Returns:
            PerformanceMetrics: Comprehensive performance metrics.

        """
        # Calculate Net Return (accounts for realized gains from sells)
        net_return = (
            (current_value + total_withdrawn - total_invested) / total_invested
            if total_invested > 0
            else 0.0
        )

        # Calculate Unrealized ROI (current holdings vs their FIFO cost basis)
        unrealized_roi = (current_value - cost_basis) / cost_basis if cost_basis > 0 else 0.0

        # Default empty metrics
        empty_metrics = PerformanceMetrics(
            daily_return=0.0,
            volatility=0.0,
            max_drawdown=0.0,
            sharpe_ratio=None,
            net_return=net_return,
            unrealized_roi=unrealized_roi,
            twr_annualized=None,
            mwr_annualized=None,
            best_day=None,
            worst_day=None,
        )

        if len(history) < 2:
            return empty_metrics

        df = pd.DataFrame([{'date': h.date.date(), 'value': h.value} for h in history])
        df = df.sort_values('date').reset_index(drop=True)

        # Filter to only days with positive value
        df_positive = df[df['value'] > 0].copy()

        if len(df_positive) < 2:
            return PerformanceMetrics(
                daily_return=0.0,
                volatility=0.0,
                max_drawdown=0.0,
                sharpe_ratio=None,
                net_return=net_return,
                unrealized_roi=unrealized_roi,
                twr_annualized=None,
                mwr_annualized=None,
                best_day=None,
                worst_day=None,
            )

        # Convert transaction_dates to a set for O(1) lookup
        txn_date_set = set(transaction_dates)

        # Calculate daily returns
        df_positive['daily_return'] = df_positive['value'].pct_change()
        df_positive['daily_return'] = df_positive['daily_return'].replace([np.inf, -np.inf], np.nan)

        # Mark transaction days
        df_positive['is_txn_day'] = df_positive['date'].isin(txn_date_set)

        # For volatility and daily return stats, exclude transaction days
        df_no_txn = df_positive[~df_positive['is_txn_day']].copy()

        is_all_na = bool(df_no_txn['daily_return'].isna().all()) if len(df_no_txn) > 0 else True
        daily_return = float(df_no_txn['daily_return'].mean()) if not is_all_na else 0.0
        volatility = float(df_no_txn['daily_return'].std()) * np.sqrt(252) if not is_all_na else 0.0

        # Best and worst day (excluding transaction days and NaN)
        valid_returns = df_no_txn['daily_return'].dropna()
        best_day = float(valid_returns.max()) if len(valid_returns) > 0 else None
        worst_day = float(valid_returns.min()) if len(valid_returns) > 0 else None

        # Max drawdown (use all positive-value days, drawdown is about portfolio value)
        rolling_max = df_positive['value'].expanding().max()
        drawdown = (df_positive['value'] - rolling_max) / rolling_max
        max_drawdown = float(drawdown.min())

        # Time-Weighted Return (TWR)
        # TWR links sub-period returns between cash flow dates
        twr_annualized = PerformanceService._calculate_twr(df_positive, txn_date_set)

        # Money-Weighted Return (MWR/IRR) using pyxirr
        mwr_annualized = PerformanceService._calculate_mwr(cash_flows, current_value)

        # Sharpe ratio using corrected volatility
        sharpe_ratio = (
            ((daily_return * 252 - risk_free_rate) / volatility) if volatility > 0 else None
        )

        return PerformanceMetrics(
            daily_return=daily_return,
            volatility=volatility,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            net_return=net_return,
            unrealized_roi=unrealized_roi,
            twr_annualized=twr_annualized,
            mwr_annualized=mwr_annualized,
            best_day=best_day,
            worst_day=worst_day,
        )

    @staticmethod
    def _calculate_twr(df_positive: pd.DataFrame, txn_date_set: set[date]) -> float | None:
        """Calculate Time-Weighted Return (TWR).

        TWR measures investment selection performance by linking sub-period returns.
        Each sub-period is between cash flow events, and returns are calculated
        as the percentage change from the day before a cash flow to the day before
        the next cash flow (or end of period).

        Args:
            df_positive: DataFrame with 'date' and 'value' columns (positive values only).
            txn_date_set: Set of dates when transactions occurred.

        Returns:
            Annualized TWR or None if cannot be calculated.

        """
        if len(df_positive) < 2:
            return None

        # Get all transaction dates that are within our date range
        df_dates = set(df_positive['date'])
        relevant_txn_dates = sorted(txn_date_set & df_dates)

        if not relevant_txn_dates:
            # No transactions in period - simple return is TWR
            start_val = df_positive['value'].iloc[0]
            end_val = df_positive['value'].iloc[-1]
            if start_val <= 0:
                return None
            total_return = (end_val / start_val) - 1
            days = (df_positive['date'].iloc[-1] - df_positive['date'].iloc[0]).days
            if days <= 0:
                return None
            return float((1 + total_return) ** (365 / days) - 1)

        # Build sub-periods
        # Each sub-period ends the day BEFORE a transaction (using pre-cash-flow value)
        # and starts from the transaction day (post-cash-flow value)
        sub_period_returns = []

        # First sub-period: from first day to day before first transaction
        first_txn_date = relevant_txn_dates[0]
        pre_first_txn = df_positive[df_positive['date'] < first_txn_date]
        if len(pre_first_txn) >= 1:
            # There are days before the first transaction
            start_val = pre_first_txn['value'].iloc[0]
            end_val = pre_first_txn['value'].iloc[-1]
            if start_val > 0:
                sub_period_returns.append(end_val / start_val)

        # Middle sub-periods: between transactions
        for i, txn_date in enumerate(relevant_txn_dates):
            next_txn_date = relevant_txn_dates[i + 1] if i + 1 < len(relevant_txn_dates) else None

            # Start from transaction day value (post-cash-flow)
            txn_day_rows = df_positive[df_positive['date'] == txn_date]
            if len(txn_day_rows) == 0:
                continue
            start_val = txn_day_rows['value'].iloc[0]

            if next_txn_date:
                # End at day before next transaction
                period_df = df_positive[
                    (df_positive['date'] >= txn_date) & (df_positive['date'] < next_txn_date)
                ]
            else:
                # End at last day of data
                period_df = df_positive[df_positive['date'] >= txn_date]

            if len(period_df) >= 1 and start_val > 0:
                end_val = period_df['value'].iloc[-1]
                sub_period_returns.append(end_val / start_val)

        if not sub_period_returns:
            return None

        # Link sub-period returns: (1+r1) * (1+r2) * ... - already as ratios
        linked_return = 1.0
        for ratio in sub_period_returns:
            linked_return *= ratio

        total_return = linked_return - 1

        # Annualize
        days = (df_positive['date'].iloc[-1] - df_positive['date'].iloc[0]).days
        if days <= 0:
            return None

        return float((1 + total_return) ** (365 / days) - 1)

    @staticmethod
    def _calculate_mwr(cash_flows: list[tuple[date, float]], current_value: float) -> float | None:
        """Calculate Money-Weighted Return (MWR/IRR) using XIRR.

        MWR measures the actual investor experience, accounting for the timing
        and size of cash flows.

        Args:
            cash_flows: List of (date, amount) tuples. Negative = outflow (investment),
                positive = inflow (sale proceeds).
            current_value: Current portfolio value (treated as final inflow).

        Returns:
            Annualized MWR (XIRR) or None if cannot be calculated.

        """
        if not cash_flows:
            return None

        # Prepare data for pyxirr
        # Cash flows: negative = money out (investment), positive = money in
        dates = [cf[0] for cf in cash_flows]
        amounts = [cf[1] for cf in cash_flows]

        # Add current value as final positive cash flow (as if we liquidated today)
        if current_value > 0:
            today = date.today()
            # Ensure final date is after all other dates
            if dates and today <= max(dates):
                today = max(dates) + timedelta(days=1)
            dates.append(today)
            amounts.append(current_value)

        # Need at least one negative and one positive cash flow
        has_negative = any(a < 0 for a in amounts)
        has_positive = any(a > 0 for a in amounts)
        if not (has_negative and has_positive):
            return None

        try:
            xirr_result = pyxirr.xirr(dates, amounts)
            if xirr_result is None or not np.isfinite(xirr_result):
                return None
            return float(xirr_result)
        except Exception:
            # XIRR can fail to converge for certain cash flow patterns
            return None

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
                t.transaction_date.date()
                if hasattr(t.transaction_date, 'date')
                else t.transaction_date
            )
            transaction_dates.append(txn_date)

        # Build cash flows for IRR calculation
        # Buy = negative cash flow (money out), Sell = positive cash flow (money in)
        cash_flows: list[tuple[date, float]] = []
        for t in transactions:
            txn_date = (
                t.transaction_date.date()
                if hasattr(t.transaction_date, 'date')
                else t.transaction_date
            )
            amount = t.units * t.price_per_unit
            if t.transaction_type == 'buy':
                cash_flows.append((txn_date, -amount))  # Investment outflow
            else:  # sell
                cash_flows.append((txn_date, amount))  # Sale inflow

        # Prepare transaction data for FIFO cost basis calculation
        fifo_transactions: list[tuple[int, str, float, float, date]] = []
        for t in transactions:
            txn_date = (
                t.transaction_date.date()
                if hasattr(t.transaction_date, 'date')
                else t.transaction_date
            )
            fifo_transactions.append(
                (t.unit_trust_id, t.transaction_type, t.units, t.price_per_unit, txn_date)
            )

        # Calculate FIFO cost basis
        cost_basis, _ = PerformanceService._calculate_fifo_cost_basis(fifo_transactions)

        metrics = PerformanceService.calculate_metrics(
            history=history,
            transaction_dates=transaction_dates,
            cash_flows=cash_flows,
            total_invested=summary.total_invested,
            total_withdrawn=summary.total_withdrawn,
            current_value=summary.current_value,
            cost_basis=cost_basis,
        )

        return PortfolioPerformance(summary=summary, metrics=metrics, history=history)
