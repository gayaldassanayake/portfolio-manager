"""Notification setting model."""

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class NotificationSetting(Base):
    """Global notification settings.

    Stores user preferences for FD maturity notifications.
    This is a singleton table (single row with id=1).
    """

    __tablename__ = 'notification_settings'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    notify_days_before_30: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    notify_days_before_7: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    notify_on_maturity: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    email_notifications_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )  # future use
    email_address: Mapped[str | None] = mapped_column(String, nullable=True)  # future use
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
