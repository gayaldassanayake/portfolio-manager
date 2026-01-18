"""Main application module for Portfolio Management API."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.portfolio import router as portfolio_router
from app.api.prices import router as prices_router
from app.api.transactions import router as transactions_router
from app.api.unit_trusts import router as unit_trusts_router
from app.database import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events.

    Creates database tables on startup.

    Args:
        app: FastAPI application instance.

    Yields:
        None

    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title='Portfolio Management API',
    description='API for managing unit trust portfolios and tracking performance',
    version='0.1.0',
    lifespan=lifespan,
)

app.include_router(unit_trusts_router)
app.include_router(prices_router)
app.include_router(transactions_router)
app.include_router(portfolio_router)


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
