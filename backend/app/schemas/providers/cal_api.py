"""Pydantic models for CAL API responses.

This module contains models for validating and parsing responses from the
Capital Alliance (CAL) Unit Trust API.
"""

from datetime import date as date_type
from decimal import Decimal

from pydantic import BaseModel, Field, RootModel, field_validator


class CALPriceEntry(BaseModel):
    """Represents a single price entry from CAL API.

    The CAL API returns prices as strings with many decimal places.
    This model parses and validates them into Decimal types.

    Attributes:
        date: The date of the price (YYYY-MM-DD format).
        unit_price: The base NAV (Net Asset Value) price per unit.
        red_price: Redemption price (sell to CAL) - populated for equity/balanced funds.
        cre_price: Creation price (buy from CAL) - populated for equity/balanced funds.

    """

    date: date_type = Field(..., description='Date of the price')
    unit_price: Decimal = Field(..., description='Base NAV price per unit', gt=0)
    red_price: Decimal | None = Field(None, description='Redemption (sell) price')
    cre_price: Decimal | None = Field(None, description='Creation (buy) price')

    @field_validator('unit_price', 'red_price', 'cre_price', mode='before')
    @classmethod
    def parse_decimal_string(cls, v: str | Decimal | None) -> Decimal | None:
        """Parse price strings from CAL API into Decimal.

        The CAL API returns prices as strings like "39.1854000000".
        This validator converts them to Decimal for precise financial calculations.

        Args:
            v: The price value (string, Decimal, or None).

        Returns:
            Decimal or None if the input was None.

        Raises:
            ValueError: If the string cannot be parsed as a Decimal.

        """
        if v is None or v == '':
            return None
        if isinstance(v, Decimal):
            return v
        if isinstance(v, str):
            # Handle empty string or "null" as None
            if v.strip() == '' or v.strip().lower() == 'null':
                return None
            return Decimal(v)
        return Decimal(str(v))


class CALPricesResponse(RootModel[dict[str, list[CALPriceEntry]]]):
    """Response from the getUTPrices endpoint.

    The CAL API returns a JSON object where keys are fund codes
    and values are arrays of price entries.

    Example:
        {
            "IGF": [
                {
                    "date": "2026-02-02",
                    "unit_price": "39.1854000000",
                    "red_price": null,
                    "cre_price": null
                }
            ],
            "QEF": [...]
        }

    """

    root: dict[str, list[CALPriceEntry]]


class CALFundRate(BaseModel):
    """Fund rate summary from getUTFundRates endpoint.

    This model is for the fund rates summary endpoint, which returns
    metadata and performance metrics for all funds.

    Note: This model is optional and included for future use.
    The current implementation only uses the getUTPrices endpoint.

    Attributes:
        FUND: Short code for the fund (e.g., 'IGF', 'QEF').
        FUND_NAME: Full descriptive name of the fund.
        LATEST_PRICE: The most recent price available.
        OLD_PRICE: The price on the requested valuedate.
        PORTFOLIO: Total fund size (AUM) in LKR.
        LATEST_DATE: The date of the LATEST_PRICE.
        OLD_DATE: The actual date used for OLD_PRICE.

    """

    FUND: str = Field(..., description='Fund code')
    FUND_NAME: str = Field(..., description='Full fund name')
    LATEST_PRICE: Decimal = Field(..., description='Most recent price', gt=0)
    OLD_PRICE: Decimal | None = Field(None, description='Price on valuedate')
    PORTFOLIO: Decimal | None = Field(None, description='Total AUM in LKR')
    LATEST_DATE: date_type = Field(..., description='Date of latest price')
    OLD_DATE: date_type | None = Field(None, description='Date of old price')

    @field_validator('LATEST_PRICE', 'OLD_PRICE', 'PORTFOLIO', mode='before')
    @classmethod
    def parse_decimal_string(cls, v: str | Decimal | None) -> Decimal | None:
        """Parse price/portfolio strings into Decimal.

        Args:
            v: The value (string, Decimal, or None).

        Returns:
            Decimal or None if the input was None.

        Raises:
            ValueError: If the string cannot be parsed as a Decimal.

        """
        if v is None or v == '':
            return None
        if isinstance(v, Decimal):
            return v
        if isinstance(v, str):
            if v.strip() == '' or v.strip().lower() == 'null':
                return None
            return Decimal(v)
        return Decimal(str(v))


class UTMSFundEntry(BaseModel):
    """A single fund entry from the ut_fundsRates analytics endpoint.

    This endpoint (reached via the portal's bypass-get-url proxy) returns,
    for every fund, the latest price plus the price on a requested ``odate``.
    Unlike getUTPrices it accepts arbitrary historical dates, so it is used to
    backfill prices older than the getUTPrices ~90-day window.

    Attributes:
        FUND: Short code for the fund (e.g., 'IGF', 'QEF').
        FUND_NAME: Full descriptive name of the fund.
        LATEST_DATE: Date of the most recent price.
        LATEST_PRICE: The most recent price available.
        OLD_DATE: The date the OLD_PRICE applies to (echoes requested odate).
        OLD_PRICE: The NAV price on OLD_DATE.
        PORTFOLIO: Total fund size (AUM) in LKR.
        RATE_PERIOD: Reporting period in days used by the source.

    """

    FUND: str = Field(..., description='Fund code')
    FUND_NAME: str | None = Field(None, description='Full fund name')
    LATEST_DATE: date_type | None = Field(None, description='Date of latest price')
    LATEST_PRICE: Decimal | None = Field(None, description='Most recent price')
    OLD_DATE: date_type | None = Field(None, description='Date of old price')
    OLD_PRICE: Decimal | None = Field(None, description='NAV on OLD_DATE')
    PORTFOLIO: Decimal | None = Field(None, description='Total AUM in LKR')
    RATE_PERIOD: str | None = Field(None, description='Reporting period in days')

    @field_validator('LATEST_PRICE', 'OLD_PRICE', 'PORTFOLIO', mode='before')
    @classmethod
    def parse_decimal_string(cls, v: str | Decimal | None) -> Decimal | None:
        """Parse price/portfolio strings into Decimal (or None)."""
        if v is None or v == '':
            return None
        if isinstance(v, Decimal):
            return v
        if isinstance(v, str):
            if v.strip() == '' or v.strip().lower() == 'null':
                return None
            return Decimal(v)
        return Decimal(str(v))


class UTMSFundRatesResponse(BaseModel):
    """Response from the ut_fundsRates analytics endpoint.

    The endpoint returns a JSON object with a single ``UTMS_FUND`` key holding
    an array of per-fund entries.

    Example:
        {
            "UTMS_FUND": [
                {
                    "FUND": "QEF",
                    "FUND_NAME": "Capital Alliance Quantitative Equity Fund",
                    "LATEST_DATE": "2026-05-21",
                    "LATEST_PRICE": "68.0908000000",
                    "OLD_DATE": "2025-05-21",
                    "OLD_PRICE": "53.0779000000",
                    "PORTFOLIO": "14430008989.5112",
                    "RATE_PERIOD": "30"
                }
            ]
        }

    """

    UTMS_FUND: list[UTMSFundEntry] = Field(default_factory=list)
