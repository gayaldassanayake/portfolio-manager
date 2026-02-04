"""Portfolio-related Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel


class PortfolioSummary(BaseModel):
    """Summary of portfolio performance.

    Attributes:
        total_invested: Total amount invested (sum of all buy transactions).
        total_withdrawn: Total amount withdrawn (sum of all sell proceeds).
        current_value: Current portfolio value.
        total_gain_loss: Net gain or loss (current_value + withdrawn - invested).
        roi_percentage: Net return percentage (gain_loss / invested * 100).
        total_units: Total units held.
        holding_count: Number of different holdings.

    """

    total_invested: float
    total_withdrawn: float
    current_value: float
    total_gain_loss: float
    roi_percentage: float
    total_units: int
    holding_count: int


class PerformanceMetrics(BaseModel):
    """Portfolio performance metrics.

    Attributes:
        daily_return: Average daily return (price-based, excludes transaction days).
        volatility: Annualized volatility (price-based, excludes transaction days).
        max_drawdown: Maximum drawdown.
        sharpe_ratio: Sharpe ratio (risk-adjusted return).
        net_return: Net return including realized gains (current + withdrawn - invested) / invested.
        unrealized_roi: Return on current holdings vs FIFO cost basis.
        twr_annualized: Time-weighted annualized return (measures investment selection).
        mwr_annualized: Money-weighted annualized return / IRR (measures actual experience).
        best_day: Best single-day return.
        worst_day: Worst single-day return.

    """

    daily_return: float
    volatility: float
    max_drawdown: float
    sharpe_ratio: float | None = None
    net_return: float
    unrealized_roi: float
    twr_annualized: float | None = None
    mwr_annualized: float | None = None
    best_day: float | None = None
    worst_day: float | None = None


class PortfolioHistory(BaseModel):
    """Historical portfolio value at a specific date.

    Attributes:
        date: Date of the portfolio value.
        value: Portfolio value on that date.

    """

    date: datetime
    value: float


class PortfolioPerformance(BaseModel):
    """Complete portfolio performance data.

    Attributes:
        summary: Portfolio summary.
        metrics: Performance metrics.
        history: Historical values.

    """

    summary: PortfolioSummary
    metrics: PerformanceMetrics
    history: list[PortfolioHistory]
