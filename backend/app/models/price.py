"""Unit trust price model."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.unit_trust import UnitTrust


class Price(Base):
    """Represents historical unit trust prices.

    Tracks daily prices for unit trusts to calculate portfolio performance.
    """

    __tablename__ = 'prices'
    __table_args__ = (UniqueConstraint('unit_trust_id', 'date', name='uq_unit_trust_date'),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    unit_trust_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('unit_trusts.id'), nullable=False, index=True
    )
    date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    unit_trust: Mapped['UnitTrust'] = relationship(back_populates='prices')
