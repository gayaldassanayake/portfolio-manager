"""Transaction model."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.unit_trust import UnitTrust


class Transaction(Base):
    """Represents unit trust buy/sell transactions.

    Records purchases and sales of unit trust units with prices.
    """

    __tablename__ = 'transactions'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    unit_trust_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('unit_trusts.id'), nullable=False, index=True
    )
    units: Mapped[float] = mapped_column(Float, nullable=False)
    price_per_unit: Mapped[float] = mapped_column(Float, nullable=False)
    transaction_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    unit_trust: Mapped['UnitTrust'] = relationship(back_populates='transactions')
