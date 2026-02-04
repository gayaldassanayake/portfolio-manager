"""Generate sample data for the portfolio database using real Yahoo Finance data."""

import asyncio
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select

from app.database import AsyncSessionLocal, Base, engine
from app.models.price import Price
from app.models.transaction import Transaction
from app.models.unit_trust import UnitTrust
from app.services.providers import ProviderError, get_provider

# Sample unit trusts with Yahoo Finance tickers
SAMPLE_UNIT_TRUSTS = [
    {
        'name': 'Vanguard 500 Index Fund',
        'symbol': 'VFIAX',
        'description': 'A mutual fund that tracks the S&P 500 index of large-cap US stocks.',
        'provider': 'yahoo',
    },
    {
        'name': 'Fidelity Contrafund',
        'symbol': 'FCNTX',
        'description': 'An actively managed fund investing in US companies with strong growth'
        + ' potential.',
        'provider': 'yahoo',
    },
    {
        'name': 'T. Rowe Price Blue Chip Growth Fund',
        'symbol': 'TRBCX',
        'description': 'A fund focused on large-cap US growth companies with sustainable'
        + ' competitive advantages.',
        'provider': 'yahoo',
    },
    {
        'name': 'Apple Inc.',
        'symbol': 'AAPL',
        'description': 'Apple Inc. designs, manufactures, and markets smartphones, computers, '
        + 'tablets, wearables, and accessories.',
        'provider': 'yahoo',
    },
    {
        'name': 'Microsoft Corporation',
        'symbol': 'MSFT',
        'description': 'Microsoft develops and supports software, services, devices, '
        + 'and solutions worldwide.',
        'provider': 'yahoo',
    },
]


async def fetch_price_history_from_yahoo(
    unit_trust_id: int, symbol: str, days: int = 365
) -> list[Price]:
    """Fetch real price history from Yahoo Finance.

    Args:
        unit_trust_id: Unit trust ID.
        symbol: Yahoo Finance ticker symbol.
        days: Number of days of price history to fetch.

    Returns:
        List of Price objects with real market data.

    """
    provider = get_provider('yahoo')
    if not provider:
        raise RuntimeError('Yahoo provider not available')

    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    try:
        fetched_prices = await provider.fetch_prices(symbol, start_date, end_date)
    except ProviderError as e:
        print(f'    Warning: Could not fetch prices for {symbol}: {e}')
        return []

    prices = []
    for fp in fetched_prices:
        prices.append(
            Price(
                unit_trust_id=unit_trust_id,
                date=datetime.combine(fp.date, datetime.min.time(), tzinfo=timezone.utc),
                price=round(fp.price, 4),
            )
        )

    return prices


async def generate_transactions(
    unit_trust_id: int, prices: list[Price], count: int = 12
) -> list[Transaction]:
    """Generate sample transactions for a unit trust using real prices.

    Generates a mix of buy and sell transactions. Buy transactions are more
    frequent (about 75%) and sell transactions are smaller (about 30-50% of
    accumulated units at that point).

    Args:
        unit_trust_id: Unit trust ID.
        prices: List of Price objects to use for transaction prices.
        count: Number of transactions to generate.

    Returns:
        List of Transaction objects.

    """
    if not prices:
        return []

    transactions = []
    accumulated_units = 0.0

    # Create a price lookup by date
    price_by_date: dict[date, float] = {p.date.date(): p.price for p in prices}
    sorted_dates = sorted(price_by_date.keys())

    if len(sorted_dates) < count:
        count = len(sorted_dates)

    # Sample notes for transactions
    buy_notes = [
        'Monthly investment',
        'Dollar cost averaging',
        'Bonus reinvestment',
        'Dividend reinvestment',
        None,
        None,
        None,
    ]
    sell_notes = [
        'Rebalancing portfolio',
        'Taking profits',
        'Tax-loss harvesting',
        None,
    ]

    # Space transactions evenly across the date range
    step = max(1, len(sorted_dates) // count)

    for i in range(count):
        date_idx = min(i * step, len(sorted_dates) - 1)
        transaction_date = sorted_dates[date_idx]
        price_per_unit = price_by_date[transaction_date]

        # Determine if this should be a sell transaction
        # Only sell after we have some units, and roughly 25% of transactions are sells
        is_sell = accumulated_units > 10 and (hash(str(transaction_date) + 'type') % 4 == 0)

        if is_sell:
            # Sell 30-50% of accumulated units
            sell_percentage = 0.3 + (hash(str(transaction_date) + 'pct') % 20) / 100
            units = round(accumulated_units * sell_percentage, 2)
            transaction_type = 'sell'
            notes = sell_notes[hash(str(transaction_date) + 'note') % len(sell_notes)]
            accumulated_units -= units
        else:
            # Buy transaction - amount varies by price (invest ~$1000-5000 worth)
            investment_amount = 1000 + (hash(str(transaction_date)) % 4000)
            units = round(investment_amount / price_per_unit, 4)
            transaction_type = 'buy'
            notes = buy_notes[hash(str(transaction_date) + 'note') % len(buy_notes)]
            accumulated_units += units

        transactions.append(
            Transaction(
                unit_trust_id=unit_trust_id,
                transaction_type=transaction_type,
                units=units,
                price_per_unit=price_per_unit,
                transaction_date=datetime.combine(
                    transaction_date, datetime.min.time(), tzinfo=timezone.utc
                ),
                notes=notes,
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

            # Fetch real prices from Yahoo Finance
            print('  - Fetching price history from Yahoo Finance...')
            prices = await fetch_price_history_from_yahoo(
                unit_trust.id, unit_trust.symbol, days=365
            )
            for price in prices:
                session.add(price)
            print(f'  - Added {len(prices)} price records')

            transactions = await generate_transactions(unit_trust.id, prices, count=12)
            for transaction in transactions:
                session.add(transaction)
            buy_count = sum(1 for t in transactions if t.transaction_type == 'buy')
            sell_count = sum(1 for t in transactions if t.transaction_type == 'sell')
            print(
                f'  - Added {len(transactions)} transactions ({buy_count} buys, {sell_count} sells)'
            )

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
