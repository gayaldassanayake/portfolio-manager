"""Unit trust model."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.price import Price
    from app.models.transaction import Transaction


class UnitTrust(Base):
    """Represents a unit trust fund.

    Stores unit trust details with related prices and transactions.
    """

    __tablename__ = 'unit_trusts'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    symbol: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    prices: Mapped[list['Price']] = relationship(
        back_populates='unit_trust', cascade='all, delete-orphan'
    )
    transactions: Mapped[list['Transaction']] = relationship(
        back_populates='unit_trust', cascade='all, delete-orphan'
    )
