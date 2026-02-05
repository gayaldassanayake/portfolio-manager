"""Integration tests for notification API endpoints."""

from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.factories import make_fixed_deposit, make_notification_log, make_notification_setting


@pytest.mark.asyncio
class TestNotificationSettingsAPI:
    """Test notification settings CRUD operations."""

    async def test_get_settings_creates_default(self, client: AsyncClient):
        """Test getting settings creates default settings if none exist."""
        response = await client.get('/api/v1/notifications/settings')
        assert response.status_code == 200
        data = response.json()
        assert data['notify_days_before_30'] is True
        assert data['notify_days_before_7'] is True
        assert data['notify_on_maturity'] is True
        assert data['email_notifications_enabled'] is False
        assert 'id' in data

    async def test_update_settings_success(self, client: AsyncClient, test_db: AsyncSession):
        """Test updating notification settings."""
        # Create initial settings
        settings = make_notification_setting()
        test_db.add(settings)
        await test_db.commit()

        response = await client.put(
            '/api/v1/notifications/settings',
            json={
                'notify_days_before_30': False,
                'notify_days_before_7': True,
                'notify_on_maturity': False,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data['notify_days_before_30'] is False
        assert data['notify_days_before_7'] is True
        assert data['notify_on_maturity'] is False

    async def test_update_settings_creates_if_not_exists(self, client: AsyncClient):
        """Test updating settings creates them if they don't exist."""
        response = await client.put(
            '/api/v1/notifications/settings',
            json={'notify_days_before_30': False},
        )
        assert response.status_code == 200
        data = response.json()
        assert data['notify_days_before_30'] is False


@pytest.mark.asyncio
class TestNotificationGenerationAPI:
    """Test notification generation logic."""

    async def test_generate_notifications_30_days(self, client: AsyncClient, test_db: AsyncSession):
        """Test generating notifications for FDs maturing in 30 days."""
        # Create FD maturing in 30 days
        start_date = datetime.now(timezone.utc) - timedelta(days=335)
        maturity_date = datetime.now(timezone.utc) + timedelta(days=30)
        fd = make_fixed_deposit(start_date=start_date, maturity_date=maturity_date)
        test_db.add(fd)

        # Create settings
        settings = make_notification_setting()
        test_db.add(settings)
        await test_db.commit()

        response = await client.post('/api/v1/notifications/generate')
        assert response.status_code == 200
        data = response.json()
        assert data['notifications_created'] == 1
        assert 'generated' in data['message'].lower()

    async def test_generate_notifications_7_days(self, client: AsyncClient, test_db: AsyncSession):
        """Test generating notifications for FDs maturing in 7 days."""
        # Create FD maturing in 7 days
        start_date = datetime.now(timezone.utc) - timedelta(days=358)
        maturity_date = datetime.now(timezone.utc) + timedelta(days=7)
        fd = make_fixed_deposit(start_date=start_date, maturity_date=maturity_date)
        test_db.add(fd)

        # Create settings with only 7-day notifications enabled
        settings = make_notification_setting(
            notify_days_before_30=False, notify_days_before_7=True, notify_on_maturity=False
        )
        test_db.add(settings)
        await test_db.commit()

        response = await client.post('/api/v1/notifications/generate')
        assert response.status_code == 200
        data = response.json()
        assert data['notifications_created'] == 1

    async def test_generate_notifications_today(self, client: AsyncClient, test_db: AsyncSession):
        """Test generating notifications for FDs maturing today."""
        # Create FD maturing in 1 day (within 0-1 day range)
        start_date = datetime.now(timezone.utc) - timedelta(days=364)
        maturity_date = datetime.now(timezone.utc) + timedelta(days=1)
        fd = make_fixed_deposit(start_date=start_date, maturity_date=maturity_date)
        test_db.add(fd)

        # Create settings with only maturity notifications enabled
        settings = make_notification_setting(
            notify_days_before_30=False, notify_days_before_7=False, notify_on_maturity=True
        )
        test_db.add(settings)
        await test_db.commit()

        response = await client.post('/api/v1/notifications/generate')
        assert response.status_code == 200
        data = response.json()
        assert data['notifications_created'] == 1

    async def test_generate_notifications_no_duplicates(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """Test that duplicate notifications are not created."""
        # Create FD and notification
        start_date = datetime.now(timezone.utc) - timedelta(days=358)
        maturity_date = datetime.now(timezone.utc) + timedelta(days=7)
        fd = make_fixed_deposit(start_date=start_date, maturity_date=maturity_date)
        test_db.add(fd)
        await test_db.commit()
        await test_db.refresh(fd)

        # Create existing notification
        notification = make_notification_log(
            fixed_deposit_id=fd.id, notification_type='maturity_7_days'
        )
        test_db.add(notification)

        # Create settings
        settings = make_notification_setting()
        test_db.add(settings)
        await test_db.commit()

        # Try to generate again
        response = await client.post('/api/v1/notifications/generate')
        assert response.status_code == 200
        data = response.json()
        assert data['notifications_created'] == 0  # Should not create duplicate

    async def test_generate_notifications_multiple_fds(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """Test generating notifications for multiple FDs."""
        # Create 2 FDs maturing in 7 days
        start_date = datetime.now(timezone.utc) - timedelta(days=358)
        maturity_date = datetime.now(timezone.utc) + timedelta(days=7)

        fd1 = make_fixed_deposit(
            start_date=start_date,
            maturity_date=maturity_date,
            institution_name='Bank A',
        )
        fd2 = make_fixed_deposit(
            start_date=start_date,
            maturity_date=maturity_date,
            institution_name='Bank B',
        )
        test_db.add_all([fd1, fd2])

        # Create settings
        settings = make_notification_setting()
        test_db.add(settings)
        await test_db.commit()

        response = await client.post('/api/v1/notifications/generate')
        assert response.status_code == 200
        data = response.json()
        assert data['notifications_created'] == 2


@pytest.mark.asyncio
class TestNotificationListAPI:
    """Test notification listing and management."""

    async def test_get_pending_notifications_empty(self, client: AsyncClient):
        """Test getting pending notifications when none exist."""
        response = await client.get('/api/v1/notifications/pending')
        assert response.status_code == 200
        assert response.json() == []

    async def test_get_pending_notifications_with_fd_details(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """Test getting pending notifications with FD details."""
        # Create FD and notification
        fd = make_fixed_deposit(institution_name='Test Bank', account_number='FD-123')
        test_db.add(fd)
        await test_db.commit()
        await test_db.refresh(fd)

        notification = make_notification_log(
            fixed_deposit_id=fd.id,
            notification_type='maturity_7_days',
            status='pending',
        )
        test_db.add(notification)
        await test_db.commit()

        response = await client.get('/api/v1/notifications/pending')
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]['institution_name'] == 'Test Bank'
        assert data[0]['account_number'] == 'FD-123'
        assert data[0]['notification_type'] == 'maturity_7_days'
        assert data[0]['status'] == 'pending'

    async def test_get_pending_notifications_filters_by_status(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """Test that only pending notifications are returned."""
        # Create FD
        fd = make_fixed_deposit()
        test_db.add(fd)
        await test_db.commit()
        await test_db.refresh(fd)

        # Create pending and dismissed notifications
        pending_notif = make_notification_log(fixed_deposit_id=fd.id, status='pending')
        dismissed_notif = make_notification_log(fixed_deposit_id=fd.id, status='dismissed')
        test_db.add_all([pending_notif, dismissed_notif])
        await test_db.commit()

        response = await client.get('/api/v1/notifications/pending')
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]['status'] == 'pending'

    async def test_mark_notification_displayed(self, client: AsyncClient, test_db: AsyncSession):
        """Test marking a notification as displayed."""
        # Create FD and notification
        fd = make_fixed_deposit()
        test_db.add(fd)
        await test_db.commit()
        await test_db.refresh(fd)

        notification = make_notification_log(fixed_deposit_id=fd.id, status='pending')
        test_db.add(notification)
        await test_db.commit()
        await test_db.refresh(notification)

        response = await client.patch(f'/api/v1/notifications/{notification.id}/display')
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'displayed'
        assert data['displayed_at'] is not None

    async def test_dismiss_notifications_success(self, client: AsyncClient, test_db: AsyncSession):
        """Test dismissing multiple notifications."""
        # Create FD and notifications
        fd = make_fixed_deposit()
        test_db.add(fd)
        await test_db.commit()
        await test_db.refresh(fd)

        notif1 = make_notification_log(fixed_deposit_id=fd.id, status='pending')
        notif2 = make_notification_log(fixed_deposit_id=fd.id, status='pending')
        test_db.add_all([notif1, notif2])
        await test_db.commit()
        await test_db.refresh(notif1)
        await test_db.refresh(notif2)

        response = await client.post(
            '/api/v1/notifications/dismiss',
            json={'notification_ids': [notif1.id, notif2.id]},
        )
        assert response.status_code == 200
        data = response.json()
        assert data['dismissed_count'] == 2

        # Verify notifications are dismissed
        response = await client.get('/api/v1/notifications/pending')
        assert response.status_code == 200
        assert response.json() == []

    async def test_dismiss_notifications_empty_list(self, client: AsyncClient):
        """Test dismissing with empty list returns 0."""
        response = await client.post('/api/v1/notifications/dismiss', json={'notification_ids': []})
        assert response.status_code == 200
        data = response.json()
        assert data['dismissed_count'] == 0
