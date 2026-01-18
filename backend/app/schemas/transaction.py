"""Transaction-related Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TransactionBase(BaseModel):
    """Base transaction schema.

    Attributes:
        unit_trust_id: ID of the unit trust.
        units: Number of units.
        price_per_unit: Price per unit.
        transaction_date: Transaction date.

    """

    unit_trust_id: int
    units: float
    price_per_unit: float
    transaction_date: datetime


class TransactionCreate(BaseModel):
    """Schema for creating a transaction.

    Attributes:
        unit_trust_id: ID of the unit trust.
        units: Number of units.
        transaction_date: Transaction date.

    """

    unit_trust_id: int
    units: float
    transaction_date: datetime


class TransactionUpdate(BaseModel):
    """Schema for updating a transaction.

    All fields are optional.

    Attributes:
        units: New number of units.
        price_per_unit: New price per unit.
        transaction_date: New transaction date.

    """

    units: float | None = None
    price_per_unit: float | None = None
    transaction_date: datetime | None = None


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
