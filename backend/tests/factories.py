"""Test data factories for creating test objects."""

from datetime import datetime, timedelta, timezone

from app.models.price import Price
from app.models.transaction import Transaction
from app.models.unit_trust import UnitTrust


def make_unit_trust(
    name: str = 'Test Fund',
    symbol: str = 'TEST',
    description: str | None = 'Test unit trust description',
) -> UnitTrust:
    """Create a unit trust instance for testing.

    Args:
        name: Unit trust name.
        symbol: Unit trust symbol.
        description: Unit trust description.

    Returns:
        UnitTrust: Test unit trust instance.

    """
    return UnitTrust(name=name, symbol=symbol, description=description)


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
