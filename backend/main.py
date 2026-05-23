"""Main application module for Portfolio Management API."""

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from alembic.config import Config
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from alembic import command
from app.api.fixed_deposits import router as fixed_deposits_router
from app.api.notifications import router as notifications_router
from app.api.portfolio import router as portfolio_router
from app.api.prices import router as prices_router
from app.api.transactions import router as transactions_router
from app.api.unit_trusts import router as unit_trusts_router


def _run_migrations() -> None:
    """Upgrade the database to the latest Alembic revision.

    Runs synchronously (Alembic manages its own event loop), so callers must
    invoke it from a worker thread, never the running async loop.
    """
    config = Config(str(Path(__file__).parent / 'alembic.ini'))
    command.upgrade(config, 'head')


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events.

    Applies any pending database migrations on startup.

    Args:
        app: FastAPI application instance.

    Yields:
        None

    """
    await asyncio.to_thread(_run_migrations)
    yield


app = FastAPI(
    title='Portfolio Management API',
    description='API for managing unit trust portfolios and tracking performance',
    version='0.1.0',
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(unit_trusts_router)
app.include_router(prices_router)
app.include_router(transactions_router)
app.include_router(portfolio_router)
app.include_router(fixed_deposits_router)
app.include_router(notifications_router)


@app.get('/')
async def root():
    """Get API root information.

    Returns:
        dict: API message, documentation URL, and version.

    """
    return {
        'message': 'Portfolio Management API',
        'docs': '/docs',
        'version': '0.1.0',
    }


@app.get('/health')
async def health():
    """Health check endpoint.

    Returns:
        dict: Health status.

    """
    return {'status': 'healthy'}
