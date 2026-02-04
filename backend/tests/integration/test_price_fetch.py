"""Integration tests for price fetch API endpoints."""

from datetime import datetime, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.factories import make_price, make_unit_trust


@pytest.mark.asyncio
class TestPriceFetchSingle:
    """Test single unit trust price fetch endpoint."""

    async def test_fetch_prices_success(self, client: AsyncClient, test_db: AsyncSession):
        """Test successful price fetch using CAL provider."""
        ut = make_unit_trust(symbol='CALFUND', provider='cal')
        test_db.add(ut)
        await test_db.commit()
        await test_db.refresh(ut)

        response = await client.post(
            f'/api/v1/prices/fetch/{ut.id}',
            params={'start_date': '2026-01-15', 'end_date': '2026-01-17'},
        )

        assert response.status_code == 200
        data = response.json()
        assert data['unit_trust_id'] == ut.id
        assert data['symbol'] == 'CALFUND'
        assert data['provider'] == 'cal'
        assert data['prices_fetched'] == 3
        assert data['prices_saved'] == 3
        assert len(data['prices']) == 3

    async def test_fetch_prices_unit_trust_not_found(self, client: AsyncClient):
        """Test fetch for non-existent unit trust returns 404."""
        response = await client.post('/api/v1/prices/fetch/999')

        assert response.status_code == 404
        assert 'Unit trust not found' in response.json()['detail']

    async def test_fetch_prices_no_provider_configured(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """Test fetch without provider configured returns 400."""
        ut = make_unit_trust(symbol='NOPROV', provider=None)
        test_db.add(ut)
        await test_db.commit()
        await test_db.refresh(ut)

        response = await client.post(f'/api/v1/prices/fetch/{ut.id}')

        assert response.status_code == 400
        assert 'No provider configured' in response.json()['detail']
        assert 'yahoo' in response.json()['detail']  # Shows available providers

    async def test_fetch_prices_skips_existing_dates(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """Test fetch skips dates that already have prices."""
        ut = make_unit_trust(symbol='EXISTING', provider='cal')
        # Pre-create a price for Jan 16
        existing_price = make_price(
            unit_trust_id=1,
            date=datetime(2026, 1, 16, tzinfo=timezone.utc),
            price=5.0,
        )
        test_db.add_all([ut, existing_price])
        await test_db.commit()
        await test_db.refresh(ut)

        response = await client.post(
            f'/api/v1/prices/fetch/{ut.id}',
            params={'start_date': '2026-01-15', 'end_date': '2026-01-17'},
        )

        assert response.status_code == 200
        data = response.json()
        assert data['prices_fetched'] == 3  # Provider returned 3
        assert data['prices_saved'] == 2  # Only 2 new ones saved (Jan 15, 17)

    async def test_fetch_prices_with_date_range(self, client: AsyncClient, test_db: AsyncSession):
        """Test fetch with custom date range."""
        ut = make_unit_trust(symbol='DATETEST', provider='cal')
        test_db.add(ut)
        await test_db.commit()
        await test_db.refresh(ut)

        response = await client.post(
            f'/api/v1/prices/fetch/{ut.id}',
            params={'start_date': '2026-01-01', 'end_date': '2026-01-10'},
        )

        assert response.status_code == 200
        data = response.json()
        assert data['prices_fetched'] == 10
        assert data['prices_saved'] == 10

    async def test_fetch_prices_with_provider_symbol(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """Test fetch uses provider_symbol when set."""
        ut = make_unit_trust(
            symbol='INTERNAL',
            provider='cal',
            provider_symbol='EXTERNAL_SYMBOL',
        )
        test_db.add(ut)
        await test_db.commit()
        await test_db.refresh(ut)

        response = await client.post(
            f'/api/v1/prices/fetch/{ut.id}',
            params={'start_date': '2026-01-15', 'end_date': '2026-01-15'},
        )

        assert response.status_code == 200
        data = response.json()
        # Should succeed (CAL provider ignores symbol anyway)
        assert data['prices_saved'] == 1

    async def test_fetch_prices_defaults_to_today(self, client: AsyncClient, test_db: AsyncSession):
        """Test fetch defaults to today when no dates provided."""
        ut = make_unit_trust(symbol='TODAY', provider='cal')
        test_db.add(ut)
        await test_db.commit()
        await test_db.refresh(ut)

        response = await client.post(f'/api/v1/prices/fetch/{ut.id}')

        assert response.status_code == 200
        data = response.json()
        assert data['prices_fetched'] == 1
        assert data['prices_saved'] == 1

    async def test_fetch_prices_saves_to_database(self, client: AsyncClient, test_db: AsyncSession):
        """Test fetched prices are actually saved to the database."""
        ut = make_unit_trust(symbol='DBTEST', provider='cal')
        test_db.add(ut)
        await test_db.commit()
        await test_db.refresh(ut)

        # Fetch prices
        await client.post(
            f'/api/v1/prices/fetch/{ut.id}',
            params={'start_date': '2026-01-15', 'end_date': '2026-01-17'},
        )

        # Verify prices exist via list endpoint
        response = await client.get(f'/api/v1/prices?unit_trust_id={ut.id}')
        assert response.status_code == 200
        prices = response.json()
        assert len(prices) == 3


@pytest.mark.asyncio
class TestPriceFetchBulk:
    """Test bulk price fetch endpoint."""

    async def test_bulk_fetch_all_trusts(self, client: AsyncClient, test_db: AsyncSession):
        """Test bulk fetch for all unit trusts."""
        ut1 = make_unit_trust(symbol='BULK1', provider='cal')
        ut2 = make_unit_trust(symbol='BULK2', provider='cal')
        test_db.add_all([ut1, ut2])
        await test_db.commit()

        response = await client.post(
            '/api/v1/prices/fetch',
            params={'start_date': '2026-01-15', 'end_date': '2026-01-15'},
        )

        assert response.status_code == 200
        data = response.json()
        assert data['total_requested'] == 2
        assert data['successful'] == 2
        assert data['failed'] == 0
        assert len(data['results']) == 2
        assert len(data['errors']) == 0

    async def test_bulk_fetch_filtered_ids(self, client: AsyncClient, test_db: AsyncSession):
        """Test bulk fetch for specific unit trust IDs only."""
        ut1 = make_unit_trust(symbol='FILTER1', provider='cal')
        ut2 = make_unit_trust(symbol='FILTER2', provider='cal')
        ut3 = make_unit_trust(symbol='FILTER3', provider='cal')
        test_db.add_all([ut1, ut2, ut3])
        await test_db.commit()
        await test_db.refresh(ut1)
        await test_db.refresh(ut2)

        response = await client.post(
            '/api/v1/prices/fetch',
            params={
                'unit_trust_ids': [ut1.id, ut2.id],
                'start_date': '2026-01-15',
                'end_date': '2026-01-15',
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data['total_requested'] == 2  # Only 2 requested, not 3
        assert data['successful'] == 2

    async def test_bulk_fetch_partial_success(self, client: AsyncClient, test_db: AsyncSession):
        """Test bulk fetch with some failures (no provider configured)."""
        ut1 = make_unit_trust(symbol='SUCCESS', provider='cal')
        ut2 = make_unit_trust(symbol='FAIL', provider=None)  # No provider
        test_db.add_all([ut1, ut2])
        await test_db.commit()

        response = await client.post(
            '/api/v1/prices/fetch',
            params={'start_date': '2026-01-15', 'end_date': '2026-01-15'},
        )

        assert response.status_code == 200
        data = response.json()
        assert data['total_requested'] == 2
        assert data['successful'] == 1
        assert data['failed'] == 1
        assert len(data['results']) == 1
        assert len(data['errors']) == 1
        assert data['errors'][0]['symbol'] == 'FAIL'
        assert 'No provider configured' in data['errors'][0]['error']

    async def test_bulk_fetch_empty_database(self, client: AsyncClient):
        """Test bulk fetch when no unit trusts exist."""
        response = await client.post(
            '/api/v1/prices/fetch',
            params={'start_date': '2026-01-15', 'end_date': '2026-01-15'},
        )

        assert response.status_code == 200
        data = response.json()
        assert data['total_requested'] == 0
        assert data['successful'] == 0
        assert data['failed'] == 0

    async def test_bulk_fetch_response_structure(self, client: AsyncClient, test_db: AsyncSession):
        """Test bulk fetch response has correct structure."""
        ut = make_unit_trust(symbol='STRUCT', provider='cal')
        test_db.add(ut)
        await test_db.commit()
        await test_db.refresh(ut)

        response = await client.post(
            '/api/v1/prices/fetch',
            params={'start_date': '2026-01-15', 'end_date': '2026-01-15'},
        )

        assert response.status_code == 200
        data = response.json()

        # Check top-level structure
        assert 'total_requested' in data
        assert 'successful' in data
        assert 'failed' in data
        assert 'results' in data
        assert 'errors' in data

        # Check result structure
        result = data['results'][0]
        assert 'unit_trust_id' in result
        assert 'symbol' in result
        assert 'provider' in result
        assert 'prices_fetched' in result
        assert 'prices_saved' in result
        assert 'prices' in result

    async def test_bulk_fetch_unknown_provider_error(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """Test bulk fetch handles unknown provider gracefully."""
        # Manually set an invalid provider (bypassing schema validation)
        ut = make_unit_trust(symbol='BADPROV')
        ut.provider = 'nonexistent'  # Set invalid provider directly
        test_db.add(ut)
        await test_db.commit()

        response = await client.post(
            '/api/v1/prices/fetch',
            params={'start_date': '2026-01-15', 'end_date': '2026-01-15'},
        )

        assert response.status_code == 200
        data = response.json()
        assert data['failed'] == 1
        assert 'Unknown provider' in data['errors'][0]['error']
