"""Test configuration and shared fixtures."""

from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from main import app

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine

TEST_DATABASE_URL = 'sqlite+aiosqlite:///:memory:'


@pytest_asyncio.fixture(scope='session')
async def test_engine() -> AsyncGenerator['AsyncEngine', None]:
    """Create test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture
async def test_db(test_engine: 'AsyncEngine') -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test."""
    async_session_maker = async_sessionmaker(
        test_engine, expire_on_commit=False, class_=AsyncSession
    )

    async with async_session_maker() as session:
        # Clear all tables before each test
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

        yield session


@pytest_asyncio.fixture
async def client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create FastAPI test client with database override."""

    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as ac:
        yield ac

    app.dependency_overrides.clear()
