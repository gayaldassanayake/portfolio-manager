"""Integration tests for fixed deposit API endpoints."""

from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.factories import make_fixed_deposit


@pytest.mark.asyncio
class TestFixedDepositAPI:
    """Test fixed deposit CRUD operations."""

    async def test_create_fixed_deposit_success(self, client: AsyncClient):
        """Test successful fixed deposit creation."""
        start_date = datetime.now(timezone.utc)
        maturity_date = start_date + timedelta(days=365)

        response = await client.post(
            '/api/v1/fixed-deposits',
            json={
                'principal_amount': 10000.0,
                'interest_rate': 8.5,
                'start_date': start_date.isoformat(),
                'maturity_date': maturity_date.isoformat(),
                'institution_name': 'ABC Bank',
                'account_number': 'FD-001',
                'interest_payout_frequency': 'at_maturity',
                'interest_calculation_type': 'simple',
                'auto_renewal': False,
                'notes': 'Test FD',
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data['principal_amount'] == 10000.0
        assert data['interest_rate'] == 8.5
        assert data['institution_name'] == 'ABC Bank'
        assert data['account_number'] == 'FD-001'
        assert 'id' in data
        assert 'created_at' in data

    async def test_create_fixed_deposit_validation_error(self, client: AsyncClient):
        """Test creating fixed deposit with maturity before start fails."""
        start_date = datetime.now(timezone.utc)
        maturity_date = start_date - timedelta(days=1)  # Before start

        response = await client.post(
            '/api/v1/fixed-deposits',
            json={
                'principal_amount': 10000.0,
                'interest_rate': 8.5,
                'start_date': start_date.isoformat(),
                'maturity_date': maturity_date.isoformat(),
                'institution_name': 'ABC Bank',
                'account_number': 'FD-001',
                'interest_payout_frequency': 'at_maturity',
                'interest_calculation_type': 'simple',
                'auto_renewal': False,
            },
        )
        assert response.status_code == 422
        assert 'after start date' in response.json()['detail'][0]['msg'].lower()

    async def test_list_fixed_deposits_empty(self, client: AsyncClient):
        """Test listing fixed deposits when none exist."""
        response = await client.get('/api/v1/fixed-deposits')
        assert response.status_code == 200
        assert response.json() == []

    async def test_list_fixed_deposits_multiple(self, client: AsyncClient, test_db: AsyncSession):
        """Test listing multiple fixed deposits with calculated values."""
        fd1 = make_fixed_deposit(
            institution_name='Bank A', account_number='FD-001', interest_rate=8.0
        )
        fd2 = make_fixed_deposit(
            institution_name='Bank B', account_number='FD-002', interest_rate=9.5
        )
        test_db.add_all([fd1, fd2])
        await test_db.commit()

        response = await client.get('/api/v1/fixed-deposits')
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

        # Check that calculated fields are present
        for fd in data:
            assert 'current_value' in fd
            assert 'accrued_interest' in fd
            assert 'days_to_maturity' in fd
            assert 'is_matured' in fd
            assert 'term_days' in fd

    async def test_list_fixed_deposits_filter_active(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """Test filtering fixed deposits by active status."""
        # Create active FD
        active_fd = make_fixed_deposit(
            institution_name='Bank A',
            start_date=datetime.now(timezone.utc),
            maturity_date=datetime.now(timezone.utc) + timedelta(days=365),
        )

        # Create matured FD
        matured_fd = make_fixed_deposit(
            institution_name='Bank B',
            start_date=datetime.now(timezone.utc) - timedelta(days=365),
            maturity_date=datetime.now(timezone.utc) - timedelta(days=1),
        )

        test_db.add_all([active_fd, matured_fd])
        await test_db.commit()

        response = await client.get('/api/v1/fixed-deposits?status=active')
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]['institution_name'] == 'Bank A'
        assert not data[0]['is_matured']

    async def test_list_fixed_deposits_filter_matured(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """Test filtering fixed deposits by matured status."""
        # Create active FD
        active_fd = make_fixed_deposit(
            institution_name='Bank A',
            start_date=datetime.now(timezone.utc),
            maturity_date=datetime.now(timezone.utc) + timedelta(days=365),
        )

        # Create matured FD
        matured_fd = make_fixed_deposit(
            institution_name='Bank B',
            start_date=datetime.now(timezone.utc) - timedelta(days=365),
            maturity_date=datetime.now(timezone.utc) - timedelta(days=1),
        )

        test_db.add_all([active_fd, matured_fd])
        await test_db.commit()

        response = await client.get('/api/v1/fixed-deposits?status=matured')
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]['institution_name'] == 'Bank B'
        assert data[0]['is_matured']

    async def test_get_fixed_deposit_success(self, client: AsyncClient, test_db: AsyncSession):
        """Test getting a specific fixed deposit by ID."""
        fd = make_fixed_deposit(
            principal_amount=15000.0, interest_rate=7.5, institution_name='Test Bank'
        )
        test_db.add(fd)
        await test_db.commit()
        await test_db.refresh(fd)

        response = await client.get(f'/api/v1/fixed-deposits/{fd.id}')
        assert response.status_code == 200
        data = response.json()
        assert data['id'] == fd.id
        assert data['principal_amount'] == 15000.0
        assert data['interest_rate'] == 7.5
        assert data['institution_name'] == 'Test Bank'
        # Check calculated fields
        assert 'current_value' in data
        assert data['current_value'] >= 15000.0  # Should include accrued interest

    async def test_get_fixed_deposit_not_found(self, client: AsyncClient):
        """Test getting non-existent fixed deposit returns 404."""
        response = await client.get('/api/v1/fixed-deposits/999')
        assert response.status_code == 404
        assert 'not found' in response.json()['detail'].lower()

    async def test_update_fixed_deposit_success(self, client: AsyncClient, test_db: AsyncSession):
        """Test updating a fixed deposit."""
        fd = make_fixed_deposit(principal_amount=10000.0, interest_rate=8.0)
        test_db.add(fd)
        await test_db.commit()
        await test_db.refresh(fd)

        response = await client.put(
            f'/api/v1/fixed-deposits/{fd.id}',
            json={'principal_amount': 12000.0, 'interest_rate': 9.0, 'notes': 'Updated'},
        )
        assert response.status_code == 200
        data = response.json()
        assert data['principal_amount'] == 12000.0
        assert data['interest_rate'] == 9.0
        assert data['notes'] == 'Updated'

    async def test_update_fixed_deposit_validation_error(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """Test updating fixed deposit with invalid dates fails."""
        fd = make_fixed_deposit()
        test_db.add(fd)
        await test_db.commit()
        await test_db.refresh(fd)

        # Try to set maturity before start
        start_date = datetime.now(timezone.utc)
        maturity_date = start_date - timedelta(days=1)

        response = await client.put(
            f'/api/v1/fixed-deposits/{fd.id}',
            json={
                'start_date': start_date.isoformat(),
                'maturity_date': maturity_date.isoformat(),
            },
        )
        assert response.status_code == 400
        assert 'after start date' in response.json()['detail'].lower()

    async def test_delete_fixed_deposit_success(self, client: AsyncClient, test_db: AsyncSession):
        """Test deleting a fixed deposit."""
        fd = make_fixed_deposit()
        test_db.add(fd)
        await test_db.commit()
        await test_db.refresh(fd)

        response = await client.delete(f'/api/v1/fixed-deposits/{fd.id}')
        assert response.status_code == 204

        # Verify deletion
        response = await client.get(f'/api/v1/fixed-deposits/{fd.id}')
        assert response.status_code == 404

    async def test_delete_fixed_deposit_not_found(self, client: AsyncClient):
        """Test deleting non-existent fixed deposit returns 404."""
        response = await client.delete('/api/v1/fixed-deposits/999')
        assert response.status_code == 404

    async def test_calculate_interest_simple(self, client: AsyncClient):
        """Test interest calculation utility endpoint with simple interest."""
        start_date = datetime.now(timezone.utc)
        maturity_date = start_date + timedelta(days=365)

        response = await client.post(
            '/api/v1/fixed-deposits/calculate-interest',
            json={
                'principal': 10000.0,
                'annual_rate': 8.0,
                'start_date': start_date.isoformat(),
                'maturity_date': maturity_date.isoformat(),
                'calculation_type': 'simple',
                'payout_frequency': 'at_maturity',
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data['total_interest'] == 800.0  # 10000 * 0.08 * 1 = 800
        assert data['maturity_value'] == 10800.0
        assert data['term_days'] == 365
        assert 'current_interest' in data
        assert 'days_remaining' in data

    async def test_calculate_interest_compound(self, client: AsyncClient):
        """Test interest calculation utility endpoint with compound interest."""
        start_date = datetime.now(timezone.utc)
        maturity_date = start_date + timedelta(days=365)

        response = await client.post(
            '/api/v1/fixed-deposits/calculate-interest',
            json={
                'principal': 10000.0,
                'annual_rate': 8.0,
                'start_date': start_date.isoformat(),
                'maturity_date': maturity_date.isoformat(),
                'calculation_type': 'compound',
                'payout_frequency': 'monthly',
            },
        )
        assert response.status_code == 200
        data = response.json()
        # Compound interest should be more than simple
        assert data['total_interest'] > 800.0
        assert data['maturity_value'] > 10800.0
