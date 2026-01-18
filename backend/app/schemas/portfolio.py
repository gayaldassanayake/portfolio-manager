"""Portfolio-related Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel


class PortfolioSummary(BaseModel):
    """Summary of portfolio performance.

    Attributes:
        total_invested: Total amount invested.
        current_value: Current portfolio value.
        total_gain_loss: Total gain or loss amount.
        roi_percentage: Return on investment percentage.
        total_units: Total units held.
        holding_count: Number of different holdings.

    """

    total_invested: float
    current_value: float
    total_gain_loss: float
    roi_percentage: float
    total_units: int
    holding_count: int


class PerformanceMetrics(BaseModel):
    """Portfolio performance metrics.

    Attributes:
        daily_return: Average daily return.
        volatility: Annualized volatility.
        annualized_return: Annualized return.
        max_drawdown: Maximum drawdown.
        sharpe_ratio: Sharpe ratio (risk-adjusted return).

    """

    daily_return: float
    volatility: float
    annualized_return: float
    max_drawdown: float
    sharpe_ratio: float | None = None


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
