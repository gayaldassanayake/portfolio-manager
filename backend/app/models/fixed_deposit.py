"""Fixed deposit model."""

from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.notification_log import NotificationLog


class InterestPayoutFrequency(str, Enum):
    """Interest payout frequency options."""

    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUALLY = "annually"
    AT_MATURITY = "at_maturity"


class InterestCalculationType(str, Enum):
    """Interest calculation type options."""

    SIMPLE = "simple"
    COMPOUND = "compound"


class FixedDeposit(Base):
    """Represents a fixed deposit investment.

    Stores fixed deposit details with interest calculation settings
    and maturity tracking.
    """

    __tablename__ = 'fixed_deposits'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    principal_amount: Mapped[float] = mapped_column(Float, nullable=False)
    interest_rate: Mapped[float] = mapped_column(Float, nullable=False)  # percentage
    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    maturity_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    institution_name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    account_number: Mapped[str] = mapped_column(String, nullable=False)
    interest_payout_frequency: Mapped[str] = mapped_column(
        String, nullable=False, default=InterestPayoutFrequency.AT_MATURITY.value
    )
    interest_calculation_type: Mapped[str] = mapped_column(
        String, nullable=False, default=InterestCalculationType.SIMPLE.value
    )
    auto_renewal: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    notes: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    notification_logs: Mapped[list['NotificationLog']] = relationship(
        back_populates='fixed_deposit', cascade='all, delete-orphan'
    )
