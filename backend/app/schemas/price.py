"""Price-related Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PriceBase(BaseModel):
    """Base price schema.

    Attributes:
        date: Price date.
        price: Unit price.

    """

    date: datetime
    price: float


class PriceCreate(PriceBase):
    """Schema for creating a price.

    Attributes:
        unit_trust_id: ID of the unit trust.

    """

    unit_trust_id: int


class PriceUpdate(BaseModel):
    """Schema for updating a price.

    All fields are optional.

    Attributes:
        date: New price date.
        price: New price value.

    """

    date: datetime | None = None
    price: float | None = None


class PriceResponse(PriceBase):
    """Schema for price response.

    Attributes:
        id: Price ID.
        unit_trust_id: ID of the unit trust.
        created_at: Creation timestamp.

    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    unit_trust_id: int
    created_at: datetime
