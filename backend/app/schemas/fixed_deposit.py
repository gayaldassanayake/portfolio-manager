"""Fixed deposit-related Pydantic schemas."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Type literals for fixed deposit enums
InterestPayoutFrequencyType = Literal['monthly', 'quarterly', 'annually', 'at_maturity']
InterestCalculationType = Literal['simple', 'compound']


class FixedDepositBase(BaseModel):
    """Base fixed deposit schema.

    Attributes:
        principal_amount: The principal amount invested.
        interest_rate: Annual interest rate as percentage (e.g., 8.5 for 8.5%).
        start_date: Start date of the fixed deposit.
        maturity_date: Maturity date of the fixed deposit.
        institution_name: Name of the financial institution.
        account_number: Account number or reference.
        interest_payout_frequency: Frequency of interest payout.
        interest_calculation_type: Type of interest calculation (simple or compound).
        auto_renewal: Whether the FD is set for auto-renewal.
        notes: Optional notes about the fixed deposit.
    """

    principal_amount: float = Field(gt=0, description="Principal amount must be positive")
    interest_rate: float = Field(ge=0, le=100, description="Interest rate between 0 and 100")
    start_date: datetime
    maturity_date: datetime
    institution_name: str
    account_number: str
    interest_payout_frequency: InterestPayoutFrequencyType = 'at_maturity'
    interest_calculation_type: InterestCalculationType = 'simple'
    auto_renewal: bool = False
    notes: str | None = None

    @field_validator('maturity_date')
    @classmethod
    def validate_maturity_after_start(cls, v: datetime, info) -> datetime:
        """Validate that maturity date is after start date."""
        if 'start_date' in info.data and v <= info.data['start_date']:
            raise ValueError('Maturity date must be after start date')
        return v


class FixedDepositCreate(FixedDepositBase):
    """Schema for creating a fixed deposit."""


class FixedDepositUpdate(BaseModel):
    """Schema for updating a fixed deposit.

    All fields are optional.
    """

    principal_amount: float | None = Field(None, gt=0)
    interest_rate: float | None = Field(None, ge=0, le=100)
    start_date: datetime | None = None
    maturity_date: datetime | None = None
    institution_name: str | None = None
    account_number: str | None = None
    interest_payout_frequency: InterestPayoutFrequencyType | None = None
    interest_calculation_type: InterestCalculationType | None = None
    auto_renewal: bool | None = None
    notes: str | None = None


class FixedDepositResponse(FixedDepositBase):
    """Schema for fixed deposit response.

    Attributes:
        id: Fixed deposit ID.
        created_at: Creation timestamp.
        updated_at: Last update timestamp.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class FixedDepositWithValue(FixedDepositResponse):
    """Schema for fixed deposit with calculated current value.

    Attributes:
        current_value: Current value including accrued interest.
        accrued_interest: Interest accrued so far.
        days_to_maturity: Days remaining until maturity (negative if matured).
        is_matured: Whether the FD has reached maturity.
        term_days: Total term of the FD in days.
    """

    current_value: float
    accrued_interest: float
    days_to_maturity: int
    is_matured: bool
    term_days: int


class InterestCalculationRequest(BaseModel):
    """Schema for interest calculation request (utility endpoint).

    Attributes:
        principal: Principal amount.
        annual_rate: Annual interest rate as percentage.
        start_date: Start date.
        maturity_date: Maturity date.
        calculation_type: Simple or compound interest.
        payout_frequency: Interest payout frequency.
    """

    principal: float = Field(gt=0)
    annual_rate: float = Field(ge=0, le=100)
    start_date: datetime
    maturity_date: datetime
    calculation_type: InterestCalculationType
    payout_frequency: InterestPayoutFrequencyType


class InterestCalculationResponse(BaseModel):
    """Schema for interest calculation response.

    Attributes:
        total_interest: Total interest at maturity.
        maturity_value: Principal + total interest.
        term_days: Total term in days.
        current_interest: Interest accrued as of today.
        current_value: Current value as of today.
        days_elapsed: Days elapsed from start.
        days_remaining: Days remaining to maturity.
    """

    total_interest: float
    maturity_value: float
    term_days: int
    current_interest: float
    current_value: float
    days_elapsed: int
    days_remaining: int
