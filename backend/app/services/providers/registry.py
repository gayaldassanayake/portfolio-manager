"""Provider registry for looking up price providers by name."""

from app.services.providers.base import PriceProvider
from app.services.providers.cal import CALProvider
from app.services.providers.yahoo import YahooProvider

# Registry of available providers
_PROVIDERS: dict[str, PriceProvider] = {
    'yahoo': YahooProvider(),
    'cal': CALProvider(),
}


def get_provider(name: str) -> PriceProvider | None:
    """Get a provider by name.

    Args:
        name: Provider name (case-insensitive).

    Returns:
        Provider instance or None if not found.

    """
    return _PROVIDERS.get(name.lower())


def get_available_providers() -> list[str]:
    """Get list of available provider names.

    Returns:
        List of provider names.

    """
    return list(_PROVIDERS.keys())
