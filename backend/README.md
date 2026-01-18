# Portfolio Management API

A FastAPI-based portfolio management system for unit trusts with performance tracking.

## Features

- Manage unit trusts (create, update, delete, list)
- Track historical prices for unit trusts
- Record buy transactions
- Portfolio performance metrics (ROI, volatility, annualized returns, max drawdown)
- Historical portfolio value tracking

## Tech Stack

- FastAPI - Async web framework
- SQLAlchemy 2.0 - Async ORM
- SQLite - Database (aiosqlite driver)
- Pydantic v2 - Data validation
- Pandas/NumPy - Performance calculations

## Installation

```bash
# Install dependencies
uv sync
```

## Running

```bash
# Development server
uv run uvicorn main:app --reload

# Production
uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

## Database Seeding

Generate sample data for development and testing:

```bash
# Seed database with sample unit trusts, prices, and transactions
uv run seed-db
```

This will create:
- 4 sample unit trusts
- 365 days of price history for each fund
- 12 sample transactions per fund

## Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=app --cov-report=term-missing

# Generate HTML coverage report
uv run pytest --cov=app --cov-report=html
# Open htmlcov/index.html in browser

# Run specific test file
uv run pytest tests/integration/test_unit_trusts.py

# Run specific test
uv run pytest tests/integration/test_unit_trusts.py::TestUnitTrustAPI::test_create_unit_trust_success
```

**Test Coverage:** 96% (430 statements, 18 missed)

## API Documentation

Interactive API documentation is available at `/docs` (Swagger UI) and `/redoc` (ReDoc).

## API Endpoints

### Unit Trusts

- `POST /api/v1/unit-trusts` - Create a new unit trust
- `GET /api/v1/unit-trusts` - List all unit trusts
- `GET /api/v1/unit-trusts/{id}` - Get unit trust details
- `PUT /api/v1/unit-trusts/{id}` - Update unit trust
- `DELETE /api/v1/unit-trusts/{id}` - Delete unit trust
- `GET /api/v1/unit-trusts/{id}/with-stats` - Get unit trust with holding statistics

### Prices

- `POST /api/v1/prices` - Add a price for a unit trust
- `GET /api/v1/prices` - List prices (with optional filters)
- `GET /api/v1/prices/{id}` - Get price details
- `PUT /api/v1/prices/{id}` - Update price
- `DELETE /api/v1/prices/{id}` - Delete price
- `POST /api/v1/prices/bulk` - Bulk import prices

### Transactions

- `POST /api/v1/transactions` - Record a buy transaction
- `GET /api/v1/transactions` - List transactions (with optional filters)
- `GET /api/v1/transactions/{id}` - Get transaction details
- `PUT /api/v1/transactions/{id}` - Update transaction
- `DELETE /api/v1/transactions/{id}` - Delete transaction

### Portfolio Performance

- `GET /api/v1/portfolio/summary` - Get portfolio summary (invested, value, gain/loss, ROI)
- `GET /api/v1/portfolio/performance` - Get full performance analysis
- `GET /api/v1/portfolio/history` - Get portfolio value history
- `GET /api/v1/portfolio/metrics` - Get performance metrics (volatility, returns, drawdown)

## Example Usage

### Create a Unit Trust

```bash
curl -X POST http://localhost:8000/api/v1/unit-trusts \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Vanguard S&P 500",
    "symbol": "VFIAX",
    "description": "S&P 500 Index Fund"
  }'
```

### Add Price Data

```bash
curl -X POST http://localhost:8000/api/v1/prices \
  -H "Content-Type: application/json" \
  -d '{
    "unit_trust_id": 1,
    "date": "2026-01-01T00:00:00",
    "price": 450.25
  }'
```

### Buy Units

```bash
curl -X POST http://localhost:8000/api/v1/transactions \
  -H "Content-Type: application/json" \
  -d '{
    "unit_trust_id": 1,
    "units": 10.5,
    "transaction_date": "2026-01-01T00:00:00"
  }'
```

### Get Portfolio Summary

```bash
curl http://localhost:8000/api/v1/portfolio/summary
```

## Performance Metrics

- **Total Invested**: Sum of all transaction amounts
- **Current Value**: Units held × latest price
- **Gain/Loss**: Current value - Total invested
- **ROI**: (Gain/Loss) / Total invested × 100
- **Daily Returns**: Day-over-day percentage changes
- **Volatility**: Annualized standard deviation of returns
- **Annualized Returns**: CAGR over holding period
- **Max Drawdown**: Largest peak-to-trough decline
- **Sharpe Ratio**: Risk-adjusted return measure
