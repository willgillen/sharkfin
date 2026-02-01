"""Tests for IconProviderService."""
import pytest
from unittest.mock import patch, MagicMock

from app.services.icon_provider_service import (
    IconProviderService,
    IconProvider,
    IconResult,
    get_icon_provider_service,
)


class TestIconProviderService:
    """Tests for IconProviderService."""

    def test_simple_icons_url_with_color(self):
        """Test generating Simple Icons URL with color."""
        service = IconProviderService()
        result = service.get_simple_icons_url("amazon", "FF9900")

        assert result.icon_type == "url"
        assert result.icon_value == "https://cdn.simpleicons.org/amazon/FF9900"
        assert result.provider == "simple_icons"
        assert result.requires_attribution is False
        assert result.brand_color == "#FF9900"

    def test_simple_icons_url_without_color(self):
        """Test generating Simple Icons URL without color."""
        service = IconProviderService()
        result = service.get_simple_icons_url("chase")

        assert result.icon_type == "url"
        assert result.icon_value == "https://cdn.simpleicons.org/chase"
        assert result.provider == "simple_icons"
        assert result.brand_color is None

    def test_logo_dev_not_available_without_api_key(self):
        """Test that logo.dev is not available without API key."""
        with patch("app.services.icon_provider_service.settings") as mock_settings:
            mock_settings.LOGO_DEV_API_KEY = None
            mock_settings.logo_dev_enabled = False

            service = IconProviderService()
            assert service.logo_dev_available is False

    def test_logo_dev_available_with_api_key(self):
        """Test that logo.dev is available with API key."""
        with patch("app.services.icon_provider_service.settings") as mock_settings:
            mock_settings.LOGO_DEV_API_KEY = "test_api_key"
            mock_settings.logo_dev_enabled = True

            service = IconProviderService()
            assert service.logo_dev_available is True

    def test_logo_dev_url_with_domain(self):
        """Test generating Logo.dev URL with domain."""
        with patch("app.services.icon_provider_service.settings") as mock_settings:
            mock_settings.LOGO_DEV_API_KEY = "test_key"
            mock_settings.logo_dev_enabled = True

            service = IconProviderService()
            result = service.get_logo_dev_url(domain="chase.com")

            assert result is not None
            assert result.icon_type == "url"
            assert "img.logo.dev/chase.com" in result.icon_value
            assert "token=test_key" in result.icon_value
            assert result.provider == "logo_dev"
            assert result.requires_attribution is True

    def test_logo_dev_url_with_ticker(self):
        """Test generating Logo.dev URL with stock ticker."""
        with patch("app.services.icon_provider_service.settings") as mock_settings:
            mock_settings.LOGO_DEV_API_KEY = "test_key"
            mock_settings.logo_dev_enabled = True

            service = IconProviderService()
            result = service.get_logo_dev_url(ticker="AAPL")

            assert result is not None
            assert "img.logo.dev/ticker/AAPL" in result.icon_value

    def test_logo_dev_url_with_name(self):
        """Test generating Logo.dev URL with company name."""
        with patch("app.services.icon_provider_service.settings") as mock_settings:
            mock_settings.LOGO_DEV_API_KEY = "test_key"
            mock_settings.logo_dev_enabled = True

            service = IconProviderService()
            result = service.get_logo_dev_url(name="Apple Inc")

            assert result is not None
            assert "img.logo.dev/name/" in result.icon_value

    def test_logo_dev_url_returns_none_when_not_configured(self):
        """Test that logo.dev returns None when not configured."""
        with patch("app.services.icon_provider_service.settings") as mock_settings:
            mock_settings.LOGO_DEV_API_KEY = None
            mock_settings.logo_dev_enabled = False

            service = IconProviderService()
            result = service.get_logo_dev_url(domain="chase.com")

            assert result is None

    def test_get_icon_simple_icons_preference(self):
        """Test get_icon with simple_icons preference."""
        service = IconProviderService()
        result = service.get_icon(
            payee_name="Amazon",
            simple_icons_slug="amazon",
            simple_icons_color="FF9900",
            user_preference="simple_icons",
        )

        assert result.provider == "simple_icons"
        assert "cdn.simpleicons.org/amazon" in result.icon_value

    def test_get_icon_logo_dev_preference_with_domain(self):
        """Test get_icon with logo_dev preference and domain."""
        with patch("app.services.icon_provider_service.settings") as mock_settings:
            mock_settings.LOGO_DEV_API_KEY = "test_key"
            mock_settings.logo_dev_enabled = True

            service = IconProviderService()
            result = service.get_icon(
                payee_name="Chase",
                simple_icons_slug="chase",
                logo_dev_domain="chase.com",
                user_preference="logo_dev",
            )

            assert result.provider == "logo_dev"
            assert "img.logo.dev/chase.com" in result.icon_value

    def test_get_icon_fallback_to_simple_icons(self):
        """Test get_icon falls back to Simple Icons when logo.dev not available."""
        with patch("app.services.icon_provider_service.settings") as mock_settings:
            mock_settings.LOGO_DEV_API_KEY = None
            mock_settings.logo_dev_enabled = False

            service = IconProviderService()
            result = service.get_icon(
                payee_name="Chase",
                simple_icons_slug="chase",
                logo_dev_domain="chase.com",
                user_preference="logo_dev",  # User prefers logo_dev but it's not available
            )

            # Should fall back to simple_icons
            assert result.provider == "simple_icons"
            assert "cdn.simpleicons.org/chase" in result.icon_value

    def test_get_icon_fallback_to_emoji(self):
        """Test get_icon falls back to emoji when no icons available."""
        service = IconProviderService()
        result = service.get_icon(
            payee_name="Local Coffee Shop",
            user_preference="simple_icons",
        )

        assert result.icon_type == "emoji"
        assert result.icon_value.startswith("emoji:")
        assert result.provider == "fallback"

    def test_get_icon_custom_fallback_emoji(self):
        """Test get_icon with custom fallback emoji."""
        service = IconProviderService()
        result = service.get_icon(
            payee_name="Local Coffee Shop",
            user_preference="simple_icons",
            fallback_emoji="☕",
        )

        assert result.icon_value == "emoji:☕"

    def test_get_icon_provider_status(self):
        """Test get_icon_provider_status returns correct structure."""
        service = IconProviderService()
        status = service.get_icon_provider_status()

        assert "providers" in status
        assert "simple_icons" in status["providers"]
        assert "logo_dev" in status["providers"]
        assert "default_provider" in status
        assert status["default_provider"] == "simple_icons"

        # Check Simple Icons provider info
        si = status["providers"]["simple_icons"]
        assert si["available"] is True
        assert si["requires_api_key"] is False
        assert si["requires_attribution"] is False

        # Check Logo.dev provider info
        ld = status["providers"]["logo_dev"]
        assert "available" in ld
        assert ld["requires_api_key"] is True

    def test_singleton_pattern(self):
        """Test that get_icon_provider_service returns singleton."""
        # Reset singleton
        import app.services.icon_provider_service as module
        module._icon_provider_service = None

        service1 = get_icon_provider_service()
        service2 = get_icon_provider_service()

        assert service1 is service2


class TestIconResult:
    """Tests for IconResult dataclass."""

    def test_icon_result_creation(self):
        """Test creating IconResult."""
        result = IconResult(
            icon_type="url",
            icon_value="https://example.com/icon.png",
            provider="test",
            requires_attribution=False,
        )

        assert result.icon_type == "url"
        assert result.icon_value == "https://example.com/icon.png"
        assert result.provider == "test"
        assert result.requires_attribution is False
        assert result.confidence == 1.0  # Default
        assert result.brand_color is None  # Default

    def test_icon_result_with_all_fields(self):
        """Test creating IconResult with all fields."""
        result = IconResult(
            icon_type="url",
            icon_value="https://example.com/icon.png",
            provider="simple_icons",
            requires_attribution=False,
            confidence=0.9,
            brand_color="#FF0000",
        )

        assert result.confidence == 0.9
        assert result.brand_color == "#FF0000"
