"""Transaction-related Pydantic schemas."""

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class TransactionTypeEnum(str, Enum):
    """Enumeration for transaction types."""

    BUY = 'buy'
    SELL = 'sell'


class TransactionBase(BaseModel):
    """Base transaction schema.

    Attributes:
        unit_trust_id: ID of the unit trust.
        transaction_type: Type of transaction (buy or sell).
        units: Number of units (always positive).
        price_per_unit: Price per unit.
        transaction_date: Transaction date.
        notes: Optional notes for the transaction.

    """

    unit_trust_id: int
    transaction_type: Literal['buy', 'sell'] = 'buy'
    units: float = Field(..., gt=0, description='Number of units (must be positive)')
    price_per_unit: float
    transaction_date: datetime
    notes: str | None = None


class TransactionCreate(BaseModel):
    """Schema for creating a transaction.

    Attributes:
        unit_trust_id: ID of the unit trust.
        transaction_type: Type of transaction (buy or sell).
        units: Number of units (always positive).
        transaction_date: Transaction date.
        notes: Optional notes for the transaction.

    """

    unit_trust_id: int
    transaction_type: Literal['buy', 'sell'] = 'buy'
    units: float = Field(..., gt=0, description='Number of units (must be positive)')
    transaction_date: datetime
    notes: str | None = None


class TransactionUpdate(BaseModel):
    """Schema for updating a transaction.

    All fields are optional.

    Attributes:
        transaction_type: Type of transaction (buy or sell).
        units: New number of units.
        price_per_unit: New price per unit.
        transaction_date: New transaction date.
        notes: Updated notes.

    """

    transaction_type: Literal['buy', 'sell'] | None = None
    units: float | None = Field(None, gt=0, description='Number of units (must be positive)')
    price_per_unit: float | None = None
    transaction_date: datetime | None = None
    notes: str | None = None


class TransactionResponse(TransactionBase):
    """Schema for transaction response.

    Attributes:
        id: Transaction ID.
        created_at: Creation timestamp.

    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class TransactionWithUnitTrust(TransactionResponse):
    """Schema for transaction with unit trust details.

    Attributes:
        unit_trust_name: Name of the unit trust.
        unit_trust_symbol: Symbol of the unit trust.

    """

    unit_trust_name: str
    unit_trust_symbol: str
