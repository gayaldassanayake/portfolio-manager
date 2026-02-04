"""Notification-related Pydantic schemas."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

# Type literals for notification enums
NotificationTypeType = Literal['maturity_30_days', 'maturity_7_days', 'maturity_today']
NotificationStatusType = Literal['pending', 'displayed', 'dismissed']


class NotificationSettingResponse(BaseModel):
    """Schema for notification settings response.

    Attributes:
        id: Settings ID (always 1).
        notify_days_before_30: Enable 30-day advance notifications.
        notify_days_before_7: Enable 7-day advance notifications.
        notify_on_maturity: Enable maturity day notifications.
        email_notifications_enabled: Enable email notifications (future).
        email_address: Email address for notifications (future).
        created_at: Creation timestamp.
        updated_at: Last update timestamp.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    notify_days_before_30: bool
    notify_days_before_7: bool
    notify_on_maturity: bool
    email_notifications_enabled: bool
    email_address: str | None
    created_at: datetime
    updated_at: datetime


class NotificationSettingUpdate(BaseModel):
    """Schema for updating notification settings.

    All fields are optional.
    """

    notify_days_before_30: bool | None = None
    notify_days_before_7: bool | None = None
    notify_on_maturity: bool | None = None
    email_notifications_enabled: bool | None = None
    email_address: str | None = None


class NotificationLogResponse(BaseModel):
    """Schema for notification log response.

    Attributes:
        id: Notification ID.
        fixed_deposit_id: Associated fixed deposit ID.
        notification_type: Type of notification.
        status: Current status.
        created_at: Creation timestamp.
        displayed_at: When notification was displayed.
        dismissed_at: When notification was dismissed.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    fixed_deposit_id: int
    notification_type: NotificationTypeType
    status: NotificationStatusType
    created_at: datetime
    displayed_at: datetime | None
    dismissed_at: datetime | None


class NotificationWithFD(NotificationLogResponse):
    """Schema for notification with associated fixed deposit details.

    Attributes:
        institution_name: Name of the financial institution.
        account_number: Account number.
        principal_amount: Principal amount.
        maturity_date: Maturity date.
        interest_rate: Interest rate.
    """

    institution_name: str
    account_number: str
    principal_amount: float
    maturity_date: datetime
    interest_rate: float


class NotificationDismissRequest(BaseModel):
    """Schema for dismissing multiple notifications.

    Attributes:
        notification_ids: List of notification IDs to dismiss.
    """

    notification_ids: list[int]


class NotificationGenerateResponse(BaseModel):
    """Schema for notification generation response.

    Attributes:
        notifications_created: Number of new notifications created.
        message: Success message.
    """

    notifications_created: int
    message: str
