"""One-off: populate buy/sell prices on existing QEF price rows.

CAL only quotes buy (creation) and sell (redemption) prices through the
``getUTPrices`` rolling ~90-day window, so this updates the rows that fall in
that window and leaves older backfilled rows (NAV-only) untouched.

Run from the backend directory:  uv run python scripts/backfill_qef_buy_sell.py
"""

import asyncio
from datetime import datetime

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.price import Price
from app.models.unit_trust import UnitTrust
from app.services.providers.cal import CALProvider


async def main() -> None:
    """Fetch the recent QEF series and write buy/sell onto matching rows."""
    async with AsyncSessionLocal() as db:
        ut = (
            await db.execute(select(UnitTrust).where(UnitTrust.symbol == 'QEF'))
        ).scalar_one()

        symbol = ut.provider_symbol or ut.symbol
        # The recent getUTPrices window is the only source of buy/sell prices.
        recent = await CALProvider()._fetch_recent_prices(symbol, symbol.upper())
        quoted = {fp.date: fp for fp in recent if fp.buy_price is not None or fp.sell_price is not None}

        rows = (
            await db.execute(select(Price).where(Price.unit_trust_id == ut.id))
        ).scalars().all()

        updated = 0
        for row in rows:
            d = row.date.date() if isinstance(row.date, datetime) else row.date
            fp = quoted.get(d)
            if fp is None:
                continue
            row.buy_price = fp.buy_price
            row.sell_price = fp.sell_price
            updated += 1

        await db.commit()
        print(f'QEF (id={ut.id}): {len(rows)} rows total, '
              f'{len(quoted)} dates quoted upstream, {updated} rows updated.')


if __name__ == '__main__':
    asyncio.run(main())
