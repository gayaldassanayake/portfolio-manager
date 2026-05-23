# Backend Architecture - Portfolio Manager

## Overview
FastAPI-based backend for managing unit trust portfolios. It uses SQLAlchemy with an asynchronous SQLite database (`aiosqlite`) and provides endpoints for managing unit trusts, prices, and transactions, as well as calculating portfolio performance metrics.

## Tech Stack
- **Framework:** FastAPI
- **Language:** Python 3.14+
- **Database:** SQLite (via SQLAlchemy + aiosqlite)
- **Validation:** Pydantic v2
- **Data Analysis:** NumPy, Pandas (used for financial calculations and time-series data)
- **Tooling:** `uv` for dependency management, `ruff` for linting/formatting, `pytest` for testing

## Project Structure
- `app/`: Core application logic
  - `api/`: FastAPI routers and endpoints
    - `portfolio.py`: Summary, performance metrics, and history endpoints
    - `prices.py`: Historical price management
    - `transactions.py`: Buy/Sell transaction management
    - `unit_trusts.py`: Unit trust CRUD and statistics
  - `models/`: SQLAlchemy database models
    - `unit_trust.py`: `UnitTrust` model (id, name, symbol, etc.)
    - `price.py`: `Price` model (id, unit_trust_id, date, price)
    - `transaction.py`: `Transaction` model (id, unit_trust_id, transaction_type, units, price_per_unit)
  - `schemas/`: Pydantic models for request/response validation
  - `services/`: Business logic and complex calculations
    - `performance.py`: `PerformanceService` for ROI, CAGR, Sharpe Ratio, and history calculations using Pandas/NumPy.
  - `database.py`: Database connection and session management (`get_db` dependency)
- `main.py`: Application entry point, router registration, CORS, and database initialization via lifespan events.
- `scripts/`: Utility scripts
  - `seed_db.py`: Database seeding logic (accessible via `uv run seed-db`)
- `tests/`: Test suite
  - `unit/`: Unit tests for services and schemas
  - `integration/`: Integration tests for API endpoints
  - `factories.py`: Model factories for testing

## Key Concepts
- **Unit Trust:** Investment products tracked by the system.
- **Price:** Historical daily prices for unit trusts.
- **Transaction:** Buy/Sell records for unit trusts. Net units are calculated as `sum(buy) - sum(sell)`.
- **Performance Metrics:** 
  - **ROI:** Return on Investment.
  - **Volatility:** Annualized standard deviation of daily returns.
  - **Sharpe Ratio:** Risk-adjusted return calculation.
  - **Max Drawdown:** Largest peak-to-trough decline.
  - **Annualized Return (CAGR):** Compound Annual Growth Rate.

## API Endpoints
- `GET /api/v1/unit-trusts`: List and manage investment products.
- `GET /api/v1/portfolio/summary`: High-level portfolio view (total invested, current value, total gain/loss).
- `GET /api/v1/portfolio/performance`: Detailed performance including history and metrics.
- `GET /api/v1/portfolio/history`: Time-series data of portfolio value.

## Development
### Setup
```bash
uv sync
```

### Running the server
```bash
uvicorn main:app --reload
```

### Seeding the database
```bash
uv run seed-db
```

### Testing
```bash
pytest
```

### Linting & Formatting
```bash
ruff check .
ruff format .
```
