"""Unit tests for performance service calculations."""

from datetime import datetime, timezone

from app.schemas.portfolio import PerformanceMetrics, PortfolioHistory
from app.services.performance import PerformanceService


class TestPerformanceService:
    """Test performance calculation methods."""

    def test_calculate_metrics_basic(self):
        """Test basic metrics calculation with known values."""
        history = [
            PortfolioHistory(date=datetime(2026, 1, 1, tzinfo=timezone.utc), value=1000.0),
            PortfolioHistory(date=datetime(2026, 1, 2, tzinfo=timezone.utc), value=1010.0),
            PortfolioHistory(date=datetime(2026, 1, 3, tzinfo=timezone.utc), value=1015.0),
            PortfolioHistory(date=datetime(2026, 1, 4, tzinfo=timezone.utc), value=1020.0),
        ]

        metrics = PerformanceService.calculate_metrics(history)

        assert isinstance(metrics, PerformanceMetrics)
        assert metrics.daily_return > 0  # Increasing values
        assert metrics.volatility >= 0
        assert metrics.annualized_return > 0
        assert metrics.max_drawdown <= 0

    def test_calculate_metrics_single_point(self):
        """Test metrics with single data point returns zeros."""
        history = [PortfolioHistory(date=datetime(2026, 1, 1, tzinfo=timezone.utc), value=1000.0)]

        metrics = PerformanceService.calculate_metrics(history)

        assert metrics.daily_return == 0.0
        assert metrics.volatility == 0.0
        assert metrics.annualized_return == 0.0
        assert metrics.max_drawdown == 0.0
        assert metrics.sharpe_ratio is None

    def test_calculate_metrics_no_data(self):
        """Test metrics with no data returns zeros."""
        history = []

        metrics = PerformanceService.calculate_metrics(history)

        assert metrics.daily_return == 0.0
        assert metrics.volatility == 0.0
        assert metrics.annualized_return == 0.0
        assert metrics.max_drawdown == 0.0

    def test_calculate_metrics_constant_values(self):
        """Test metrics with no volatility (constant values)."""
        history = [
            PortfolioHistory(date=datetime(2026, 1, i, tzinfo=timezone.utc), value=1000.0)
            for i in range(1, 11)
        ]

        metrics = PerformanceService.calculate_metrics(history)

        assert metrics.volatility == 0.0
        assert metrics.annualized_return == 0.0
        assert metrics.sharpe_ratio is None  # Undefined when volatility is 0

    def test_calculate_metrics_negative_returns(self):
        """Test metrics calculation with declining values."""
        history = [
            PortfolioHistory(date=datetime(2026, 1, 1, tzinfo=timezone.utc), value=1000.0),
            PortfolioHistory(date=datetime(2026, 1, 2, tzinfo=timezone.utc), value=980.0),
            PortfolioHistory(date=datetime(2026, 1, 3, tzinfo=timezone.utc), value=960.0),
            PortfolioHistory(date=datetime(2026, 1, 4, tzinfo=timezone.utc), value=950.0),
        ]

        metrics = PerformanceService.calculate_metrics(history)

        assert metrics.daily_return < 0  # Declining values
        assert metrics.annualized_return < 0
        assert metrics.max_drawdown < 0

    def test_annualized_return_calculation(self):
        """Test annualized return formula."""
        # 10% gain over 365 days should be close to 10% annualized
        history = [
            PortfolioHistory(date=datetime(2025, 1, 1, tzinfo=timezone.utc), value=1000.0),
            PortfolioHistory(date=datetime(2026, 1, 1, tzinfo=timezone.utc), value=1100.0),
        ]

        metrics = PerformanceService.calculate_metrics(history)

        # Should be approximately 10%
        assert 0.09 < metrics.annualized_return < 0.11

    def test_max_drawdown_calculation(self):
        """Test max drawdown identifies largest peak-to-trough decline."""
        history = [
            PortfolioHistory(date=datetime(2026, 1, 1, tzinfo=timezone.utc), value=1000.0),
            PortfolioHistory(date=datetime(2026, 1, 2, tzinfo=timezone.utc), value=1100.0),  # Peak
            PortfolioHistory(
                date=datetime(2026, 1, 3, tzinfo=timezone.utc), value=900.0
            ),  # Trough (-18.2%)
            PortfolioHistory(date=datetime(2026, 1, 4, tzinfo=timezone.utc), value=950.0),
        ]

        metrics = PerformanceService.calculate_metrics(history)

        # Max drawdown from 1100 to 900 = -18.18%
        assert -0.19 < metrics.max_drawdown < -0.18

    def test_sharpe_ratio_zero_volatility(self):
        """Test Sharpe ratio returns None when volatility is zero."""
        history = [
            PortfolioHistory(date=datetime(2026, 1, i, tzinfo=timezone.utc), value=1000.0)
            for i in range(1, 6)
        ]

        metrics = PerformanceService.calculate_metrics(history)

        assert metrics.sharpe_ratio is None

    def test_sharpe_ratio_with_custom_risk_free_rate(self):
        """Test Sharpe ratio calculation with custom risk-free rate."""
        history = [
            PortfolioHistory(date=datetime(2026, 1, 1, tzinfo=timezone.utc), value=1000.0),
            PortfolioHistory(date=datetime(2026, 1, 2, tzinfo=timezone.utc), value=1010.0),
            PortfolioHistory(date=datetime(2026, 1, 3, tzinfo=timezone.utc), value=1020.0),
            PortfolioHistory(date=datetime(2026, 1, 4, tzinfo=timezone.utc), value=1015.0),
            PortfolioHistory(date=datetime(2026, 1, 5, tzinfo=timezone.utc), value=1025.0),
        ]

        metrics = PerformanceService.calculate_metrics(history, risk_free_rate=0.05)

        assert metrics.sharpe_ratio is not None
        assert isinstance(metrics.sharpe_ratio, float)
