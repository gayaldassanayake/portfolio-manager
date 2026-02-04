"""Notification log model."""

from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.fixed_deposit import FixedDeposit


class NotificationType(str, Enum):
    """Notification type options."""

    MATURITY_30_DAYS = "maturity_30_days"
    MATURITY_7_DAYS = "maturity_7_days"
    MATURITY_TODAY = "maturity_today"


class NotificationStatus(str, Enum):
    """Notification status options."""

    PENDING = "pending"
    DISPLAYED = "displayed"
    DISMISSED = "dismissed"


class NotificationLog(Base):
    """Tracks individual notifications for fixed deposits.

    Stores notification history with status tracking for display and dismissal.
    """

    __tablename__ = 'notification_logs'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    fixed_deposit_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('fixed_deposits.id', ondelete='CASCADE'), nullable=False, index=True
    )
    notification_type: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(
        String, nullable=False, default=NotificationStatus.PENDING.value, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), index=True
    )
    displayed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    dismissed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    fixed_deposit: Mapped['FixedDeposit'] = relationship(back_populates='notification_logs')
