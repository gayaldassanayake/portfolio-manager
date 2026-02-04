"""Notification management API endpoints."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.fixed_deposit import FixedDeposit
from app.models.notification_log import NotificationLog, NotificationStatus, NotificationType
from app.models.notification_setting import NotificationSetting
from app.schemas import (
    NotificationDismissRequest,
    NotificationGenerateResponse,
    NotificationLogResponse,
    NotificationSettingResponse,
    NotificationSettingUpdate,
    NotificationWithFD,
)

router = APIRouter(prefix='/api/v1/notifications', tags=['Notifications'])


@router.get('/settings', response_model=NotificationSettingResponse)
async def get_notification_settings(db: AsyncSession = Depends(get_db)):
    """Get notification settings.

    Creates default settings if they don't exist.

    Args:
        db: Database session.

    Returns:
        NotificationSettingResponse: Current notification settings.

    """
    result = await db.execute(select(NotificationSetting).where(NotificationSetting.id == 1))
    settings = result.scalar_one_or_none()

    if not settings:
        # Create default settings
        settings = NotificationSetting(
            id=1,
            notify_days_before_30=True,
            notify_days_before_7=True,
            notify_on_maturity=True,
            email_notifications_enabled=False,
            email_address=None,
        )
        db.add(settings)
        await db.commit()
        await db.refresh(settings)

    return settings


@router.put('/settings', response_model=NotificationSettingResponse)
async def update_notification_settings(
    settings_update: NotificationSettingUpdate, db: AsyncSession = Depends(get_db)
):
    """Update notification settings.

    Args:
        settings_update: Updated settings data.
        db: Database session.

    Returns:
        NotificationSettingResponse: Updated settings.

    Raises:
        HTTPException: If settings not found.

    """
    result = await db.execute(select(NotificationSetting).where(NotificationSetting.id == 1))
    settings = result.scalar_one_or_none()

    if not settings:
        # Create if doesn't exist
        settings = NotificationSetting(id=1)
        db.add(settings)

    update_data = settings_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(settings, field, value)

    await db.commit()
    await db.refresh(settings)
    return settings


@router.post('/generate', response_model=NotificationGenerateResponse)
async def generate_notifications(db: AsyncSession = Depends(get_db)):
    """Generate pending notifications for upcoming FD maturities.

    Checks all active FDs and creates notifications based on settings.
    Skips notifications that already exist for a given FD+type combination.

    Args:
        db: Database session.

    Returns:
        NotificationGenerateResponse: Count of notifications created.

    """
    # Get notification settings
    result = await db.execute(select(NotificationSetting).where(NotificationSetting.id == 1))
    settings = result.scalar_one_or_none()

    if not settings:
        # Create default settings
        settings = NotificationSetting(
            id=1,
            notify_days_before_30=True,
            notify_days_before_7=True,
            notify_on_maturity=True,
        )
        db.add(settings)
        await db.commit()
        await db.refresh(settings)

    # Get all active (non-matured) FDs
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(FixedDeposit)
        .where(FixedDeposit.maturity_date > now)
        .order_by(FixedDeposit.maturity_date)
    )
    active_fds = result.scalars().all()

    notifications_created = 0

    for fd in active_fds:
        # Ensure maturity_date is timezone-aware
        maturity_date = fd.maturity_date
        if maturity_date.tzinfo is None:
            maturity_date = maturity_date.replace(tzinfo=timezone.utc)

        days_to_maturity = (maturity_date - now).days

        # Determine which notifications should be created
        notification_types_to_create = []

        # Check 30-day notification (28-32 day range for tolerance)
        if settings.notify_days_before_30 and 28 <= days_to_maturity <= 32:
            notification_types_to_create.append(NotificationType.MATURITY_30_DAYS)

        # Check 7-day notification (5-9 day range for tolerance)
        if settings.notify_days_before_7 and 5 <= days_to_maturity <= 9:
            notification_types_to_create.append(NotificationType.MATURITY_7_DAYS)

        # Check maturity day notification (0-1 day range)
        if settings.notify_on_maturity and 0 <= days_to_maturity <= 1:
            notification_types_to_create.append(NotificationType.MATURITY_TODAY)

        # Create notifications if they don't already exist
        for notification_type in notification_types_to_create:
            # Check if notification already exists for this FD + type
            existing = await db.execute(
                select(NotificationLog).where(
                    NotificationLog.fixed_deposit_id == fd.id,
                    NotificationLog.notification_type == notification_type.value,
                )
            )
            if existing.scalar_one_or_none():
                continue  # Skip if already exists

            # Create new notification
            notification = NotificationLog(
                fixed_deposit_id=fd.id,
                notification_type=notification_type.value,
                status=NotificationStatus.PENDING.value,
            )
            db.add(notification)
            notifications_created += 1

    await db.commit()

    return NotificationGenerateResponse(
        notifications_created=notifications_created,
        message=f'Successfully generated {notifications_created} notification(s)',
    )


@router.get('/pending', response_model=list[NotificationWithFD])
async def get_pending_notifications(db: AsyncSession = Depends(get_db)):
    """Get all pending notifications with FD details.

    Args:
        db: Database session.

    Returns:
        List of pending notifications with associated FD information.

    """
    result = await db.execute(
        select(NotificationLog, FixedDeposit)
        .join(FixedDeposit, NotificationLog.fixed_deposit_id == FixedDeposit.id)
        .where(NotificationLog.status == NotificationStatus.PENDING.value)
        .order_by(NotificationLog.created_at.desc())
    )
    rows = result.all()

    notifications = []
    for notification_log, fixed_deposit in rows:
        notifications.append(
            NotificationWithFD(
                id=notification_log.id,
                fixed_deposit_id=notification_log.fixed_deposit_id,
                notification_type=notification_log.notification_type,
                status=notification_log.status,
                created_at=notification_log.created_at,
                displayed_at=notification_log.displayed_at,
                dismissed_at=notification_log.dismissed_at,
                institution_name=fixed_deposit.institution_name,
                account_number=fixed_deposit.account_number,
                principal_amount=fixed_deposit.principal_amount,
                maturity_date=fixed_deposit.maturity_date,
                interest_rate=fixed_deposit.interest_rate,
            )
        )

    return notifications


@router.patch('/{notification_id}/display', response_model=NotificationLogResponse)
async def mark_notification_displayed(notification_id: int, db: AsyncSession = Depends(get_db)):
    """Mark a notification as displayed.

    Args:
        notification_id: Notification ID.
        db: Database session.

    Returns:
        NotificationLogResponse: Updated notification.

    Raises:
        HTTPException: If notification not found.

    """
    result = await db.execute(select(NotificationLog).where(NotificationLog.id == notification_id))
    notification = result.scalar_one_or_none()

    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Notification not found')

    notification.status = NotificationStatus.DISPLAYED.value
    notification.displayed_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(notification)
    return notification


@router.post('/dismiss', response_model=dict)
async def dismiss_notifications(
    request: NotificationDismissRequest, db: AsyncSession = Depends(get_db)
):
    """Dismiss multiple notifications.

    Args:
        request: List of notification IDs to dismiss.
        db: Database session.

    Returns:
        Dictionary with count of dismissed notifications.

    """
    if not request.notification_ids:
        return {'dismissed_count': 0, 'message': 'No notifications to dismiss'}

    result = await db.execute(
        select(NotificationLog).where(NotificationLog.id.in_(request.notification_ids))
    )
    notifications = result.scalars().all()

    dismissed_count = 0
    now = datetime.now(timezone.utc)

    for notification in notifications:
        notification.status = NotificationStatus.DISMISSED.value
        notification.dismissed_at = now
        dismissed_count += 1

    await db.commit()

    return {
        'dismissed_count': dismissed_count,
        'message': f'Dismissed {dismissed_count} notification(s)',
    }
