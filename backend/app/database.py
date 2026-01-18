"""Database configuration and session management."""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = 'sqlite+aiosqlite:///./portfolio.db'


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


engine = create_async_engine(DATABASE_URL, echo=False)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency injection for database sessions.

    Yields:
        AsyncSession: Database session.

    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
