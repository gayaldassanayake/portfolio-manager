"""Unit tests for Pydantic schema validation."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.schemas.portfolio import PerformanceMetrics, PortfolioHistory, PortfolioSummary
from app.schemas.price import PriceCreate, PriceResponse
from app.schemas.transaction import TransactionCreate, TransactionResponse
from app.schemas.unit_trust import UnitTrustCreate, UnitTrustResponse


class TestUnitTrustSchemas:
    """Test unit trust schema validation."""

    def test_unit_trust_create_valid(self):
        """Test valid unit trust creation data."""
        data = {'name': 'Test Fund', 'symbol': 'TEST', 'description': 'A test fund'}
        schema = UnitTrustCreate(**data)
        assert schema.name == 'Test Fund'
        assert schema.symbol == 'TEST'
        assert schema.description == 'A test fund'

    def test_unit_trust_create_without_description(self):
        """Test unit trust creation without optional description."""
        data = {'name': 'Test Fund', 'symbol': 'TEST'}
        schema = UnitTrustCreate(**data)
        assert schema.name == 'Test Fund'
        assert schema.symbol == 'TEST'
        assert schema.description is None

    def test_unit_trust_create_missing_required_fields(self):
        """Test unit trust creation fails with missing required fields."""
        with pytest.raises(ValidationError):
            UnitTrustCreate(name='Test')  # ty:ignore[missing-argument]

    def test_unit_trust_response_from_dict(self):
        """Test unit trust response model construction."""
        data = {
            'id': 1,
            'name': 'Test Fund',
            'symbol': 'TEST',
            'description': 'Test',
            'created_at': datetime.now(timezone.utc),
        }
        schema = UnitTrustResponse(**data)
        assert schema.id == 1
        assert schema.name == 'Test Fund'


class TestPriceSchemas:
    """Test price schema validation."""

    def test_price_create_valid(self):
        """Test valid price creation data."""
        data = {
            'unit_trust_id': 1,
            'date': datetime(2026, 1, 15, tzinfo=timezone.utc),
            'price': 100.50,
        }
        schema = PriceCreate(**data)
        assert schema.unit_trust_id == 1
        assert schema.price == 100.50

    def test_price_create_negative_price(self):
        """Test price creation with negative price (should be allowed by Pydantic)."""
        # Note: Business logic validation should happen in the API layer
        data = {
            'unit_trust_id': 1,
            'date': datetime.now(timezone.utc),
            'price': -10.0,
        }
        schema = PriceCreate(**data)
        assert schema.price == -10.0

    def test_price_response_from_dict(self):
        """Test price response model construction."""
        data = {
            'id': 1,
            'unit_trust_id': 1,
            'date': datetime(2026, 1, 15, tzinfo=timezone.utc),
            'price': 100.50,
            'created_at': datetime.now(timezone.utc),
        }
        schema = PriceResponse(**data)
        assert schema.id == 1
        assert schema.price == 100.50


class TestTransactionSchemas:
    """Test transaction schema validation."""

    def test_transaction_create_valid(self):
        """Test valid transaction creation data."""
        data = {
            'unit_trust_id': 1,
            'units': 10.5,
            'transaction_date': datetime(2026, 1, 15, tzinfo=timezone.utc),
        }
        schema = TransactionCreate(**data)
        assert schema.unit_trust_id == 1
        assert schema.units == 10.5

    def test_transaction_create_missing_fields(self):
        """Test transaction creation fails with missing required fields."""
        with pytest.raises(ValidationError):
            TransactionCreate(unit_trust_id=1)  # ty:ignore[missing-argument]

    def test_transaction_create_zero_units(self):
        """Test transaction creation with zero units (should be allowed)."""
        data = {
            'unit_trust_id': 1,
            'units': 0.0,
            'transaction_date': datetime.now(timezone.utc),
        }
        schema = TransactionCreate(**data)
        assert schema.units == 0.0

    def test_transaction_response_from_dict(self):
        """Test transaction response model construction."""
        data = {
            'id': 1,
            'unit_trust_id': 1,
            'units': 10.5,
            'price_per_unit': 100.0,
            'transaction_date': datetime(2026, 1, 15, tzinfo=timezone.utc),
            'created_at': datetime.now(timezone.utc),
        }
        schema = TransactionResponse(**data)
        assert schema.id == 1
        assert schema.units == 10.5
        assert schema.price_per_unit == 100.0


class TestPortfolioSchemas:
    """Test portfolio schema validation."""

    def test_portfolio_summary_from_dict(self):
        """Test portfolio summary model construction."""
        data = {
            'total_invested': 1000.0,
            'current_value': 1100.0,
            'total_gain_loss': 100.0,
            'roi_percentage': 10.0,
            'total_units': 10,
            'holding_count': 1,
        }
        schema = PortfolioSummary(**data)
        assert schema.total_invested == 1000.0
        assert schema.roi_percentage == 10.0

    def test_performance_metrics_from_dict(self):
        """Test performance metrics model construction."""
        data = {
            'daily_return': 0.01,
            'volatility': 0.15,
            'annualized_return': 0.12,
            'max_drawdown': -0.05,
            'sharpe_ratio': 1.5,
        }
        schema = PerformanceMetrics(**data)
        assert schema.daily_return == 0.01
        assert schema.volatility == 0.15
        assert schema.sharpe_ratio == 1.5

    def test_performance_metrics_sharpe_ratio_none(self):
        """Test performance metrics with None Sharpe ratio."""
        data = {
            'daily_return': 0.0,
            'volatility': 0.0,
            'annualized_return': 0.0,
            'max_drawdown': 0.0,
            'sharpe_ratio': None,
        }
        schema = PerformanceMetrics(**data)
        assert schema.sharpe_ratio is None

    def test_portfolio_history_from_dict(self):
        """Test portfolio history model construction."""
        data = {'date': datetime(2026, 1, 15, tzinfo=timezone.utc), 'value': 1000.0}
        schema = PortfolioHistory(**data)
        assert schema.value == 1000.0
        assert isinstance(schema.date, datetime)
