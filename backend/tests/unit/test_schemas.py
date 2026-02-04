"""Unit tests for Pydantic schema validation."""

from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.portfolio import PerformanceMetrics, PortfolioHistory, PortfolioSummary
from app.schemas.price import PriceCreate, PriceResponse
from app.schemas.providers.cal_api import CALPriceEntry, CALPricesResponse
from app.schemas.transaction import TransactionCreate, TransactionResponse
from app.schemas.unit_trust import UnitTrustCreate, UnitTrustResponse, UnitTrustUpdate


class TestUnitTrustSchemas:
    """Test unit trust schema validation."""

    def test_unit_trust_create_valid(self):
        """Test valid unit trust creation data."""
        schema = UnitTrustCreate(
            name='Test Fund',
            symbol='TEST',
            description='A test fund',
        )
        assert schema.name == 'Test Fund'
        assert schema.symbol == 'TEST'
        assert schema.description == 'A test fund'

    def test_unit_trust_create_without_description(self):
        """Test unit trust creation without optional description."""
        schema = UnitTrustCreate(
            name='Test Fund',
            symbol='TEST',
        )
        assert schema.name == 'Test Fund'
        assert schema.symbol == 'TEST'
        assert schema.description is None

    def test_unit_trust_create_missing_required_fields(self):
        """Test unit trust creation fails with missing required fields."""
        with pytest.raises(ValidationError):
            UnitTrustCreate(name='Test')  # ty:ignore[missing-argument]

    def test_unit_trust_response_from_dict(self):
        """Test unit trust response model construction."""
        schema = UnitTrustResponse(
            id=1,
            name='Test Fund',
            symbol='TEST',
            description='Test',
            created_at=datetime.now(timezone.utc),
        )
        assert schema.id == 1
        assert schema.name == 'Test Fund'

    def test_unit_trust_create_with_valid_provider(self):
        """Test unit trust creation with valid provider values."""
        # Test 'yahoo' provider
        schema_yahoo = UnitTrustCreate(
            name='Yahoo Fund',
            symbol='YHOO',
            provider='yahoo',
        )
        assert schema_yahoo.provider == 'yahoo'

        # Test 'cal' provider
        schema_cal = UnitTrustCreate(
            name='CAL Fund',
            symbol='CAL',
            provider='cal',
        )
        assert schema_cal.provider == 'cal'

    def test_unit_trust_create_with_invalid_provider(self):
        """Test unit trust creation fails with invalid provider."""
        with pytest.raises(ValidationError) as exc_info:
            UnitTrustCreate(
                name='Invalid Fund',
                symbol='INV',
                provider='invalid_provider',  # ty:ignore[invalid-argument-type]
            )
        # Check error mentions the invalid value
        assert 'provider' in str(exc_info.value).lower()

    def test_unit_trust_create_with_provider_symbol(self):
        """Test unit trust creation with provider_symbol."""
        schema = UnitTrustCreate(
            name='Test Fund',
            symbol='INTERNAL',
            provider='yahoo',
            provider_symbol='EXTERNAL',
        )
        assert schema.symbol == 'INTERNAL'
        assert schema.provider_symbol == 'EXTERNAL'

    def test_unit_trust_update_with_provider(self):
        """Test unit trust update with provider field."""
        schema = UnitTrustUpdate(provider='cal')
        assert schema.provider == 'cal'
        assert schema.name is None
        assert schema.symbol is None

    def test_unit_trust_update_with_invalid_provider(self):
        """Test unit trust update fails with invalid provider."""
        with pytest.raises(ValidationError):
            UnitTrustUpdate(provider='not_a_provider')  # ty:ignore[invalid-argument-type]


class TestPriceSchemas:
    """Test price schema validation."""

    def test_price_create_valid(self):
        """Test valid price creation data."""
        schema = PriceCreate(
            unit_trust_id=1,
            date=datetime(2026, 1, 15, tzinfo=timezone.utc),
            price=100.50,
        )
        assert schema.unit_trust_id == 1
        assert schema.price == 100.50

    def test_price_create_negative_price(self):
        """Test price creation with negative price (should be allowed by Pydantic)."""
        # Note: Business logic validation should happen in the API layer
        schema = PriceCreate(
            unit_trust_id=1,
            date=datetime.now(timezone.utc),
            price=-10.0,
        )
        assert schema.price == -10.0

    def test_price_response_from_dict(self):
        """Test price response model construction."""
        schema = PriceResponse(
            id=1,
            unit_trust_id=1,
            date=datetime(2026, 1, 15, tzinfo=timezone.utc),
            price=100.50,
            created_at=datetime.now(timezone.utc),
        )
        assert schema.id == 1
        assert schema.price == 100.50


class TestTransactionSchemas:
    """Test transaction schema validation."""

    def test_transaction_create_valid(self):
        """Test valid transaction creation data."""
        schema = TransactionCreate(
            unit_trust_id=1,
            units=10.5,
            transaction_date=datetime(2026, 1, 15, tzinfo=timezone.utc),
        )
        assert schema.unit_trust_id == 1
        assert schema.units == 10.5

    def test_transaction_create_missing_fields(self):
        """Test transaction creation fails with missing required fields."""
        with pytest.raises(ValidationError):
            TransactionCreate(unit_trust_id=1)  # ty:ignore[missing-argument]

    def test_transaction_create_zero_units(self):
        """Test transaction creation with zero units (should fail validation)."""
        with pytest.raises(ValueError):
            TransactionCreate(
                unit_trust_id=1,
                units=0.0,
                transaction_date=datetime.now(timezone.utc),
            )

    def test_transaction_response_from_dict(self):
        """Test transaction response model construction."""
        schema = TransactionResponse(
            id=1,
            unit_trust_id=1,
            transaction_type='buy',
            units=10.5,
            price_per_unit=100.0,
            transaction_date=datetime(2026, 1, 15, tzinfo=timezone.utc),
            notes='Test note',
            created_at=datetime.now(timezone.utc),
        )
        assert schema.id == 1
        assert schema.units == 10.5
        assert schema.price_per_unit == 100.0
        assert schema.transaction_type == 'buy'
        assert schema.notes == 'Test note'


class TestPortfolioSchemas:
    """Test portfolio schema validation."""

    def test_portfolio_summary_from_dict(self):
        """Test portfolio summary model construction."""
        schema = PortfolioSummary(
            total_invested=1000.0,
            current_value=1100.0,
            total_gain_loss=100.0,
            roi_percentage=10.0,
            total_units=10,
            holding_count=1,
        )
        assert schema.total_invested == 1000.0
        assert schema.roi_percentage == 10.0

    def test_performance_metrics_from_dict(self):
        """Test performance metrics model construction."""
        schema = PerformanceMetrics(
            daily_return=0.01,
            volatility=0.15,
            annualized_return=0.12,
            max_drawdown=-0.05,
            sharpe_ratio=1.5,
        )
        assert schema.daily_return == 0.01
        assert schema.volatility == 0.15
        assert schema.annualized_return == 0.12
        assert schema.sharpe_ratio == 1.5

    def test_performance_metrics_sharpe_ratio_none(self):
        """Test performance metrics with None Sharpe ratio."""
        schema = PerformanceMetrics(
            daily_return=0.0,
            volatility=0.0,
            annualized_return=0.0,
            max_drawdown=0.0,
            sharpe_ratio=None,
        )
        assert schema.sharpe_ratio is None

    def test_portfolio_history_from_dict(self):
        """Test portfolio history model construction."""
        schema = PortfolioHistory(
            date=datetime(2026, 1, 15, tzinfo=timezone.utc),
            value=1000.0,
        )
        assert schema.value == 1000.0
        assert isinstance(schema.date, datetime)


class TestCALAPISchemas:
    """Test CAL API schema validation."""

    def test_cal_price_entry_valid(self):
        """Test valid CAL price entry parsing."""
        entry = CALPriceEntry.model_validate(
            {
                'date': '2026-02-01',
                'unit_price': '39.1854000000',
            }
        )
        assert entry.date == date(2026, 2, 1)
        assert entry.unit_price == Decimal('39.1854000000')
        assert entry.red_price is None
        assert entry.cre_price is None

    def test_cal_price_entry_with_all_prices(self):
        """Test CAL price entry with redemption and creation prices."""
        entry = CALPriceEntry.model_validate(
            {
                'date': '2026-02-01',
                'unit_price': '25.5000',
                'red_price': '25.3750',
                'cre_price': '25.6250',
            }
        )
        assert entry.unit_price == Decimal('25.5000')
        assert entry.red_price == Decimal('25.3750')
        assert entry.cre_price == Decimal('25.6250')

    def test_cal_price_entry_decimal_parsing(self):
        """Test that string prices are correctly parsed to Decimal."""
        entry = CALPriceEntry.model_validate(
            {
                'date': '2026-02-01',
                'unit_price': '100.123456789',
            }
        )
        assert isinstance(entry.unit_price, Decimal)
        assert entry.unit_price == Decimal('100.123456789')

    def test_cal_price_entry_invalid_unit_price(self):
        """Test validation error for missing unit_price."""
        with pytest.raises(ValidationError) as exc_info:
            CALPriceEntry.model_validate(
                {
                    'date': '2026-02-01',
                    'unit_price': None,  # Should fail - unit_price is required
                }
            )
        assert 'unit_price' in str(exc_info.value).lower()

    def test_cal_price_entry_zero_unit_price(self):
        """Test validation error for zero unit_price."""
        with pytest.raises(ValidationError) as exc_info:
            CALPriceEntry.model_validate(
                {
                    'date': '2026-02-01',
                    'unit_price': '0.0',  # Should fail - gt=0 constraint
                }
            )
        assert 'unit_price' in str(exc_info.value).lower()

    def test_cal_price_entry_negative_unit_price(self):
        """Test validation error for negative unit_price."""
        with pytest.raises(ValidationError) as exc_info:
            CALPriceEntry.model_validate(
                {
                    'date': '2026-02-01',
                    'unit_price': '-10.5',  # Should fail - gt=0 constraint
                }
            )
        assert 'unit_price' in str(exc_info.value).lower()

    def test_cal_price_entry_empty_string_optional_prices(self):
        """Test that empty strings for optional prices become None."""
        entry = CALPriceEntry.model_validate(
            {
                'date': '2026-02-01',
                'unit_price': '39.00',
                'red_price': '',
                'cre_price': '',
            }
        )

        assert entry.red_price is None
        assert entry.cre_price is None

    def test_cal_prices_response_valid(self):
        """Test valid CAL prices response parsing."""
        response_data = {
            'IGF': [
                {
                    'date': '2026-02-01',
                    'unit_price': '39.1854000000',
                    'red_price': None,
                    'cre_price': None,
                },
                {
                    'date': '2026-02-02',
                    'unit_price': '39.2100000000',
                    'red_price': None,
                    'cre_price': None,
                },
            ]
        }
        response = CALPricesResponse.model_validate(response_data)
        assert 'IGF' in response.root
        assert len(response.root['IGF']) == 2
        assert response.root['IGF'][0].unit_price == Decimal('39.1854000000')

    def test_cal_prices_response_multiple_funds(self):
        """Test CAL prices response with multiple funds."""
        response_data = {
            'IGF': [
                {'date': '2026-02-01', 'unit_price': '39.00', 'red_price': None, 'cre_price': None}
            ],
            'QEF': [
                {'date': '2026-02-01', 'unit_price': '25.50', 'red_price': None, 'cre_price': None}
            ],
        }
        response = CALPricesResponse.model_validate(response_data)
        assert len(response.root) == 2
        assert 'IGF' in response.root
        assert 'QEF' in response.root

    def test_cal_prices_response_empty_array(self):
        """Test CAL prices response with empty price array."""
        response_data = {'IGF': []}
        response = CALPricesResponse.model_validate(response_data)
        assert 'IGF' in response.root
        assert len(response.root['IGF']) == 0

    def test_cal_prices_response_invalid_structure(self):
        """Test validation error for invalid response structure."""
        with pytest.raises(ValidationError):
            # Not a dict
            CALPricesResponse.model_validate(['invalid'])

    def test_cal_price_entry_invalid_date_format(self):
        """Test validation error for invalid date format."""
        with pytest.raises(ValidationError):
            CALPriceEntry.model_validate(
                {
                    'date': 'not-a-date',
                    'unit_price': '39.00',
                }
            )
