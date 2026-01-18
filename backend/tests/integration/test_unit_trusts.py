"""Integration tests for unit trust API endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.factories import make_unit_trust


@pytest.mark.asyncio
class TestUnitTrustAPI:
    """Test unit trust CRUD operations."""

    async def test_create_unit_trust_success(self, client: AsyncClient):
        """Test successful unit trust creation."""
        response = await client.post(
            '/api/v1/unit-trusts',
            json={'name': 'Vanguard 500', 'symbol': 'VFIAX', 'description': 'S&P 500 Index'},
        )
        assert response.status_code == 201
        data = response.json()
        assert data['name'] == 'Vanguard 500'
        assert data['symbol'] == 'VFIAX'
        assert data['description'] == 'S&P 500 Index'
        assert 'id' in data
        assert 'created_at' in data

    async def test_create_unit_trust_duplicate_symbol(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """Test creating unit trust with duplicate symbol fails."""
        # Create first unit trust
        ut = make_unit_trust(symbol='DUP')
        test_db.add(ut)
        await test_db.commit()

        # Try to create duplicate
        response = await client.post(
            '/api/v1/unit-trusts',
            json={'name': 'Another Fund', 'symbol': 'DUP', 'description': 'Test'},
        )
        assert response.status_code == 400
        assert 'already exists' in response.json()['detail']

    async def test_create_unit_trust_missing_fields(self, client: AsyncClient):
        """Test creating unit trust with missing required fields fails."""
        response = await client.post('/api/v1/unit-trusts', json={'name': 'Test'})
        assert response.status_code == 422

    async def test_list_unit_trusts_empty(self, client: AsyncClient):
        """Test listing unit trusts when none exist."""
        response = await client.get('/api/v1/unit-trusts')
        assert response.status_code == 200
        assert response.json() == []

    async def test_list_unit_trusts_multiple(self, client: AsyncClient, test_db: AsyncSession):
        """Test listing multiple unit trusts."""
        ut1 = make_unit_trust(name='Fund A', symbol='FUNDA')
        ut2 = make_unit_trust(name='Fund B', symbol='FUNDB')
        test_db.add_all([ut1, ut2])
        await test_db.commit()

        response = await client.get('/api/v1/unit-trusts')
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert {ut['symbol'] for ut in data} == {'FUNDA', 'FUNDB'}

    async def test_get_unit_trust_success(self, client: AsyncClient, test_db: AsyncSession):
        """Test getting a specific unit trust by ID."""
        ut = make_unit_trust(name='Test Fund', symbol='TEST')
        test_db.add(ut)
        await test_db.commit()
        await test_db.refresh(ut)

        response = await client.get(f'/api/v1/unit-trusts/{ut.id}')
        assert response.status_code == 200
        data = response.json()
        assert data['id'] == ut.id
        assert data['name'] == 'Test Fund'
        assert data['symbol'] == 'TEST'

    async def test_get_unit_trust_not_found(self, client: AsyncClient):
        """Test getting non-existent unit trust returns 404."""
        response = await client.get('/api/v1/unit-trusts/999')
        assert response.status_code == 404
        assert 'not found' in response.json()['detail']

    async def test_update_unit_trust_success(self, client: AsyncClient, test_db: AsyncSession):
        """Test updating a unit trust."""
        ut = make_unit_trust(name='Old Name', symbol='OLD')
        test_db.add(ut)
        await test_db.commit()
        await test_db.refresh(ut)

        response = await client.put(
            f'/api/v1/unit-trusts/{ut.id}',
            json={'name': 'New Name', 'description': 'Updated description'},
        )
        assert response.status_code == 200
        data = response.json()
        assert data['name'] == 'New Name'
        assert data['symbol'] == 'OLD'  # Symbol unchanged
        assert data['description'] == 'Updated description'

    async def test_update_unit_trust_not_found(self, client: AsyncClient):
        """Test updating non-existent unit trust returns 404."""
        response = await client.put('/api/v1/unit-trusts/999', json={'name': 'New Name'})
        assert response.status_code == 404

    async def test_delete_unit_trust_success(self, client: AsyncClient, test_db: AsyncSession):
        """Test deleting a unit trust."""
        ut = make_unit_trust()
        test_db.add(ut)
        await test_db.commit()
        await test_db.refresh(ut)

        response = await client.delete(f'/api/v1/unit-trusts/{ut.id}')
        assert response.status_code == 204

        # Verify it's deleted
        response = await client.get(f'/api/v1/unit-trusts/{ut.id}')
        assert response.status_code == 404

    async def test_delete_unit_trust_not_found(self, client: AsyncClient):
        """Test deleting non-existent unit trust returns 404."""
        response = await client.delete('/api/v1/unit-trusts/999')
        assert response.status_code == 404

    async def test_get_unit_trust_with_stats_no_transactions(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """Test getting unit trust stats with no transactions."""
        ut = make_unit_trust()
        test_db.add(ut)
        await test_db.commit()
        await test_db.refresh(ut)

        response = await client.get(f'/api/v1/unit-trusts/{ut.id}/with-stats')
        assert response.status_code == 200
        data = response.json()
        assert data['total_units'] == 0.0
        assert data['avg_purchase_price'] == 0.0
        assert data['latest_price'] is None

    async def test_get_unit_trust_with_stats_not_found(self, client: AsyncClient):
        """Test getting stats for non-existent unit trust returns 404."""
        response = await client.get('/api/v1/unit-trusts/999/with-stats')
        assert response.status_code == 404
