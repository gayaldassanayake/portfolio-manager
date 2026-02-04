"""Interest calculation service for fixed deposits."""

from datetime import datetime, timezone


def calculate_simple_interest(principal: float, annual_rate: float, days: int) -> float:
    """Calculate simple interest.

    Formula: Interest = Principal × Rate × Time

    Args:
        principal: The principal amount
        annual_rate: Annual interest rate as percentage (e.g., 8.5 for 8.5%)
        days: Number of days for the calculation

    Returns:
        The calculated interest amount
    """
    if principal <= 0 or annual_rate < 0 or days < 0:
        return 0.0

    # Convert percentage to decimal and calculate time in years
    rate_decimal = annual_rate / 100
    time_in_years = days / 365

    interest = principal * rate_decimal * time_in_years
    return round(interest, 2)


def calculate_compound_interest(
    principal: float, annual_rate: float, days: int, frequency: str
) -> float:
    """Calculate compound interest.

    Formula: A = P(1 + r/n)^(nt), return A - P

    Args:
        principal: The principal amount
        annual_rate: Annual interest rate as percentage (e.g., 8.5 for 8.5%)
        days: Number of days for the calculation
        frequency: Interest payout frequency ('monthly', 'quarterly', 'annually', 'at_maturity')

    Returns:
        The calculated interest amount (not including principal)
    """
    if principal <= 0 or annual_rate < 0 or days < 0:
        return 0.0

    # Map frequency to compounding periods per year
    frequency_map = {
        'monthly': 12,
        'quarterly': 4,
        'annually': 1,
        'at_maturity': 1,  # Compound once at maturity
    }

    n = frequency_map.get(frequency, 1)
    rate_decimal = annual_rate / 100
    time_in_years = days / 365

    # Calculate compound amount: A = P(1 + r/n)^(nt)
    compound_amount = principal * ((1 + rate_decimal / n) ** (n * time_in_years))

    # Return interest only (A - P)
    interest = compound_amount - principal
    return round(interest, 2)


def calculate_current_value(
    principal: float,
    annual_rate: float,
    start_date: datetime,
    maturity_date: datetime,
    calculation_type: str,
    payout_frequency: str,
    as_of_date: datetime | None = None,
) -> tuple[float, float, int]:
    """Calculate current value of a fixed deposit with accrued interest.

    Args:
        principal: The principal amount
        annual_rate: Annual interest rate as percentage
        start_date: Start date of the FD
        maturity_date: Maturity date of the FD
        calculation_type: 'simple' or 'compound'
        payout_frequency: Interest payout frequency
        as_of_date: Date to calculate value as of (defaults to now)

    Returns:
        Tuple of (current_value, accrued_interest, days_to_maturity)
        - current_value: Principal + accrued interest
        - accrued_interest: Interest earned so far
        - days_to_maturity: Days remaining (negative if matured)
    """
    if as_of_date is None:
        as_of_date = datetime.now(timezone.utc)

    # Ensure all dates are timezone-aware
    if start_date.tzinfo is None:
        start_date = start_date.replace(tzinfo=timezone.utc)
    if maturity_date.tzinfo is None:
        maturity_date = maturity_date.replace(tzinfo=timezone.utc)
    if as_of_date.tzinfo is None:
        as_of_date = as_of_date.replace(tzinfo=timezone.utc)

    # Calculate days to maturity (can be negative if matured)
    days_to_maturity = (maturity_date - as_of_date).days

    # Cap the effective date at maturity date
    effective_date = min(as_of_date, maturity_date)

    # Calculate days elapsed from start
    days_elapsed = (effective_date - start_date).days

    # Handle edge case where effective_date is before start_date
    if days_elapsed < 0:
        return (principal, 0.0, days_to_maturity)

    # Calculate interest based on type
    if calculation_type == 'simple':
        accrued_interest = calculate_simple_interest(principal, annual_rate, days_elapsed)
    else:  # compound
        accrued_interest = calculate_compound_interest(
            principal, annual_rate, days_elapsed, payout_frequency
        )

    current_value = principal + accrued_interest

    return (round(current_value, 2), accrued_interest, days_to_maturity)
