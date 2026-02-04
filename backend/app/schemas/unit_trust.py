"""Unit trust-related Pydantic schemas."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

# Supported price providers
ProviderType = Literal['yahoo', 'cal']


class UnitTrustBase(BaseModel):
    """Base unit trust schema.

    Attributes:
        name: Unit trust name.
        symbol: Unit trust symbol.
        description: Optional description.
        provider: Price provider name ('yahoo' or 'cal').
        provider_symbol: Symbol used by the provider (defaults to symbol if not set).

    """

    name: str
    symbol: str
    description: str | None = None
    provider: ProviderType | None = None
    provider_symbol: str | None = None


class UnitTrustCreate(UnitTrustBase):
    """Schema for creating a unit trust."""


class UnitTrustUpdate(BaseModel):
    """Schema for updating a unit trust.

    All fields are optional.

    Attributes:
        name: New name.
        symbol: New symbol.
        description: New description.
        provider: New provider name ('yahoo' or 'cal').
        provider_symbol: New provider symbol.

    """

    name: str | None = None
    symbol: str | None = None
    description: str | None = None
    provider: ProviderType | None = None
    provider_symbol: str | None = None


class UnitTrustResponse(UnitTrustBase):
    """Schema for unit trust response.

    Attributes:
        id: Unit trust ID.
        created_at: Creation timestamp.

    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class UnitTrustWithStats(UnitTrustResponse):
    """Schema for unit trust with statistics.

    Attributes:
        total_units: Total units held.
        avg_purchase_price: Average purchase price.
        latest_price: Latest available price.

    """

    total_units: float = 0.0
    avg_purchase_price: float = 0.0
    latest_price: float | None = None
