"""Unit tests for provider registry."""

from app.services.providers.cal import CALProvider
from app.services.providers.registry import get_available_providers, get_provider
from app.services.providers.yahoo import YahooProvider


class TestProviderRegistry:
    """Tests for provider registry."""

    def test_get_provider_yahoo(self):
        """Test getting Yahoo provider by name."""
        provider = get_provider('yahoo')

        assert provider is not None
        assert isinstance(provider, YahooProvider)
        assert provider.name == 'yahoo'

    def test_get_provider_cal(self):
        """Test getting CAL provider by name."""
        provider = get_provider('cal')

        assert provider is not None
        assert isinstance(provider, CALProvider)
        assert provider.name == 'cal'

    def test_get_provider_unknown(self):
        """Test getting unknown provider returns None."""
        provider = get_provider('unknown_provider')

        assert provider is None

    def test_get_provider_case_insensitive(self):
        """Test provider lookup is case-insensitive."""
        provider_lower = get_provider('yahoo')
        provider_upper = get_provider('YAHOO')
        provider_mixed = get_provider('Yahoo')

        assert provider_lower is not None
        assert provider_upper is not None
        assert provider_mixed is not None
        # All should return the same provider instance
        assert provider_lower is provider_upper is provider_mixed

    def test_get_available_providers(self):
        """Test listing available providers."""
        providers = get_available_providers()

        assert isinstance(providers, list)
        assert 'yahoo' in providers
        assert 'cal' in providers
        assert len(providers) == 2
