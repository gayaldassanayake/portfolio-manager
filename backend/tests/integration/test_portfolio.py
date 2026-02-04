"""Integration tests for portfolio performance API endpoints."""

from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.factories import make_price, make_price_history, make_transaction, make_unit_trust


@pytest.mark.asyncio
class TestPortfolioAPI:
    """Test portfolio performance endpoints."""

    async def test_portfolio_summary_empty(self, client: AsyncClient):
        """Test portfolio summary with no transactions."""
        response = await client.get('/api/v1/portfolio/summary')
        assert response.status_code == 200
        data = response.json()
        assert data['total_invested'] == 0.0
        assert data['current_value'] == 0.0
        assert data['total_gain_loss'] == 0.0
        assert data['roi_percentage'] == 0.0
        assert data['total_units'] == 0
        assert data['holding_count'] == 0

    async def test_portfolio_summary_single_holding(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """Test portfolio summary with single holding."""
        ut = make_unit_trust()
        test_date = datetime(2026, 1, 1, tzinfo=timezone.utc)
        price = make_price(unit_trust_id=1, date=test_date, price=100.0)
        latest_price = make_price(
            unit_trust_id=1, date=datetime(2026, 1, 15, tzinfo=timezone.utc), price=110.0
        )
        txn = make_transaction(unit_trust_id=1, units=10.0, price_per_unit=100.0)
        test_db.add_all([ut, price, latest_price, txn])
        await test_db.commit()

        response = await client.get('/api/v1/portfolio/summary')
        assert response.status_code == 200
        data = response.json()
        assert data['total_invested'] == 1000.0  # 10 * 100
        assert data['current_value'] == 1100.0  # 10 * 110
        assert data['total_gain_loss'] == 100.0
        assert data['roi_percentage'] == 10.0
        assert data['total_units'] == 10
        assert data['holding_count'] == 1

    async def test_portfolio_summary_multiple_holdings(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """Test portfolio summary with multiple holdings."""
        ut1 = make_unit_trust(symbol='FUND1')
        ut2 = make_unit_trust(symbol='FUND2')

        price1 = make_price(unit_trust_id=1, price=100.0)
        price2 = make_price(unit_trust_id=2, price=200.0)

        txn1 = make_transaction(unit_trust_id=1, units=10.0, price_per_unit=100.0)
        txn2 = make_transaction(unit_trust_id=2, units=5.0, price_per_unit=200.0)

        test_db.add_all([ut1, ut2, price1, price2, txn1, txn2])
        await test_db.commit()

        response = await client.get('/api/v1/portfolio/summary')
        assert response.status_code == 200
        data = response.json()
        assert data['total_invested'] == 2000.0  # (10*100) + (5*200)
        assert data['current_value'] == 2000.0  # Same prices
        assert data['holding_count'] == 2

    async def test_portfolio_summary_with_gain(self, client: AsyncClient, test_db: AsyncSession):
        """Test portfolio summary with positive gain."""
        ut = make_unit_trust()
        buy_price = make_price(
            unit_trust_id=1, date=datetime(2026, 1, 1, tzinfo=timezone.utc), price=100.0
        )
        current_price = make_price(
            unit_trust_id=1, date=datetime(2026, 1, 15, tzinfo=timezone.utc), price=150.0
        )
        txn = make_transaction(unit_trust_id=1, units=10.0, price_per_unit=100.0)
        test_db.add_all([ut, buy_price, current_price, txn])
        await test_db.commit()

        response = await client.get('/api/v1/portfolio/summary')
        assert response.status_code == 200
        data = response.json()
        assert data['total_gain_loss'] == 500.0
        assert data['roi_percentage'] == 50.0

    async def test_portfolio_summary_with_loss(self, client: AsyncClient, test_db: AsyncSession):
        """Test portfolio summary with loss."""
        ut = make_unit_trust()
        buy_price = make_price(
            unit_trust_id=1, date=datetime(2026, 1, 1, tzinfo=timezone.utc), price=100.0
        )
        current_price = make_price(
            unit_trust_id=1, date=datetime(2026, 1, 15, tzinfo=timezone.utc), price=80.0
        )
        txn = make_transaction(unit_trust_id=1, units=10.0, price_per_unit=100.0)
        test_db.add_all([ut, buy_price, current_price, txn])
        await test_db.commit()

        response = await client.get('/api/v1/portfolio/summary')
        assert response.status_code == 200
        data = response.json()
        assert data['total_gain_loss'] == -200.0
        assert data['roi_percentage'] == -20.0

    async def test_portfolio_summary_with_buy_and_sell(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """Test portfolio summary with buy and sell transactions."""
        ut = make_unit_trust()
        current_price = make_price(
            unit_trust_id=1, date=datetime(2026, 1, 15, tzinfo=timezone.utc), price=120.0
        )
        # Buy 10 units at 100
        txn_buy = make_transaction(
            unit_trust_id=1, units=10.0, price_per_unit=100.0, transaction_type='buy'
        )
        # Sell 3 units at 110
        txn_sell = make_transaction(
            unit_trust_id=1, units=3.0, price_per_unit=110.0, transaction_type='sell'
        )
        test_db.add_all([ut, current_price, txn_buy, txn_sell])
        await test_db.commit()

        response = await client.get('/api/v1/portfolio/summary')
        assert response.status_code == 200
        data = response.json()
        # Total invested = only buy transactions = 10 * 100 = 1000
        assert data['total_invested'] == 1000.0
        # Total withdrawn = sell proceeds = 3 * 110 = 330
        assert data['total_withdrawn'] == 330.0
        # Net units = 10 - 3 = 7
        assert data['total_units'] == 7
        # Current value = 7 * 120 = 840
        assert data['current_value'] == 840.0
        # Net gain/loss = current_value + total_withdrawn - total_invested
        # = 840 + 330 - 1000 = 170 (net profit including realized gain from sale)
        assert data['total_gain_loss'] == 170.0
        assert data['holding_count'] == 1

    async def test_portfolio_performance_empty(self, client: AsyncClient):
        """Test portfolio performance with no data."""
        response = await client.get('/api/v1/portfolio/performance')
        assert response.status_code == 200
        data = response.json()
        assert 'summary' in data
        assert 'metrics' in data
        assert 'history' in data
        assert data['summary']['total_invested'] == 0.0
        assert data['history'] == []

    async def test_portfolio_performance_with_data(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """Test portfolio performance returns all components."""
        ut = make_unit_trust()
        prices = make_price_history(unit_trust_id=1, days=30, start_price=100.0)
        # Create transaction at the start of the price history period
        transaction_date = datetime.now(timezone.utc) - timedelta(days=30)
        txn = make_transaction(
            unit_trust_id=1, units=10.0, price_per_unit=100.0, transaction_date=transaction_date
        )
        test_db.add_all([ut, *prices, txn])
        await test_db.commit()

        response = await client.get('/api/v1/portfolio/performance?days=30')
        assert response.status_code == 200
        data = response.json()

        assert 'summary' in data
        assert 'metrics' in data
        assert 'history' in data

        assert data['summary']['total_invested'] > 0
        assert len(data['history']) > 0

        # Check metrics are present
        metrics = data['metrics']
        assert 'daily_return' in metrics
        assert 'volatility' in metrics
        assert 'twr_annualized' in metrics
        assert 'mwr_annualized' in metrics
        assert 'net_return' in metrics
        assert 'unrealized_roi' in metrics
        assert 'max_drawdown' in metrics
        assert 'best_day' in metrics
        assert 'worst_day' in metrics

    async def test_portfolio_history_empty(self, client: AsyncClient):
        """Test portfolio history with no prices."""
        response = await client.get('/api/v1/portfolio/history')
        assert response.status_code == 200
        assert response.json() == []

    async def test_portfolio_history_date_range(self, client: AsyncClient, test_db: AsyncSession):
        """Test portfolio history respects days parameter."""
        from datetime import datetime, timedelta, timezone

        ut = make_unit_trust()
        prices = make_price_history(unit_trust_id=1, days=60, start_price=100.0)
        # Create transaction at the start of the price history period
        transaction_date = datetime.now(timezone.utc) - timedelta(days=60)
        txn = make_transaction(
            unit_trust_id=1, units=10.0, price_per_unit=100.0, transaction_date=transaction_date
        )
        test_db.add_all([ut, *prices, txn])
        await test_db.commit()

        response = await client.get('/api/v1/portfolio/history?days=30')
        assert response.status_code == 200
        data = response.json()

        # Should only return last 30 days
        assert len(data) <= 31  # Inclusive of start and end dates

    async def test_portfolio_metrics_with_data(self, client: AsyncClient, test_db: AsyncSession):
        """Test portfolio metrics calculation."""
        ut = make_unit_trust()
        # Create price history with some volatility
        base_date = datetime.now(timezone.utc) - timedelta(days=30)
        prices = []
        for i in range(30):
            date = base_date + timedelta(days=i)
            price_val = 100.0 + (i * 0.5)  # Gradually increasing
            prices.append(make_price(unit_trust_id=1, date=date, price=price_val))

        # Create transaction at start of price history
        txn = make_transaction(
            unit_trust_id=1,
            units=10.0,
            price_per_unit=100.0,
            transaction_date=base_date,
        )
        test_db.add_all([ut, *prices, txn])
        await test_db.commit()

        response = await client.get('/api/v1/portfolio/metrics?days=30')
        assert response.status_code == 200
        data = response.json()

        assert data['volatility'] >= 0
        assert data['daily_return'] is not None
        assert data['net_return'] is not None
        assert data['unrealized_roi'] is not None
        assert data['max_drawdown'] <= 0  # Drawdown is negative or zero
        # TWR and MWR may or may not be None depending on calculation success
        assert 'twr_annualized' in data
        assert 'mwr_annualized' in data


@pytest.mark.asyncio
class TestPortfolioHistoryEquityCurve:
    """Test portfolio history as a true equity curve.

    These tests verify that the portfolio history reflects holdings as they
    existed at each point in time, not current holdings applied retroactively.
    """

    async def test_history_zero_before_first_transaction(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """Portfolio value should be zero before any transactions."""
        ut = make_unit_trust()
        base_date = datetime.now(timezone.utc) - timedelta(days=10)

        # Create prices for all 10 days
        prices = [
            make_price(unit_trust_id=1, date=base_date + timedelta(days=i), price=100.0)
            for i in range(10)
        ]

        # Transaction happens on day 5
        txn_date = base_date + timedelta(days=5)
        txn = make_transaction(
            unit_trust_id=1,
            units=10.0,
            price_per_unit=100.0,
            transaction_date=txn_date,
        )

        test_db.add_all([ut, *prices, txn])
        await test_db.commit()

        response = await client.get('/api/v1/portfolio/history?days=15')
        assert response.status_code == 200
        data = response.json()

        # Convert to dict for easier lookup
        history_by_date = {h['date'][:10]: h['value'] for h in data}

        # Days before transaction should have 0 value
        for i in range(5):
            date_str = (base_date + timedelta(days=i)).strftime('%Y-%m-%d')
            if date_str in history_by_date:
                assert history_by_date[date_str] == 0.0, f'Day {i} should be 0 before transaction'

        # Days from transaction onward should have positive value
        for i in range(5, 10):
            date_str = (base_date + timedelta(days=i)).strftime('%Y-%m-%d')
            if date_str in history_by_date:
                assert history_by_date[date_str] > 0, (
                    f'Day {i} should have positive value after transaction'
                )

    async def test_history_increases_after_buy(self, client: AsyncClient, test_db: AsyncSession):
        """Portfolio value should increase when a buy transaction occurs."""
        ut = make_unit_trust()
        base_date = datetime.now(timezone.utc) - timedelta(days=10)

        # Prices at 100 throughout
        prices = [
            make_price(unit_trust_id=1, date=base_date + timedelta(days=i), price=100.0)
            for i in range(10)
        ]

        # First buy on day 2: 10 units
        txn1 = make_transaction(
            unit_trust_id=1,
            units=10.0,
            price_per_unit=100.0,
            transaction_date=base_date + timedelta(days=2),
        )
        # Second buy on day 6: 5 more units
        txn2 = make_transaction(
            unit_trust_id=1,
            units=5.0,
            price_per_unit=100.0,
            transaction_date=base_date + timedelta(days=6),
        )

        test_db.add_all([ut, *prices, txn1, txn2])
        await test_db.commit()

        response = await client.get('/api/v1/portfolio/history?days=15')
        assert response.status_code == 200
        data = response.json()

        history_by_date = {h['date'][:10]: h['value'] for h in data}

        # Days 2-5: should have 10 * 100 = 1000
        for i in range(2, 6):
            date_str = (base_date + timedelta(days=i)).strftime('%Y-%m-%d')
            if date_str in history_by_date:
                assert abs(history_by_date[date_str] - 1000.0) < 0.01, f'Day {i} should be 1000'

        # Days 6+: should have 15 * 100 = 1500
        for i in range(6, 10):
            date_str = (base_date + timedelta(days=i)).strftime('%Y-%m-%d')
            if date_str in history_by_date:
                assert abs(history_by_date[date_str] - 1500.0) < 0.01, f'Day {i} should be 1500'

    async def test_history_decreases_after_sell(self, client: AsyncClient, test_db: AsyncSession):
        """Portfolio value should decrease when a sell transaction occurs."""
        ut = make_unit_trust()
        base_date = datetime.now(timezone.utc) - timedelta(days=10)

        # Prices at 100 throughout
        prices = [
            make_price(unit_trust_id=1, date=base_date + timedelta(days=i), price=100.0)
            for i in range(10)
        ]

        # Buy on day 2: 10 units
        txn_buy = make_transaction(
            unit_trust_id=1,
            units=10.0,
            price_per_unit=100.0,
            transaction_date=base_date + timedelta(days=2),
        )
        # Sell on day 6: 4 units
        txn_sell = make_transaction(
            unit_trust_id=1,
            units=4.0,
            price_per_unit=100.0,
            transaction_date=base_date + timedelta(days=6),
            transaction_type='sell',
        )

        test_db.add_all([ut, *prices, txn_buy, txn_sell])
        await test_db.commit()

        response = await client.get('/api/v1/portfolio/history?days=15')
        assert response.status_code == 200
        data = response.json()

        history_by_date = {h['date'][:10]: h['value'] for h in data}

        # Days 2-5: should have 10 * 100 = 1000
        for i in range(2, 6):
            date_str = (base_date + timedelta(days=i)).strftime('%Y-%m-%d')
            if date_str in history_by_date:
                assert abs(history_by_date[date_str] - 1000.0) < 0.01, f'Day {i} should be 1000'

        # Days 6+: should have 6 * 100 = 600 (10 - 4 = 6 units)
        for i in range(6, 10):
            date_str = (base_date + timedelta(days=i)).strftime('%Y-%m-%d')
            if date_str in history_by_date:
                assert abs(history_by_date[date_str] - 600.0) < 0.01, f'Day {i} should be 600'

    async def test_history_forward_fills_missing_prices(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """Missing prices should be forward-filled from last known price."""
        ut = make_unit_trust()
        base_date = datetime.now(timezone.utc) - timedelta(days=10)

        # Only create prices on days 0, 1, 2 and 7, 8, 9 (gap on days 3-6)
        prices = [
            make_price(unit_trust_id=1, date=base_date + timedelta(days=0), price=100.0),
            make_price(unit_trust_id=1, date=base_date + timedelta(days=1), price=100.0),
            make_price(unit_trust_id=1, date=base_date + timedelta(days=2), price=110.0),
            # Gap: days 3, 4, 5, 6 have no prices
            make_price(unit_trust_id=1, date=base_date + timedelta(days=7), price=120.0),
            make_price(unit_trust_id=1, date=base_date + timedelta(days=8), price=120.0),
            make_price(unit_trust_id=1, date=base_date + timedelta(days=9), price=120.0),
        ]

        # Buy on day 1
        txn = make_transaction(
            unit_trust_id=1,
            units=10.0,
            price_per_unit=100.0,
            transaction_date=base_date + timedelta(days=1),
        )

        test_db.add_all([ut, *prices, txn])
        await test_db.commit()

        response = await client.get('/api/v1/portfolio/history?days=15')
        assert response.status_code == 200
        data = response.json()

        history_by_date = {h['date'][:10]: h['value'] for h in data}

        # Days 3-6 should use forward-filled price of 110 (from day 2)
        for i in range(3, 7):
            date_str = (base_date + timedelta(days=i)).strftime('%Y-%m-%d')
            if date_str in history_by_date:
                assert abs(history_by_date[date_str] - 1100.0) < 0.01, (
                    f'Day {i} should use forward-filled price of 110'
                )

    async def test_history_multiple_funds_different_transaction_dates(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """Test equity curve with multiple funds bought at different times."""
        ut1 = make_unit_trust(name='Fund 1', symbol='FUND1')
        ut2 = make_unit_trust(name='Fund 2', symbol='FUND2')

        base_date = datetime.now(timezone.utc) - timedelta(days=10)

        # Fund 1 prices: constant 100
        prices_fund1 = [
            make_price(unit_trust_id=1, date=base_date + timedelta(days=i), price=100.0)
            for i in range(10)
        ]
        # Fund 2 prices: constant 200
        prices_fund2 = [
            make_price(unit_trust_id=2, date=base_date + timedelta(days=i), price=200.0)
            for i in range(10)
        ]

        # Buy Fund 1 on day 2: 10 units = 1000 value
        txn1 = make_transaction(
            unit_trust_id=1,
            units=10.0,
            price_per_unit=100.0,
            transaction_date=base_date + timedelta(days=2),
        )
        # Buy Fund 2 on day 5: 5 units = 1000 value
        txn2 = make_transaction(
            unit_trust_id=2,
            units=5.0,
            price_per_unit=200.0,
            transaction_date=base_date + timedelta(days=5),
        )

        test_db.add_all([ut1, ut2, *prices_fund1, *prices_fund2, txn1, txn2])
        await test_db.commit()

        response = await client.get('/api/v1/portfolio/history?days=15')
        assert response.status_code == 200
        data = response.json()

        history_by_date = {h['date'][:10]: h['value'] for h in data}

        # Days 0-1: no holdings, value = 0
        for i in range(2):
            date_str = (base_date + timedelta(days=i)).strftime('%Y-%m-%d')
            if date_str in history_by_date:
                assert history_by_date[date_str] == 0.0

        # Days 2-4: only Fund 1 (10 * 100 = 1000)
        for i in range(2, 5):
            date_str = (base_date + timedelta(days=i)).strftime('%Y-%m-%d')
            if date_str in history_by_date:
                assert abs(history_by_date[date_str] - 1000.0) < 0.01

        # Days 5+: Fund 1 + Fund 2 (1000 + 1000 = 2000)
        for i in range(5, 10):
            date_str = (base_date + timedelta(days=i)).strftime('%Y-%m-%d')
            if date_str in history_by_date:
                assert abs(history_by_date[date_str] - 2000.0) < 0.01

    async def test_history_sell_all_units_goes_to_zero(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """Portfolio value should go to zero when all units are sold."""
        ut = make_unit_trust()
        base_date = datetime.now(timezone.utc) - timedelta(days=10)

        prices = [
            make_price(unit_trust_id=1, date=base_date + timedelta(days=i), price=100.0)
            for i in range(10)
        ]

        # Buy on day 2: 10 units
        txn_buy = make_transaction(
            unit_trust_id=1,
            units=10.0,
            price_per_unit=100.0,
            transaction_date=base_date + timedelta(days=2),
        )
        # Sell all on day 6: 10 units
        txn_sell = make_transaction(
            unit_trust_id=1,
            units=10.0,
            price_per_unit=100.0,
            transaction_date=base_date + timedelta(days=6),
            transaction_type='sell',
        )

        test_db.add_all([ut, *prices, txn_buy, txn_sell])
        await test_db.commit()

        response = await client.get('/api/v1/portfolio/history?days=15')
        assert response.status_code == 200
        data = response.json()

        history_by_date = {h['date'][:10]: h['value'] for h in data}

        # Days 2-5: should have 10 * 100 = 1000
        for i in range(2, 6):
            date_str = (base_date + timedelta(days=i)).strftime('%Y-%m-%d')
            if date_str in history_by_date:
                assert abs(history_by_date[date_str] - 1000.0) < 0.01

        # Days 6+: should be 0 (all units sold)
        for i in range(6, 10):
            date_str = (base_date + timedelta(days=i)).strftime('%Y-%m-%d')
            if date_str in history_by_date:
                assert history_by_date[date_str] == 0.0

    async def test_history_multiple_transactions_same_day(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """Multiple transactions on same day should be aggregated correctly."""
        ut = make_unit_trust()
        base_date = datetime.now(timezone.utc) - timedelta(days=10)

        prices = [
            make_price(unit_trust_id=1, date=base_date + timedelta(days=i), price=100.0)
            for i in range(10)
        ]

        txn_date = base_date + timedelta(days=3)
        # Multiple buys on same day
        txn1 = make_transaction(
            unit_trust_id=1,
            units=5.0,
            price_per_unit=100.0,
            transaction_date=txn_date,
        )
        txn2 = make_transaction(
            unit_trust_id=1,
            units=3.0,
            price_per_unit=100.0,
            transaction_date=txn_date,
        )
        # And a sell on same day
        txn3 = make_transaction(
            unit_trust_id=1,
            units=2.0,
            price_per_unit=100.0,
            transaction_date=txn_date,
            transaction_type='sell',
        )

        test_db.add_all([ut, *prices, txn1, txn2, txn3])
        await test_db.commit()

        response = await client.get('/api/v1/portfolio/history?days=15')
        assert response.status_code == 200
        data = response.json()

        history_by_date = {h['date'][:10]: h['value'] for h in data}

        # Net units = 5 + 3 - 2 = 6
        # Value from day 3 onwards = 6 * 100 = 600
        for i in range(3, 10):
            date_str = (base_date + timedelta(days=i)).strftime('%Y-%m-%d')
            if date_str in history_by_date:
                assert abs(history_by_date[date_str] - 600.0) < 0.01
