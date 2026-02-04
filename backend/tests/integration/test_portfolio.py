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
        # Net units = 10 - 3 = 7
        assert data['total_units'] == 7
        # Current value = 7 * 120 = 840
        assert data['current_value'] == 840.0
        # Gain/loss = 840 - 1000 = -160
        assert data['total_gain_loss'] == -160.0
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
        assert 'annualized_return' in metrics
        assert 'max_drawdown' in metrics

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

        txn = make_transaction(unit_trust_id=1, units=10.0, price_per_unit=100.0)
        test_db.add_all([ut, *prices, txn])
        await test_db.commit()

        response = await client.get('/api/v1/portfolio/metrics?days=30')
        assert response.status_code == 200
        data = response.json()

        assert data['volatility'] >= 0
        assert data['daily_return'] is not None
        assert data['annualized_return'] is not None
        assert data['max_drawdown'] <= 0  # Drawdown is negative or zero
