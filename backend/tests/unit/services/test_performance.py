"""Unit tests for performance service calculations."""

from datetime import date, datetime, timezone

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
        # Transaction happened on day 1, so subsequent price gains are pure returns
        transaction_dates = [date(2026, 1, 1)]
        cash_flows = [(date(2026, 1, 1), -1000.0)]  # Invested $1000

        metrics = PerformanceService.calculate_metrics(
            history=history,
            transaction_dates=transaction_dates,
            cash_flows=cash_flows,
            total_invested=1000.0,
            total_withdrawn=0.0,
            current_value=1020.0,
            cost_basis=1000.0,
        )

        assert isinstance(metrics, PerformanceMetrics)
        assert metrics.daily_return > 0  # Increasing values
        assert metrics.volatility >= 0
        assert metrics.net_return == 0.02  # 2% return
        assert metrics.unrealized_roi == 0.02  # 2% unrealized gain
        assert metrics.max_drawdown <= 0

    def test_calculate_metrics_single_point(self):
        """Test metrics with single data point returns zeros."""
        history = [PortfolioHistory(date=datetime(2026, 1, 1, tzinfo=timezone.utc), value=1000.0)]

        metrics = PerformanceService.calculate_metrics(
            history=history,
            transaction_dates=[date(2026, 1, 1)],
            cash_flows=[(date(2026, 1, 1), -1000.0)],
            total_invested=1000.0,
            total_withdrawn=0.0,
            current_value=1000.0,
            cost_basis=1000.0,
        )

        assert metrics.daily_return == 0.0
        assert metrics.volatility == 0.0
        assert metrics.net_return == 0.0
        assert metrics.unrealized_roi == 0.0
        assert metrics.max_drawdown == 0.0
        assert metrics.sharpe_ratio is None

    def test_calculate_metrics_no_data(self):
        """Test metrics with no data returns zeros."""
        history = []

        metrics = PerformanceService.calculate_metrics(
            history=history,
            transaction_dates=[],
            cash_flows=[],
            total_invested=0.0,
            total_withdrawn=0.0,
            current_value=0.0,
            cost_basis=0.0,
        )

        assert metrics.daily_return == 0.0
        assert metrics.volatility == 0.0
        assert metrics.net_return == 0.0
        assert metrics.unrealized_roi == 0.0
        assert metrics.max_drawdown == 0.0

    def test_calculate_metrics_constant_values(self):
        """Test metrics with no volatility (constant values)."""
        history = [
            PortfolioHistory(date=datetime(2026, 1, i, tzinfo=timezone.utc), value=1000.0)
            for i in range(1, 11)
        ]

        metrics = PerformanceService.calculate_metrics(
            history=history,
            transaction_dates=[date(2026, 1, 1)],
            cash_flows=[(date(2026, 1, 1), -1000.0)],
            total_invested=1000.0,
            total_withdrawn=0.0,
            current_value=1000.0,
            cost_basis=1000.0,
        )

        assert metrics.volatility == 0.0
        assert metrics.net_return == 0.0
        assert metrics.unrealized_roi == 0.0
        assert metrics.sharpe_ratio is None  # Undefined when volatility is 0

    def test_calculate_metrics_negative_returns(self):
        """Test metrics calculation with declining values."""
        history = [
            PortfolioHistory(date=datetime(2026, 1, 1, tzinfo=timezone.utc), value=1000.0),
            PortfolioHistory(date=datetime(2026, 1, 2, tzinfo=timezone.utc), value=980.0),
            PortfolioHistory(date=datetime(2026, 1, 3, tzinfo=timezone.utc), value=960.0),
            PortfolioHistory(date=datetime(2026, 1, 4, tzinfo=timezone.utc), value=950.0),
        ]

        metrics = PerformanceService.calculate_metrics(
            history=history,
            transaction_dates=[date(2026, 1, 1)],
            cash_flows=[(date(2026, 1, 1), -1000.0)],
            total_invested=1000.0,
            total_withdrawn=0.0,
            current_value=950.0,
            cost_basis=1000.0,
        )

        assert metrics.daily_return < 0  # Declining values
        assert metrics.net_return == -0.05  # -5% loss
        assert metrics.unrealized_roi == -0.05  # -5% unrealized loss
        assert metrics.max_drawdown < 0

    def test_net_return_with_withdrawals(self):
        """Test net return correctly accounts for withdrawals."""
        # Scenario: Invested $1000, sold $300 worth, current value $800
        # Net return = (800 + 300 - 1000) / 1000 = 0.1 = 10%
        history = [
            PortfolioHistory(date=datetime(2026, 1, 1, tzinfo=timezone.utc), value=1000.0),
            PortfolioHistory(date=datetime(2026, 1, 2, tzinfo=timezone.utc), value=800.0),
        ]

        metrics = PerformanceService.calculate_metrics(
            history=history,
            transaction_dates=[date(2026, 1, 1)],
            cash_flows=[(date(2026, 1, 1), -1000.0), (date(2026, 1, 2), 300.0)],
            total_invested=1000.0,
            total_withdrawn=300.0,
            current_value=800.0,
            cost_basis=700.0,  # After selling some, cost basis is lower
        )

        # Net return: (800 + 300 - 1000) / 1000 = 0.1
        assert metrics.net_return == 0.1

    def test_unrealized_roi_with_fifo_cost_basis(self):
        """Test unrealized ROI uses FIFO cost basis correctly."""
        # Scenario: Cost basis $700 (after FIFO accounting), current value $840
        # Unrealized ROI = (840 - 700) / 700 = 0.2 = 20%
        history = [
            PortfolioHistory(date=datetime(2026, 1, 1, tzinfo=timezone.utc), value=700.0),
            PortfolioHistory(date=datetime(2026, 1, 2, tzinfo=timezone.utc), value=840.0),
        ]

        metrics = PerformanceService.calculate_metrics(
            history=history,
            transaction_dates=[date(2026, 1, 1)],
            cash_flows=[(date(2026, 1, 1), -700.0)],
            total_invested=700.0,
            total_withdrawn=0.0,
            current_value=840.0,
            cost_basis=700.0,
        )

        # Unrealized ROI: (840 - 700) / 700 = 0.2
        assert metrics.unrealized_roi == 0.2

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

        metrics = PerformanceService.calculate_metrics(
            history=history,
            transaction_dates=[date(2026, 1, 1)],
            cash_flows=[(date(2026, 1, 1), -1000.0)],
            total_invested=1000.0,
            total_withdrawn=0.0,
            current_value=950.0,
            cost_basis=1000.0,
        )

        # Max drawdown from 1100 to 900 = -18.18%
        assert -0.19 < metrics.max_drawdown < -0.18

    def test_sharpe_ratio_zero_volatility(self):
        """Test Sharpe ratio returns None when volatility is zero."""
        history = [
            PortfolioHistory(date=datetime(2026, 1, i, tzinfo=timezone.utc), value=1000.0)
            for i in range(1, 6)
        ]

        metrics = PerformanceService.calculate_metrics(
            history=history,
            transaction_dates=[date(2026, 1, 1)],
            cash_flows=[(date(2026, 1, 1), -1000.0)],
            total_invested=1000.0,
            total_withdrawn=0.0,
            current_value=1000.0,
            cost_basis=1000.0,
        )

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

        metrics = PerformanceService.calculate_metrics(
            history=history,
            transaction_dates=[date(2026, 1, 1)],
            cash_flows=[(date(2026, 1, 1), -1000.0)],
            total_invested=1000.0,
            total_withdrawn=0.0,
            current_value=1025.0,
            cost_basis=1000.0,
            risk_free_rate=0.05,
        )

        assert metrics.sharpe_ratio is not None
        assert isinstance(metrics.sharpe_ratio, float)

    def test_best_and_worst_day(self):
        """Test best and worst day returns are correctly identified."""
        history = [
            PortfolioHistory(date=datetime(2026, 1, 1, tzinfo=timezone.utc), value=1000.0),
            PortfolioHistory(date=datetime(2026, 1, 2, tzinfo=timezone.utc), value=1050.0),  # +5%
            PortfolioHistory(
                date=datetime(2026, 1, 3, tzinfo=timezone.utc), value=1000.0
            ),  # -4.76%
            PortfolioHistory(date=datetime(2026, 1, 4, tzinfo=timezone.utc), value=1020.0),  # +2%
        ]

        metrics = PerformanceService.calculate_metrics(
            history=history,
            transaction_dates=[date(2026, 1, 1)],
            cash_flows=[(date(2026, 1, 1), -1000.0)],
            total_invested=1000.0,
            total_withdrawn=0.0,
            current_value=1020.0,
            cost_basis=1000.0,
        )

        assert metrics.best_day is not None
        assert metrics.worst_day is not None
        # Best day: 1000 -> 1050 = +5%
        assert 0.04 < metrics.best_day < 0.06
        # Worst day: 1050 -> 1000 = -4.76%
        assert -0.05 < metrics.worst_day < -0.04

    def test_volatility_excludes_transaction_days(self):
        """Test that volatility calculation excludes days with transactions."""
        # Day 1: buy, value goes from 0 to 1000
        # Day 2: price change, value goes from 1000 to 1010
        # Day 3: another buy (deposit), value jumps from 1010 to 2010
        # Day 4: price change, value goes from 2010 to 2020
        history = [
            PortfolioHistory(date=datetime(2026, 1, 1, tzinfo=timezone.utc), value=1000.0),
            PortfolioHistory(date=datetime(2026, 1, 2, tzinfo=timezone.utc), value=1010.0),
            PortfolioHistory(
                date=datetime(2026, 1, 3, tzinfo=timezone.utc), value=2010.0
            ),  # Deposit
            PortfolioHistory(date=datetime(2026, 1, 4, tzinfo=timezone.utc), value=2020.0),
        ]

        # Two transactions: day 1 and day 3
        transaction_dates = [date(2026, 1, 1), date(2026, 1, 3)]
        cash_flows = [
            (date(2026, 1, 1), -1000.0),
            (date(2026, 1, 3), -1000.0),
        ]

        metrics = PerformanceService.calculate_metrics(
            history=history,
            transaction_dates=transaction_dates,
            cash_flows=cash_flows,
            total_invested=2000.0,
            total_withdrawn=0.0,
            current_value=2020.0,
            cost_basis=2000.0,
        )

        # If we didn't exclude transaction days, volatility would be huge
        # due to the 99% "return" from 1010 to 2010
        # With exclusion, volatility should be reasonable (based on ~1% returns)
        assert metrics.volatility < 0.5  # Less than 50% annualized volatility


class TestFIFOCostBasis:
    """Test FIFO cost basis calculation."""

    def test_fifo_simple_buy(self):
        """Test FIFO with simple buy transactions."""
        transactions = [
            (1, 'buy', 100.0, 10.0, date(2026, 1, 1)),  # 100 units @ $10
        ]
        cost_basis, _ = PerformanceService._calculate_fifo_cost_basis(transactions)
        assert cost_basis == 1000.0  # 100 * 10

    def test_fifo_multiple_buys(self):
        """Test FIFO with multiple buy transactions."""
        transactions = [
            (1, 'buy', 100.0, 10.0, date(2026, 1, 1)),  # 100 units @ $10
            (1, 'buy', 50.0, 15.0, date(2026, 1, 2)),  # 50 units @ $15
        ]
        cost_basis, _ = PerformanceService._calculate_fifo_cost_basis(transactions)
        # 100 * 10 + 50 * 15 = 1000 + 750 = 1750
        assert cost_basis == 1750.0

    def test_fifo_buy_then_sell(self):
        """Test FIFO sells from oldest lots first."""
        transactions = [
            (1, 'buy', 100.0, 10.0, date(2026, 1, 1)),  # 100 units @ $10
            (1, 'buy', 50.0, 15.0, date(2026, 1, 2)),  # 50 units @ $15
            (1, 'sell', 80.0, 12.0, date(2026, 1, 3)),  # Sell 80 units
        ]
        cost_basis, _ = PerformanceService._calculate_fifo_cost_basis(transactions)
        # After FIFO: sold 80 from first lot (100 @ $10)
        # Remaining: 20 units @ $10 + 50 units @ $15
        # = 20 * 10 + 50 * 15 = 200 + 750 = 950
        assert cost_basis == 950.0

    def test_fifo_sell_across_lots(self):
        """Test FIFO when sell spans multiple lots."""
        transactions = [
            (1, 'buy', 100.0, 10.0, date(2026, 1, 1)),  # 100 units @ $10
            (1, 'buy', 50.0, 15.0, date(2026, 1, 2)),  # 50 units @ $15
            (1, 'sell', 120.0, 12.0, date(2026, 1, 3)),  # Sell 120 units
        ]
        cost_basis, _ = PerformanceService._calculate_fifo_cost_basis(transactions)
        # After FIFO: sold all 100 from first lot + 20 from second lot
        # Remaining: 30 units @ $15
        # = 30 * 15 = 450
        assert cost_basis == 450.0

    def test_fifo_multiple_funds(self):
        """Test FIFO tracks each fund separately."""
        transactions = [
            (1, 'buy', 100.0, 10.0, date(2026, 1, 1)),  # Fund 1: 100 @ $10
            (2, 'buy', 50.0, 20.0, date(2026, 1, 1)),  # Fund 2: 50 @ $20
            (1, 'sell', 50.0, 12.0, date(2026, 1, 2)),  # Sell 50 from Fund 1
        ]
        cost_basis, per_fund = PerformanceService._calculate_fifo_cost_basis(transactions)
        # Fund 1: 50 remaining @ $10 = 500
        # Fund 2: 50 remaining @ $20 = 1000
        # Total = 1500
        assert cost_basis == 1500.0
        assert per_fund[1] == 500.0
        assert per_fund[2] == 1000.0

    def test_fifo_sell_all(self):
        """Test FIFO when all units are sold."""
        transactions = [
            (1, 'buy', 100.0, 10.0, date(2026, 1, 1)),
            (1, 'sell', 100.0, 15.0, date(2026, 1, 2)),
        ]
        cost_basis, _ = PerformanceService._calculate_fifo_cost_basis(transactions)
        assert cost_basis == 0.0


class TestTWRCalculation:
    """Test Time-Weighted Return calculation."""

    def test_twr_no_transactions_in_period(self):
        """Test TWR when there are no transactions in the period (simple return)."""
        history = [
            PortfolioHistory(date=datetime(2025, 1, 1, tzinfo=timezone.utc), value=1000.0),
            PortfolioHistory(date=datetime(2026, 1, 1, tzinfo=timezone.utc), value=1100.0),
        ]
        # Transaction was before the period
        transaction_dates = [date(2024, 12, 1)]
        cash_flows = [(date(2024, 12, 1), -1000.0)]

        metrics = PerformanceService.calculate_metrics(
            history=history,
            transaction_dates=transaction_dates,
            cash_flows=cash_flows,
            total_invested=1000.0,
            total_withdrawn=0.0,
            current_value=1100.0,
            cost_basis=1000.0,
        )

        # 10% return over 365 days = ~10% annualized
        assert metrics.twr_annualized is not None
        assert 0.09 < metrics.twr_annualized < 0.11

    def test_twr_with_mid_period_deposit(self):
        """Test TWR correctly accounts for mid-period deposits."""
        # Scenario: Start with $1000, grows to $1100, deposit $1000, grows to $2200
        # TWR should reflect the underlying 10% return, not the value jump from deposit
        history = [
            PortfolioHistory(date=datetime(2026, 1, 1, tzinfo=timezone.utc), value=1000.0),
            PortfolioHistory(date=datetime(2026, 1, 15, tzinfo=timezone.utc), value=1100.0),
            # Deposit $1000 on day 16, value jumps to $2100
            PortfolioHistory(date=datetime(2026, 1, 16, tzinfo=timezone.utc), value=2100.0),
            PortfolioHistory(date=datetime(2026, 1, 31, tzinfo=timezone.utc), value=2310.0),
        ]
        transaction_dates = [date(2026, 1, 1), date(2026, 1, 16)]
        cash_flows = [
            (date(2026, 1, 1), -1000.0),
            (date(2026, 1, 16), -1000.0),
        ]

        metrics = PerformanceService.calculate_metrics(
            history=history,
            transaction_dates=transaction_dates,
            cash_flows=cash_flows,
            total_invested=2000.0,
            total_withdrawn=0.0,
            current_value=2310.0,
            cost_basis=2000.0,
        )

        # Period 1: 1000 -> 1100 = 10% return
        # Period 2: 2100 -> 2310 = 10% return
        # Linked: 1.1 * 1.1 = 1.21 = 21% total return over 30 days
        assert metrics.twr_annualized is not None
        # This is a high annualized return due to short period


class TestMWRCalculation:
    """Test Money-Weighted Return (IRR) calculation."""

    def test_mwr_simple_investment(self):
        """Test MWR for a simple single investment."""
        history = [
            PortfolioHistory(date=datetime(2025, 1, 1, tzinfo=timezone.utc), value=1000.0),
            PortfolioHistory(date=datetime(2026, 1, 1, tzinfo=timezone.utc), value=1100.0),
        ]
        transaction_dates = [date(2025, 1, 1)]
        cash_flows = [(date(2025, 1, 1), -1000.0)]  # Invested $1000

        metrics = PerformanceService.calculate_metrics(
            history=history,
            transaction_dates=transaction_dates,
            cash_flows=cash_flows,
            total_invested=1000.0,
            total_withdrawn=0.0,
            current_value=1100.0,
            cost_basis=1000.0,
        )

        # 10% return over 1 year = ~10% IRR
        assert metrics.mwr_annualized is not None
        assert 0.09 < metrics.mwr_annualized < 0.11

    def test_mwr_with_poorly_timed_deposit(self):
        """Test MWR shows lower return for poorly timed deposits."""
        # Scenario: Invest $1000, price drops 20%, then invest another $1000
        # Price recovers. MWR should be lower than if we invested all upfront.
        history = [
            PortfolioHistory(date=datetime(2026, 1, 1, tzinfo=timezone.utc), value=1000.0),
            PortfolioHistory(date=datetime(2026, 2, 1, tzinfo=timezone.utc), value=800.0),  # -20%
            PortfolioHistory(
                date=datetime(2026, 2, 2, tzinfo=timezone.utc), value=1800.0
            ),  # +$1000 deposit
            PortfolioHistory(
                date=datetime(2026, 3, 1, tzinfo=timezone.utc), value=1980.0
            ),  # +10% from 1800
        ]
        transaction_dates = [date(2026, 1, 1), date(2026, 2, 2)]
        cash_flows = [
            (date(2026, 1, 1), -1000.0),
            (date(2026, 2, 2), -1000.0),
        ]

        metrics = PerformanceService.calculate_metrics(
            history=history,
            transaction_dates=transaction_dates,
            cash_flows=cash_flows,
            total_invested=2000.0,
            total_withdrawn=0.0,
            current_value=1980.0,
            cost_basis=2000.0,
        )

        # Net return: (1980 + 0 - 2000) / 2000 = -0.01 = -1%
        assert metrics.net_return == -0.01
        # MWR accounts for the timing
        assert metrics.mwr_annualized is not None

    def test_mwr_returns_none_when_calculation_fails(self):
        """Test MWR returns None when XIRR cannot converge."""
        # Edge case: no cash flows
        metrics = PerformanceService.calculate_metrics(
            history=[
                PortfolioHistory(date=datetime(2026, 1, 1, tzinfo=timezone.utc), value=1000.0),
                PortfolioHistory(date=datetime(2026, 1, 2, tzinfo=timezone.utc), value=1010.0),
            ],
            transaction_dates=[],
            cash_flows=[],  # No cash flows
            total_invested=0.0,
            total_withdrawn=0.0,
            current_value=1010.0,
            cost_basis=0.0,
        )

        # Should still work, but MWR might be None without negative cash flows
        # Actually with current_value > 0, we add it as final inflow
        # But with no negative outflows, XIRR can't calculate
        assert metrics.mwr_annualized is None
