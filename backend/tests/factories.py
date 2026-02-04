"""Test data factories for creating test objects."""

from datetime import datetime, timedelta, timezone

from app.models.fixed_deposit import FixedDeposit
from app.models.notification_log import NotificationLog
from app.models.notification_setting import NotificationSetting
from app.models.price import Price
from app.models.transaction import Transaction
from app.models.unit_trust import UnitTrust


def make_unit_trust(
    name: str = 'Test Fund',
    symbol: str = 'TEST',
    description: str | None = 'Test unit trust description',
    provider: str | None = None,
    provider_symbol: str | None = None,
) -> UnitTrust:
    """Create a unit trust instance for testing.

    Args:
        name: Unit trust name.
        symbol: Unit trust symbol.
        description: Unit trust description.
        provider: Price provider name (e.g., 'yahoo', 'cal').
        provider_symbol: Symbol used by the provider.

    Returns:
        UnitTrust: Test unit trust instance.

    """
    return UnitTrust(
        name=name,
        symbol=symbol,
        description=description,
        provider=provider,
        provider_symbol=provider_symbol,
    )


def make_price(
    unit_trust_id: int,
    date: datetime | None = None,
    price: float = 100.0,
) -> Price:
    """Create a price instance for testing.

    Args:
        unit_trust_id: Unit trust ID.
        date: Price date (defaults to now).
        price: Price value.

    Returns:
        Price: Test price instance.

    """
    if date is None:
        date = datetime.now(timezone.utc)
    return Price(unit_trust_id=unit_trust_id, date=date, price=price)


def make_transaction(
    unit_trust_id: int,
    units: float = 10.0,
    price_per_unit: float = 100.0,
    transaction_date: datetime | None = None,
    transaction_type: str = 'buy',
    notes: str | None = None,
) -> Transaction:
    """Create a transaction instance for testing.

    Args:
        unit_trust_id: Unit trust ID.
        units: Number of units.
        price_per_unit: Price per unit.
        transaction_date: Transaction date (defaults to now).
        transaction_type: Transaction type ('buy' or 'sell').
        notes: Optional transaction notes.

    Returns:
        Transaction: Test transaction instance.

    """
    if transaction_date is None:
        transaction_date = datetime.now(timezone.utc)
    return Transaction(
        unit_trust_id=unit_trust_id,
        transaction_type=transaction_type,
        units=units,
        price_per_unit=price_per_unit,
        transaction_date=transaction_date,
        notes=notes,
    )


def make_price_history(
    unit_trust_id: int,
    days: int = 30,
    start_price: float = 100.0,
    price_change_per_day: float = 1.0,
) -> list[Price]:
    """Create a series of prices for testing.

    Args:
        unit_trust_id: Unit trust ID.
        days: Number of days of price history.
        start_price: Starting price.
        price_change_per_day: Daily price change (can be negative).

    Returns:
        List of Price instances.

    """
    prices = []
    base_date = datetime.now(timezone.utc) - timedelta(days=days)

    for i in range(days):
        date = base_date + timedelta(days=i)
        price = start_price + (i * price_change_per_day)
        prices.append(Price(unit_trust_id=unit_trust_id, date=date, price=max(price, 0.01)))

    return prices


def make_fixed_deposit(
    principal_amount: float = 10000.0,
    interest_rate: float = 8.0,
    start_date: datetime | None = None,
    maturity_date: datetime | None = None,
    institution_name: str = 'Test Bank',
    account_number: str = 'FD-12345',
    interest_payout_frequency: str = 'at_maturity',
    interest_calculation_type: str = 'simple',
    auto_renewal: bool = False,
    notes: str | None = None,
) -> FixedDeposit:
    """Create a fixed deposit instance for testing.

    Args:
        principal_amount: Principal amount.
        interest_rate: Annual interest rate as percentage.
        start_date: Start date (defaults to now).
        maturity_date: Maturity date (defaults to 1 year from start).
        institution_name: Institution name.
        account_number: Account number.
        interest_payout_frequency: Payout frequency.
        interest_calculation_type: Calculation type.
        auto_renewal: Auto-renewal flag.
        notes: Optional notes.

    Returns:
        FixedDeposit: Test fixed deposit instance.
    """
    if start_date is None:
        start_date = datetime.now(timezone.utc)
    if maturity_date is None:
        maturity_date = start_date + timedelta(days=365)

    return FixedDeposit(
        principal_amount=principal_amount,
        interest_rate=interest_rate,
        start_date=start_date,
        maturity_date=maturity_date,
        institution_name=institution_name,
        account_number=account_number,
        interest_payout_frequency=interest_payout_frequency,
        interest_calculation_type=interest_calculation_type,
        auto_renewal=auto_renewal,
        notes=notes,
    )


def make_notification_setting(
    notify_days_before_30: bool = True,
    notify_days_before_7: bool = True,
    notify_on_maturity: bool = True,
) -> NotificationSetting:
    """Create a notification setting instance for testing.

    Args:
        notify_days_before_30: Enable 30-day notifications.
        notify_days_before_7: Enable 7-day notifications.
        notify_on_maturity: Enable maturity notifications.

    Returns:
        NotificationSetting: Test notification setting instance.
    """
    return NotificationSetting(
        id=1,
        notify_days_before_30=notify_days_before_30,
        notify_days_before_7=notify_days_before_7,
        notify_on_maturity=notify_on_maturity,
        email_notifications_enabled=False,
        email_address=None,
    )


def make_notification_log(
    fixed_deposit_id: int,
    notification_type: str = 'maturity_7_days',
    status: str = 'pending',
) -> NotificationLog:
    """Create a notification log instance for testing.

    Args:
        fixed_deposit_id: Fixed deposit ID.
        notification_type: Notification type.
        status: Notification status.

    Returns:
        NotificationLog: Test notification log instance.
    """
    return NotificationLog(
        fixed_deposit_id=fixed_deposit_id,
        notification_type=notification_type,
        status=status,
    )
