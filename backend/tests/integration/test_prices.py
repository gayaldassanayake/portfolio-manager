"""Integration tests for price API endpoints."""

from datetime import datetime, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.factories import make_price, make_unit_trust


@pytest.mark.asyncio
class TestPriceAPI:
    """Test price CRUD operations."""

    async def test_create_price_success(self, client: AsyncClient, test_db: AsyncSession):
        """Test successful price creation."""
        ut = make_unit_trust(symbol='TEST')
        test_db.add(ut)
        await test_db.commit()
        await test_db.refresh(ut)

        test_date = datetime(2026, 1, 15, tzinfo=timezone.utc)
        response = await client.post(
            '/api/v1/prices',
            json={
                'unit_trust_id': ut.id,
                'date': test_date.isoformat(),
                'price': 105.50,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data['unit_trust_id'] == ut.id
        assert data['price'] == 105.50
        assert 'id' in data

    async def test_create_price_unit_trust_not_found(self, client: AsyncClient):
        """Test creating price for non-existent unit trust fails."""
        response = await client.post(
            '/api/v1/prices',
            json={
                'unit_trust_id': 999,
                'date': datetime.now(timezone.utc).isoformat(),
                'price': 100.0,
            },
        )
        assert response.status_code == 404
        assert 'Unit trust not found' in response.json()['detail']

    async def test_create_price_duplicate_date(self, client: AsyncClient, test_db: AsyncSession):
        """Test creating duplicate price for same date fails."""
        ut = make_unit_trust()
        test_date = datetime(2026, 1, 15, tzinfo=timezone.utc)
        price = make_price(unit_trust_id=1, date=test_date)
        test_db.add_all([ut, price])
        await test_db.commit()
        await test_db.refresh(ut)

        response = await client.post(
            '/api/v1/prices',
            json={
                'unit_trust_id': ut.id,
                'date': test_date.isoformat(),
                'price': 200.0,
            },
        )
        assert response.status_code == 400
        assert 'already exists' in response.json()['detail']

    async def test_list_prices_all(self, client: AsyncClient, test_db: AsyncSession):
        """Test listing all prices."""
        ut = make_unit_trust()
        price1 = make_price(unit_trust_id=1, date=datetime(2026, 1, 1, tzinfo=timezone.utc))
        price2 = make_price(unit_trust_id=1, date=datetime(2026, 1, 2, tzinfo=timezone.utc))
        test_db.add_all([ut, price1, price2])
        await test_db.commit()

        response = await client.get('/api/v1/prices')
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    async def test_list_prices_filter_unit_trust(self, client: AsyncClient, test_db: AsyncSession):
        """Test filtering prices by unit trust ID."""
        ut1 = make_unit_trust(symbol='TEST1')
        ut2 = make_unit_trust(symbol='TEST2')
        price1 = make_price(unit_trust_id=1)
        price2 = make_price(unit_trust_id=2)
        test_db.add_all([ut1, ut2, price1, price2])
        await test_db.commit()
        await test_db.refresh(ut1)

        response = await client.get(f'/api/v1/prices?unit_trust_id={ut1.id}')
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]['unit_trust_id'] == ut1.id

    async def test_list_prices_filter_date_range(self, client: AsyncClient, test_db: AsyncSession):
        """Test filtering prices by date range."""
        from urllib.parse import quote

        ut = make_unit_trust()
        price1 = make_price(unit_trust_id=1, date=datetime(2026, 1, 1, tzinfo=timezone.utc))
        price2 = make_price(unit_trust_id=1, date=datetime(2026, 1, 15, tzinfo=timezone.utc))
        price3 = make_price(unit_trust_id=1, date=datetime(2026, 2, 1, tzinfo=timezone.utc))
        test_db.add_all([ut, price1, price2, price3])
        await test_db.commit()

        start_date = quote(datetime(2026, 1, 10, tzinfo=timezone.utc).isoformat())
        end_date = quote(datetime(2026, 1, 20, tzinfo=timezone.utc).isoformat())
        response = await client.get(f'/api/v1/prices?start_date={start_date}&end_date={end_date}')
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    async def test_get_price_success(self, client: AsyncClient, test_db: AsyncSession):
        """Test getting a specific price by ID."""
        ut = make_unit_trust()
        price = make_price(unit_trust_id=1, price=123.45)
        test_db.add_all([ut, price])
        await test_db.commit()
        await test_db.refresh(price)

        response = await client.get(f'/api/v1/prices/{price.id}')
        assert response.status_code == 200
        data = response.json()
        assert data['id'] == price.id
        assert data['price'] == 123.45

    async def test_get_price_not_found(self, client: AsyncClient):
        """Test getting non-existent price returns 404."""
        response = await client.get('/api/v1/prices/999')
        assert response.status_code == 404

    async def test_update_price_success(self, client: AsyncClient, test_db: AsyncSession):
        """Test updating a price."""
        ut = make_unit_trust()
        price = make_price(unit_trust_id=1, price=100.0)
        test_db.add_all([ut, price])
        await test_db.commit()
        await test_db.refresh(price)

        response = await client.put(f'/api/v1/prices/{price.id}', json={'price': 150.0})
        assert response.status_code == 200
        data = response.json()
        assert data['price'] == 150.0

    async def test_delete_price_success(self, client: AsyncClient, test_db: AsyncSession):
        """Test deleting a price."""
        ut = make_unit_trust()
        price = make_price(unit_trust_id=1)
        test_db.add_all([ut, price])
        await test_db.commit()
        await test_db.refresh(price)

        response = await client.delete(f'/api/v1/prices/{price.id}')
        assert response.status_code == 204

    async def test_bulk_create_prices_success(self, client: AsyncClient, test_db: AsyncSession):
        """Test bulk creating multiple prices."""
        ut = make_unit_trust()
        test_db.add(ut)
        await test_db.commit()
        await test_db.refresh(ut)

        prices_data = [
            {
                'unit_trust_id': ut.id,
                'date': datetime(2026, 1, i, tzinfo=timezone.utc).isoformat(),
                'price': 100.0 + i,
            }
            for i in range(1, 6)
        ]

        response = await client.post('/api/v1/prices/bulk', json=prices_data)
        assert response.status_code == 201
        data = response.json()
        assert data['created'] == 5

    async def test_bulk_create_prices_skips_duplicates(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """Test bulk create skips existing dates."""
        ut = make_unit_trust()
        existing_price = make_price(unit_trust_id=1, date=datetime(2026, 1, 1, tzinfo=timezone.utc))
        test_db.add_all([ut, existing_price])
        await test_db.commit()
        await test_db.refresh(ut)

        prices_data = [
            {
                'unit_trust_id': ut.id,
                'date': datetime(2026, 1, 1, tzinfo=timezone.utc).isoformat(),
                'price': 100.0,
            },
            {
                'unit_trust_id': ut.id,
                'date': datetime(2026, 1, 2, tzinfo=timezone.utc).isoformat(),
                'price': 101.0,
            },
        ]

        response = await client.post('/api/v1/prices/bulk', json=prices_data)
        assert response.status_code == 201
        data = response.json()
        assert data['created'] == 1  # Only new one created

    async def test_bulk_create_prices_invalid_unit_trust(self, client: AsyncClient):
        """Test bulk create with invalid unit trust ID fails."""
        prices_data = [
            {
                'unit_trust_id': 999,
                'date': datetime.now(timezone.utc).isoformat(),
                'price': 100.0,
            }
        ]

        response = await client.post('/api/v1/prices/bulk', json=prices_data)
        assert response.status_code == 404
        assert '999' in response.json()['detail']
