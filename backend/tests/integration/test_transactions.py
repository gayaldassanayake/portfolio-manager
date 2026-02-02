"""Integration tests for transaction API endpoints."""

from datetime import datetime, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.factories import make_price, make_transaction, make_unit_trust


@pytest.mark.asyncio
class TestTransactionAPI:
    """Test transaction CRUD operations."""

    async def test_create_transaction_success(self, client: AsyncClient, test_db: AsyncSession):
        """Test successful transaction creation with auto price lookup."""
        ut = make_unit_trust(symbol='TEST')
        test_date = datetime(2026, 1, 15, tzinfo=timezone.utc)
        price = make_price(unit_trust_id=1, date=test_date, price=100.0)
        test_db.add_all([ut, price])
        await test_db.commit()
        await test_db.refresh(ut)

        response = await client.post(
            '/api/v1/transactions',
            json={
                'unit_trust_id': ut.id,
                'units': 10.5,
                'transaction_date': test_date.isoformat(),
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data['units'] == 10.5
        assert data['price_per_unit'] == 100.0  # Auto-filled from price
        assert data['unit_trust_id'] == ut.id
        assert data['transaction_type'] == 'buy'  # Default

    async def test_create_transaction_with_type_and_notes(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """Test creating transaction with transaction_type and notes."""
        ut = make_unit_trust(symbol='TEST')
        test_date = datetime(2026, 1, 15, tzinfo=timezone.utc)
        price = make_price(unit_trust_id=1, date=test_date, price=100.0)
        test_db.add_all([ut, price])
        await test_db.commit()
        await test_db.refresh(ut)

        response = await client.post(
            '/api/v1/transactions',
            json={
                'unit_trust_id': ut.id,
                'units': 5.0,
                'transaction_date': test_date.isoformat(),
                'transaction_type': 'sell',
                'notes': 'Profit taking',
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data['units'] == 5.0
        assert data['transaction_type'] == 'sell'
        assert data['notes'] == 'Profit taking'

    async def test_create_transaction_unit_trust_not_found(self, client: AsyncClient):
        """Test creating transaction for non-existent unit trust fails."""
        response = await client.post(
            '/api/v1/transactions',
            json={
                'unit_trust_id': 999,
                'units': 10.0,
                'transaction_date': datetime.now(timezone.utc).isoformat(),
            },
        )
        assert response.status_code == 404
        assert 'Unit trust not found' in response.json()['detail']

    async def test_create_transaction_no_price_for_date(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """Test creating transaction without price for date fails."""
        ut = make_unit_trust()
        test_db.add(ut)
        await test_db.commit()
        await test_db.refresh(ut)

        response = await client.post(
            '/api/v1/transactions',
            json={
                'unit_trust_id': ut.id,
                'units': 10.0,
                'transaction_date': datetime(2026, 1, 15, tzinfo=timezone.utc).isoformat(),
            },
        )
        assert response.status_code == 400
        assert 'Price not available' in response.json()['detail']

    async def test_list_transactions_all(self, client: AsyncClient, test_db: AsyncSession):
        """Test listing all transactions."""
        ut = make_unit_trust()
        txn1 = make_transaction(unit_trust_id=1, units=5.0)
        txn2 = make_transaction(unit_trust_id=1, units=10.0)
        test_db.add_all([ut, txn1, txn2])
        await test_db.commit()

        response = await client.get('/api/v1/transactions')
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        # Check unit trust details are included
        assert all('unit_trust_name' in t for t in data)
        assert all('unit_trust_symbol' in t for t in data)

    async def test_list_transactions_filter_unit_trust(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """Test filtering transactions by unit trust ID."""
        ut1 = make_unit_trust(symbol='TEST1')
        ut2 = make_unit_trust(symbol='TEST2')
        txn1 = make_transaction(unit_trust_id=1)
        txn2 = make_transaction(unit_trust_id=2)
        test_db.add_all([ut1, ut2, txn1, txn2])
        await test_db.commit()
        await test_db.refresh(ut1)

        response = await client.get(f'/api/v1/transactions?unit_trust_id={ut1.id}')
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]['unit_trust_id'] == ut1.id

    async def test_list_transactions_filter_by_type(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """Test filtering transactions by transaction_type."""
        ut = make_unit_trust()
        txn_buy = make_transaction(unit_trust_id=1, transaction_type='buy')
        txn_sell = make_transaction(unit_trust_id=1, transaction_type='sell')
        test_db.add_all([ut, txn_buy, txn_sell])
        await test_db.commit()

        # Filter by buy
        response = await client.get('/api/v1/transactions?transaction_type=buy')
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]['transaction_type'] == 'buy'

        # Filter by sell
        response = await client.get('/api/v1/transactions?transaction_type=sell')
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]['transaction_type'] == 'sell'

    async def test_list_transactions_filter_date_range(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """Test filtering transactions by date range."""
        from urllib.parse import quote

        ut = make_unit_trust()
        txn1 = make_transaction(
            unit_trust_id=1, transaction_date=datetime(2026, 1, 1, tzinfo=timezone.utc)
        )
        txn2 = make_transaction(
            unit_trust_id=1, transaction_date=datetime(2026, 1, 15, tzinfo=timezone.utc)
        )
        txn3 = make_transaction(
            unit_trust_id=1, transaction_date=datetime(2026, 2, 1, tzinfo=timezone.utc)
        )
        test_db.add_all([ut, txn1, txn2, txn3])
        await test_db.commit()

        start_date = quote(datetime(2026, 1, 10, tzinfo=timezone.utc).isoformat())
        end_date = quote(datetime(2026, 1, 20, tzinfo=timezone.utc).isoformat())
        response = await client.get(
            f'/api/v1/transactions?start_date={start_date}&end_date={end_date}'
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    async def test_get_transaction_success(self, client: AsyncClient, test_db: AsyncSession):
        """Test getting a specific transaction by ID."""
        ut = make_unit_trust(name='Test Fund', symbol='TEST')
        txn = make_transaction(unit_trust_id=1, units=15.0)
        test_db.add_all([ut, txn])
        await test_db.commit()
        await test_db.refresh(txn)

        response = await client.get(f'/api/v1/transactions/{txn.id}')
        assert response.status_code == 200
        data = response.json()
        assert data['id'] == txn.id
        assert data['units'] == 15.0
        assert data['unit_trust_name'] == 'Test Fund'
        assert data['unit_trust_symbol'] == 'TEST'

    async def test_get_transaction_not_found(self, client: AsyncClient):
        """Test getting non-existent transaction returns 404."""
        response = await client.get('/api/v1/transactions/999')
        assert response.status_code == 404

    async def test_update_transaction_success(self, client: AsyncClient, test_db: AsyncSession):
        """Test updating a transaction."""
        ut = make_unit_trust()
        txn = make_transaction(unit_trust_id=1, units=10.0, price_per_unit=100.0)
        test_db.add_all([ut, txn])
        await test_db.commit()
        await test_db.refresh(txn)

        response = await client.put(
            f'/api/v1/transactions/{txn.id}', json={'units': 20.0, 'price_per_unit': 105.0}
        )
        assert response.status_code == 200
        data = response.json()
        assert data['units'] == 20.0
        assert data['price_per_unit'] == 105.0

    async def test_delete_transaction_success(self, client: AsyncClient, test_db: AsyncSession):
        """Test deleting a transaction."""
        ut = make_unit_trust()
        txn = make_transaction(unit_trust_id=1)
        test_db.add_all([ut, txn])
        await test_db.commit()
        await test_db.refresh(txn)

        response = await client.delete(f'/api/v1/transactions/{txn.id}')
        assert response.status_code == 204

        # Verify it's deleted
        response = await client.get(f'/api/v1/transactions/{txn.id}')
        assert response.status_code == 404
