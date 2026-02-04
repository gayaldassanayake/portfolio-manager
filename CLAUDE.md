# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Portfolio Manager is a full-stack application for tracking unit trust investments with performance analytics. It consists of a FastAPI backend and React + TypeScript frontend.

## Architecture

### Backend (FastAPI + SQLAlchemy)

The backend follows a layered architecture:

- **`main.py`**: FastAPI app setup, CORS middleware, router registration, lifespan events for DB initialization
- **`app/database.py`**: Async SQLAlchemy engine configuration (SQLite with aiosqlite driver)
- **`app/models/`**: SQLAlchemy ORM models (UnitTrust, Transaction, Price)
- **`app/schemas/`**: Pydantic v2 schemas for request/response validation
- **`app/api/`**: FastAPI route handlers organized by resource:
  - `unit_trusts.py` - CRUD operations for funds
  - `transactions.py` - Buy transaction management
  - `prices.py` - Price data CRUD and bulk price fetching from providers
  - `portfolio.py` - Portfolio summary, performance metrics, and history
- **`app/services/`**: Business logic layer
  - `performance.py` - Portfolio analytics (ROI, volatility, Sharpe ratio, max drawdown)
  - `providers/` - Price provider abstraction:
    - `base.py` - Abstract `PriceProvider` class and `FetchedPrice` dataclass
    - `registry.py` - Provider registration system
    - `yahoo.py`, `cal.py` - Concrete provider implementations

**Key patterns:**
- All database operations use async/await with SQLAlchemy 2.0 async API
- Dependency injection via FastAPI's `Depends()` for database sessions
- API endpoints return flattened transaction data (includes `unit_trust_name`, `unit_trust_symbol`) to reduce frontend joins
- Price providers are registered in the registry and selected per unit trust via `price_provider_name` field

### Frontend (React + Vite + TypeScript)

Component structure follows atomic design principles:

- **`api/`**: API client and React Query hooks
  - `client.ts` - Typed fetch wrapper with error handling, exports `api` object
  - `hooks/` - Custom hooks using `@tanstack/react-query` (useUnitTrusts, useTransactions, usePortfolio, etc.)
- **`components/`**:
  - `ui/` - Primitive components (Button, Input, Card, Table, Modal, Badge)
  - `layout/` - App structure (AppShell, Sidebar, PageHeader)
  - `features/` - Business components (StatCard, UnitTrustFormModal, FetchPricesModal)
  - `charts/` - Data visualization (PortfolioChart using recharts)
- **`pages/`**: Route-level components (Dashboard, Holdings, Performance, FundDetails, Transactions)
- **`lib/`**: Utility functions (formatters for currency/percentage/dates, `cn` helper)
- **`types/`**: TypeScript type definitions matching backend schemas

**Key patterns:**
- CSS Modules for component-scoped styling (`.module.css` files)
- React Query for server state management (caching, refetching, optimistic updates)
- Motion library (formerly Framer Motion) for animations
- Environment variable `VITE_API_URL` for API base URL (defaults to `http://localhost:8000/api/v1`)
- All API responses are typed, backend transaction responses are transformed from flattened to nested format in `api/client.ts`

## Common Development Commands

### Backend

All backend commands should be run from the `backend/` directory using `uv`:

```bash
# Start development server
uv run uvicorn main:app --reload

# Run all tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=app --cov-report=term-missing

# Run specific test file
uv run pytest tests/integration/test_unit_trusts.py

# Run specific test method
uv run pytest tests/integration/test_unit_trusts.py::TestUnitTrustAPI::test_create_unit_trust_success

# Seed database with sample data
uv run seed-db

# Code formatting and linting (ruff)
uv run ruff format .
uv run ruff check .
```

**Important:** The backend uses Python 3.14+ and requires `uv` package manager. All dependencies are in `pyproject.toml`.

### Frontend

All frontend commands should be run from the `frontend/` directory using `npm`:

```bash
# Start development server (runs on http://localhost:5173)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run linter
npm run lint
```

## Database

- **Type**: SQLite (async via aiosqlite)
- **Location**: `backend/portfolio.db`
- **Schema**: Automatically created on app startup via SQLAlchemy metadata
- **Migrations**: Not currently using Alembic - schema changes are made directly to models

## Testing Strategy

- Backend tests are in `backend/tests/` split into `unit/` and `integration/`
- Integration tests use `conftest.py` fixtures for test database setup
- Test factories are in `tests/factories.py` for generating test data
- Current coverage: 96%
- Tests use pytest with pytest-asyncio for async test support

## API Conventions

- All endpoints prefixed with `/api/v1/`
- RESTful resource naming (plural nouns)
- Transaction list endpoint returns flattened data with `unit_trust_name` and `unit_trust_symbol` fields
- Error responses follow FastAPI's standard format with `detail` field
- Dates are ISO 8601 format strings
- CORS is enabled for all origins (configured in `main.py`)

## Price Provider System

Unit trusts can specify a `price_provider_name` (e.g., "yahoo", "cal") to fetch historical prices. Providers implement the `PriceProvider` abstract base class and are registered in `services/providers/registry.py`. The `/prices/fetch` endpoint supports bulk fetching for multiple funds.
