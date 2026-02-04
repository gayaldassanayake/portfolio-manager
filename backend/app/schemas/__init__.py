"""Pydantic schemas package."""

from app.schemas.portfolio import (
    PerformanceMetrics,
    PortfolioHistory,
    PortfolioPerformance,
    PortfolioSummary,
)
from app.schemas.price import PriceCreate, PriceResponse, PriceUpdate
from app.schemas.providers.cal_api import CALPriceEntry, CALPricesResponse
from app.schemas.transaction import (
    TransactionCreate,
    TransactionResponse,
    TransactionUpdate,
    TransactionWithUnitTrust,
)
from app.schemas.unit_trust import (
    UnitTrustCreate,
    UnitTrustResponse,
    UnitTrustUpdate,
    UnitTrustWithStats,
)

__all__ = [
    'UnitTrustCreate',
    'UnitTrustResponse',
    'UnitTrustUpdate',
    'UnitTrustWithStats',
    'PriceCreate',
    'PriceResponse',
    'PriceUpdate',
    'TransactionCreate',
    'TransactionResponse',
    'TransactionUpdate',
    'TransactionWithUnitTrust',
    'PortfolioSummary',
    'PerformanceMetrics',
    'PortfolioHistory',
    'PortfolioPerformance',
    'CALPriceEntry',
    'CALPricesResponse',
]
