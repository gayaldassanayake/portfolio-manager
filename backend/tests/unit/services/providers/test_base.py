"""Unit tests for provider base classes."""

from datetime import date

from app.services.providers.base import FetchedPrice, ProviderError


class TestFetchedPrice:
    """Tests for FetchedPrice dataclass."""

    def test_fetched_price_creation(self):
        """Test FetchedPrice can be created with date and price."""
        fp = FetchedPrice(date=date(2026, 1, 15), price=5.50)

        assert fp.date == date(2026, 1, 15)
        assert fp.price == 5.50

    def test_fetched_price_equality(self):
        """Test FetchedPrice equality comparison."""
        fp1 = FetchedPrice(date=date(2026, 1, 15), price=5.50)
        fp2 = FetchedPrice(date=date(2026, 1, 15), price=5.50)

        assert fp1 == fp2


class TestProviderError:
    """Tests for ProviderError exception."""

    def test_provider_error_message_format(self):
        """Test ProviderError formats message correctly."""
        error = ProviderError(provider='yahoo', symbol='AAPL', message='API rate limited')

        assert error.provider == 'yahoo'
        assert error.symbol == 'AAPL'
        assert error.message == 'API rate limited'
        assert str(error) == '[yahoo] Failed to fetch AAPL: API rate limited'

    def test_provider_error_is_exception(self):
        """Test ProviderError can be raised and caught."""
        try:
            raise ProviderError(provider='cal', symbol='TEST', message='Connection failed')
        except ProviderError as e:
            assert e.provider == 'cal'
            assert 'Connection failed' in str(e)
