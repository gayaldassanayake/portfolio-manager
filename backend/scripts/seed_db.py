"""Generate sample data for the portfolio database."""

import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.database import AsyncSessionLocal, Base, engine
from app.models.price import Price
from app.models.transaction import Transaction
from app.models.unit_trust import UnitTrust

SAMPLE_UNIT_TRUSTS = [
    {
        'name': 'Vanguard 500 Index Fund',
        'symbol': 'VFIAX',
        'description': 'A mutual fund that tracks the S&P 500 index of large-cap US stocks.',
    },
    {
        'name': 'Fidelity Contrafund',
        'symbol': 'FCNTX',
        'description': 'An actively managed fund investing in US companies with strong growth potential.',
    },
    {
        'name': 'T. Rowe Price Blue Chip Growth Fund',
        'symbol': 'TRBCX',
        'description': 'A fund focused on large-cap US growth companies with sustainable competitive advantages.',
    },
    {
        'name': 'American Funds Growth Fund of America',
        'symbol': 'AGTHX',
        'description': 'A diversified growth fund investing in US and international companies.',
    },
]


async def generate_price_history(unit_trust_id: int, days: int = 365):
    """Generate price history for a unit trust.

    Args:
        unit_trust_id: Unit trust ID.
        days: Number of days of price history.

    """
    base_price = 1.0
    volatility = 0.02

    prices = []
    base_date = datetime.now(timezone.utc) - timedelta(days=days)

    for i in range(days):
        date = base_date + timedelta(days=i)
        if i == 0:
            price = base_price
        else:
            change = 1 + (hash(str(date)) % 1000 - 500) / 10000 * volatility * 10
            price = max(0.1, prices[-1].price * change)

        prices.append(
            Price(
                unit_trust_id=unit_trust_id,
                date=date.replace(hour=0, minute=0, second=0, microsecond=0),
                price=round(price, 4),
            )
        )

    return prices


async def generate_transactions(unit_trust_id: int, count: int = 12):
    """Generate sample transactions for a unit trust.

    Args:
        unit_trust_id: Unit trust ID.
        count: Number of transactions to generate.

    """
    transactions = []
    base_date = datetime.now(timezone.utc) - timedelta(days=365)

    for i in range(count):
        transaction_date = base_date + timedelta(days=i * (365 // count))
        units = round(100 + (hash(str(transaction_date)) % 500), 2)
        price_per_unit = round(1.0 + (hash(str(transaction_date)) % 100) / 100, 4)

        transactions.append(
            Transaction(
                unit_trust_id=unit_trust_id,
                units=units,
                price_per_unit=price_per_unit,
                transaction_date=transaction_date,
            )
        )

    return transactions


async def seed_database():
    """Seed the database with sample data."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        for unit_trust_data in SAMPLE_UNIT_TRUSTS:
            result = await session.execute(
                select(UnitTrust).where(UnitTrust.symbol == unit_trust_data['symbol'])
            )
            existing = result.scalar_one_or_none()

            if existing:
                print(f'Unit trust {unit_trust_data["symbol"]} already exists, skipping...')
                continue

            unit_trust = UnitTrust(**unit_trust_data)
            session.add(unit_trust)
            await session.flush()

            print(f'Created unit trust: {unit_trust.name} ({unit_trust.symbol})')

            prices = await generate_price_history(unit_trust.id, days=365)
            for price in prices:
                session.add(price)
            print(f'  - Added {len(prices)} price records')

            transactions = await generate_transactions(unit_trust.id, count=12)
            for transaction in transactions:
                session.add(transaction)
            print(f'  - Added {len(transactions)} transaction records')

        await session.commit()
        print('\nDatabase seeded successfully!')

    await engine.dispose()


def main():
    """Run the seed command."""
    try:
        asyncio.run(asyncio.wait_for(seed_database(), timeout=300))
    except asyncio.TimeoutError:
        print('Error: Database seeding timed out after 300 seconds')
        return 1


if __name__ == '__main__':
    try:
        asyncio.run(asyncio.wait_for(seed_database(), timeout=300))
    except asyncio.TimeoutError:
        print('Error: Database seeding timed out after 300 seconds')
        raise SystemExit(1)
