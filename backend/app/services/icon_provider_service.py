"""
Icon Provider Service - Multi-provider abstraction for merchant/payee icons.

Supports multiple icon providers:
- Simple Icons (default): CDN-based brand logos from simple-icons.org
- Logo.dev: Commercial logo API with domain/name/ticker lookups

Users can configure their preferred provider via user preferences.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Optional
from sqlalchemy.orm import Session

from app.core.config import settings


class IconProvider(str, Enum):
    """Available icon providers."""
    SIMPLE_ICONS = "simple_icons"
    LOGO_DEV = "logo_dev"


@dataclass
class IconResult:
    """Result from an icon provider lookup."""
    icon_type: str  # "url", "simple_icon", "emoji"
    icon_value: str  # The URL, CDN path, or emoji character
    provider: str  # Which provider returned this result
    requires_attribution: bool  # Whether attribution is required (logo.dev free tier)
    confidence: float = 1.0  # Match confidence
    brand_color: Optional[str] = None  # Hex color if available


class IconProviderService:
    """
    Service for resolving icons from multiple providers.

    Supports:
    - Simple Icons CDN (free, no API key required)
    - Logo.dev API (requires API key, free tier has attribution requirement)

    Provider priority is based on user preference:
    - If preference is "logo_dev" and configured: logo.dev -> Simple Icons -> emoji
    - If preference is "simple_icons": Simple Icons -> emoji

    The Logo.dev API key can be configured either:
    1. Via environment variable (LOGO_DEV_API_KEY)
    2. Via the app_settings database table (takes precedence)
    """

    SIMPLE_ICONS_CDN = "https://cdn.simpleicons.org"
    LOGO_DEV_CDN = "https://img.logo.dev"

    def __init__(self, db: Optional[Session] = None):
        """
        Initialize the service.

        Args:
            db: Optional database session. If provided, will check DB for API key.
                If not provided, will only use environment variable.
        """
        self._db = db
        self._logo_dev_api_key = self._get_logo_dev_api_key()
        self._logo_dev_enabled = self._logo_dev_api_key is not None

    def _get_logo_dev_api_key(self) -> Optional[str]:
        """
        Get Logo.dev API key, checking DB first then falling back to env var.
        """
        # First try to get from database if we have a session
        if self._db is not None:
            from app.services.app_settings_service import get_logo_dev_api_key_from_db
            db_key = get_logo_dev_api_key_from_db(self._db)
            if db_key:
                return db_key

        # Fall back to environment variable
        return settings.LOGO_DEV_API_KEY

    @property
    def logo_dev_available(self) -> bool:
        """Check if Logo.dev is configured and available."""
        return self._logo_dev_enabled

    @property
    def logo_dev_requires_attribution(self) -> bool:
        """
        Check if Logo.dev usage requires attribution.

        Free tier (500K requests/month) requires attribution.
        Paid tier ($280/year) does not require attribution.

        For now, we assume free tier and require attribution.
        This could be configurable in the future.
        """
        return True  # Assume free tier for now

    def get_icon_provider_status(self) -> dict:
        """
        Get the status of available icon providers.

        Returns information about which providers are available
        and their configuration status.
        """
        return {
            "providers": {
                "simple_icons": {
                    "available": True,
                    "requires_api_key": False,
                    "requires_attribution": False,
                    "description": "Open source brand logos from Simple Icons",
                },
                "logo_dev": {
                    "available": self.logo_dev_available,
                    "requires_api_key": True,
                    "requires_attribution": self.logo_dev_requires_attribution,
                    "description": "High-quality logos from Logo.dev API",
                },
            },
            "default_provider": IconProvider.SIMPLE_ICONS.value,
        }

    def get_simple_icons_url(
        self,
        slug: str,
        color: Optional[str] = None,
    ) -> IconResult:
        """
        Get icon URL from Simple Icons CDN.

        Args:
            slug: The Simple Icons slug (e.g., "amazon", "chase")
            color: Optional hex color (without #)

        Returns:
            IconResult with the CDN URL
        """
        if color:
            url = f"{self.SIMPLE_ICONS_CDN}/{slug}/{color}"
        else:
            url = f"{self.SIMPLE_ICONS_CDN}/{slug}"

        return IconResult(
            icon_type="url",
            icon_value=url,
            provider=IconProvider.SIMPLE_ICONS.value,
            requires_attribution=False,
            brand_color=f"#{color}" if color else None,
        )

    def get_logo_dev_url(
        self,
        domain: Optional[str] = None,
        name: Optional[str] = None,
        ticker: Optional[str] = None,
        size: int = 128,
        format: str = "png",
    ) -> Optional[IconResult]:
        """
        Get icon URL from Logo.dev API.

        Logo.dev primarily uses domain-based lookups:
        - Domain: The primary method - uses company domain (e.g., "chase.com")
        - Ticker: Stock ticker lookup (e.g., "JPM") - may not be supported
        - Name: Company name lookup - NOT SUPPORTED by Logo.dev API

        NOTE: Logo.dev only reliably supports domain-based lookups.
        The name parameter is kept for API compatibility but will generate
        URLs that may return 404 errors. Always prefer domain lookups.

        Args:
            domain: Company domain (e.g., "amazon.com") - RECOMMENDED
            name: Company name (NOT SUPPORTED - may return 404)
            ticker: Stock ticker for ticker-based lookup
            size: Image size in pixels
            format: Image format (png, jpg, webp)

        Returns:
            IconResult with the Logo.dev URL, or None if not configured
        """
        if not self.logo_dev_available:
            return None

        # Build the URL based on lookup type
        if domain:
            # Domain lookup - most reliable
            url = f"{self.LOGO_DEV_CDN}/{domain}"
        elif ticker:
            # Ticker lookup
            url = f"{self.LOGO_DEV_CDN}/ticker/{ticker}"
        elif name:
            # Name lookup
            # URL-encode the name for the path
            import urllib.parse
            encoded_name = urllib.parse.quote(name)
            url = f"{self.LOGO_DEV_CDN}/name/{encoded_name}"
        else:
            return None

        # Add query parameters
        params = {
            "token": self._logo_dev_api_key,
            "size": size,
            "format": format,
        }
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        full_url = f"{url}?{query_string}"

        return IconResult(
            icon_type="url",
            icon_value=full_url,
            provider=IconProvider.LOGO_DEV.value,
            requires_attribution=self.logo_dev_requires_attribution,
        )

    def get_icon(
        self,
        payee_name: str,
        simple_icons_slug: Optional[str] = None,
        simple_icons_color: Optional[str] = None,
        logo_dev_domain: Optional[str] = None,
        logo_dev_ticker: Optional[str] = None,
        user_preference: str = IconProvider.SIMPLE_ICONS.value,
        fallback_emoji: Optional[str] = None,
    ) -> IconResult:
        """
        Get the best available icon for a payee based on user preference.

        This method implements a fallback chain based on user preference:

        If preference is "logo_dev" (and logo.dev is configured):
            1. Try logo.dev with domain
            2. Try logo.dev with ticker
            3. Try logo.dev with name lookup
            4. Fall back to Simple Icons if slug available
            5. Fall back to emoji

        If preference is "simple_icons" (default):
            1. Try Simple Icons if slug available
            2. Fall back to emoji

        Args:
            payee_name: The payee name (used for name-based lookups)
            simple_icons_slug: Optional Simple Icons slug
            simple_icons_color: Optional hex color for Simple Icons
            logo_dev_domain: Optional domain for Logo.dev
            logo_dev_ticker: Optional ticker for Logo.dev
            user_preference: User's preferred provider ("simple_icons" or "logo_dev")
            fallback_emoji: Optional emoji to use as final fallback

        Returns:
            IconResult from the first successful provider
        """
        # Logo.dev preferred
        if user_preference == IconProvider.LOGO_DEV.value and self.logo_dev_available:
            # Try logo.dev with domain
            if logo_dev_domain:
                result = self.get_logo_dev_url(domain=logo_dev_domain)
                if result:
                    return result

            # Try logo.dev with ticker
            if logo_dev_ticker:
                result = self.get_logo_dev_url(ticker=logo_dev_ticker)
                if result:
                    return result

            # Try logo.dev with name lookup (less reliable but worth trying)
            result = self.get_logo_dev_url(name=payee_name)
            if result:
                result.confidence = 0.7  # Lower confidence for name lookup
                return result

        # Simple Icons (default or fallback from logo.dev)
        if simple_icons_slug:
            return self.get_simple_icons_url(
                slug=simple_icons_slug,
                color=simple_icons_color,
            )

        # Final fallback: emoji
        emoji = fallback_emoji or "🏢"  # Default to building emoji
        return IconResult(
            icon_type="emoji",
            icon_value=f"emoji:{emoji}",
            provider="fallback",
            requires_attribution=False,
            confidence=0.5,
        )


# Singleton instance (for non-DB usage)
_icon_provider_service: Optional[IconProviderService] = None


def get_icon_provider_service(db: Optional[Session] = None) -> IconProviderService:
    """
    Get an IconProviderService instance.

    Args:
        db: Optional database session. If provided, creates a new service
            that can check the database for API keys. If not provided,
            returns a singleton instance that only uses env vars.

    Returns:
        IconProviderService instance
    """
    global _icon_provider_service

    # If a DB session is provided, create a fresh instance to check DB
    if db is not None:
        return IconProviderService(db)

    # Otherwise use singleton (no DB access)
    if _icon_provider_service is None:
        _icon_provider_service = IconProviderService()
    return _icon_provider_service
