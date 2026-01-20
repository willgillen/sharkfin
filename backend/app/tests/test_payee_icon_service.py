"""Tests for PayeeIconService - brand logo and emoji suggestion functionality."""

import pytest
from app.services.payee_icon_service import PayeeIconService, payee_icon_service


class TestPayeeIconService:
    """Test suite for PayeeIconService."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = PayeeIconService()

    # =========================================================================
    # Brand Logo Suggestion Tests
    # =========================================================================

    def test_suggest_icon_for_exact_brand_match(self):
        """Test that exact brand names get brand logo suggestions."""
        result = self.service.suggest_icon("Starbucks")

        assert result["icon_type"] == "brand"
        assert "cdn.simpleicons.org/starbucks" in result["icon_value"]
        assert result["brand_color"] == "#006241"
        assert result["confidence"] == 1.0
        assert result["slug"] == "starbucks"

    def test_suggest_icon_for_walmart(self):
        """Test brand suggestion for Walmart."""
        result = self.service.suggest_icon("Walmart")

        assert result["icon_type"] == "brand"
        assert "walmart" in result["icon_value"]
        assert result["brand_color"] == "#0071CE"
        assert result["matched_term"] == "walmart"

    def test_suggest_icon_for_amazon(self):
        """Test brand suggestion for Amazon."""
        result = self.service.suggest_icon("Amazon")

        assert result["icon_type"] == "brand"
        assert "amazon" in result["icon_value"]
        assert result["brand_color"] == "#FF9900"

    def test_suggest_icon_for_target(self):
        """Test brand suggestion for Target."""
        result = self.service.suggest_icon("Target")

        assert result["icon_type"] == "brand"
        assert "target" in result["icon_value"]
        assert result["brand_color"] == "#CC0000"

    def test_suggest_icon_for_partial_brand_match(self):
        """Test brand suggestion when brand name is part of payee name."""
        result = self.service.suggest_icon("STARBUCKS STORE #12345")

        assert result["icon_type"] == "brand"
        assert "starbucks" in result["icon_value"]
        assert result["matched_term"] == "starbucks"
        # Confidence should be less than 1.0 for partial match
        assert result["confidence"] < 1.0

    def test_suggest_icon_for_uber_trip(self):
        """Test brand suggestion for Uber with transaction-like name."""
        result = self.service.suggest_icon("UBER TRIP 12345 SF CA")

        assert result["icon_type"] == "brand"
        assert "uber" in result["icon_value"]
        assert result["matched_term"] == "uber"

    def test_suggest_icon_for_netflix_subscription(self):
        """Test brand suggestion for streaming service."""
        result = self.service.suggest_icon("NETFLIX.COM")

        assert result["icon_type"] == "brand"
        assert "netflix" in result["icon_value"]

    def test_suggest_icon_case_insensitive(self):
        """Test that brand matching is case-insensitive."""
        result1 = self.service.suggest_icon("STARBUCKS")
        result2 = self.service.suggest_icon("starbucks")
        result3 = self.service.suggest_icon("StArBuCkS")

        assert result1["icon_type"] == "brand"
        assert result2["icon_type"] == "brand"
        assert result3["icon_type"] == "brand"
        assert result1["slug"] == result2["slug"] == result3["slug"]

    def test_suggest_icon_with_special_characters(self):
        """Test brand matching with special characters in name."""
        result = self.service.suggest_icon("McDonald's")

        assert result["icon_type"] == "brand"
        assert "mcdonalds" in result["icon_value"]

    def test_suggest_icon_for_gas_station(self):
        """Test brand suggestion for gas station."""
        result = self.service.suggest_icon("Shell Gas Station")

        assert result["icon_type"] == "brand"
        assert "shell" in result["icon_value"]

    def test_suggest_icon_for_airline(self):
        """Test brand suggestion for airline."""
        result = self.service.suggest_icon("United Airlines")

        assert result["icon_type"] == "brand"
        assert "unitedairlines" in result["icon_value"]

    # =========================================================================
    # Emoji Fallback Tests
    # =========================================================================

    def test_suggest_emoji_for_unknown_payee(self):
        """Test emoji fallback for unknown payee name."""
        result = self.service.suggest_icon("Joe's Corner Store")

        assert result["icon_type"] == "emoji"
        assert result["icon_value"].startswith("emoji:")
        assert result["emoji"] is not None

    def test_suggest_emoji_for_restaurant_keyword(self):
        """Test emoji suggestion for restaurant keyword."""
        result = self.service.suggest_icon("Mike's Restaurant")

        assert result["icon_type"] == "emoji"
        assert result["emoji"] == "🍽️"
        assert result["matched_term"] == "restaurant"

    def test_suggest_emoji_for_grocery_keyword(self):
        """Test emoji suggestion for grocery keyword."""
        result = self.service.suggest_icon("Local Grocery Store")

        assert result["icon_type"] == "emoji"
        assert result["emoji"] == "🛒"
        assert result["matched_term"] == "grocery"

    def test_suggest_emoji_for_pizza_keyword(self):
        """Test emoji suggestion for pizza keyword (when no brand match)."""
        result = self.service.suggest_icon("Tony's Pizza Place")

        assert result["icon_type"] == "emoji"
        # Should match "pizza"
        assert result["emoji"] == "🍕"

    def test_suggest_emoji_for_gas_keyword(self):
        """Test emoji suggestion for gas/fuel keyword."""
        result = self.service.suggest_icon("City Gas & Fuel")

        assert result["icon_type"] == "emoji"
        assert result["emoji"] == "⛽"

    def test_suggest_emoji_for_medical_keyword(self):
        """Test emoji suggestion for medical/doctor keyword."""
        result = self.service.suggest_icon("Dr. Smith Medical Clinic")

        assert result["icon_type"] == "emoji"
        # Should match "doctor", "medical", or "clinic"
        assert result["emoji"] in ["👨‍⚕️", "👩‍⚕️", "🏥"]

    def test_suggest_emoji_for_gym_fitness(self):
        """Test emoji suggestion for gym/fitness."""
        result = self.service.suggest_icon("Downtown Fitness Gym")

        assert result["icon_type"] == "emoji"
        assert result["emoji"] in ["💪", "🏋️"]

    def test_default_emoji_is_store(self):
        """Test that the default emoji is the store emoji."""
        # Directly verify the default constant
        assert self.service.DEFAULT_EMOJI == "🏪"

    def test_low_confidence_for_partial_match(self):
        """Test that partial brand matches have lower confidence."""
        # Full match should have high confidence
        full_result = self.service.suggest_icon("Starbucks")
        assert full_result["confidence"] == 1.0

        # Partial match (brand in longer string) should have lower confidence
        partial_result = self.service.suggest_icon("STARBUCKS STORE #12345 MAIN ST")
        assert partial_result["confidence"] < 1.0

    # =========================================================================
    # Logo URL Parsing Tests
    # =========================================================================

    def test_parse_logo_url_brand(self):
        """Test parsing a brand logo URL."""
        result = self.service.parse_logo_url("https://cdn.simpleicons.org/starbucks/006241")

        assert result["type"] == "brand"
        assert "starbucks" in result["value"]
        assert result["display_value"] == result["value"]

    def test_parse_logo_url_emoji(self):
        """Test parsing an emoji logo URL."""
        result = self.service.parse_logo_url("emoji:☕")

        assert result["type"] == "emoji"
        assert result["value"] == "☕"
        assert result["display_value"] == "☕"

    def test_parse_logo_url_custom(self):
        """Test parsing a custom logo URL."""
        custom_url = "https://example.com/my-logo.png"
        result = self.service.parse_logo_url(custom_url)

        assert result["type"] == "custom"
        assert result["value"] == custom_url
        assert result["display_value"] == custom_url

    def test_parse_logo_url_none(self):
        """Test parsing None/empty logo URL."""
        result1 = self.service.parse_logo_url(None)
        result2 = self.service.parse_logo_url("")

        assert result1["type"] == "none"
        assert result1["display_value"] == "🏪"  # Default emoji

        assert result2["type"] == "none"

    # =========================================================================
    # Brand URL Generation Tests
    # =========================================================================

    def test_get_brand_url_with_color(self):
        """Test generating brand URL with color."""
        url = self.service.get_brand_url("starbucks", "006241")

        assert url == "https://cdn.simpleicons.org/starbucks/006241"

    def test_get_brand_url_without_color(self):
        """Test generating brand URL without color."""
        url = self.service.get_brand_url("starbucks")

        assert url == "https://cdn.simpleicons.org/starbucks"

    # =========================================================================
    # Brand List Tests
    # =========================================================================

    def test_get_all_brands_returns_list(self):
        """Test that get_all_brands returns a list of brands."""
        brands = self.service.get_all_brands()

        assert isinstance(brands, list)
        assert len(brands) > 100  # We have 500+ brands
        assert all("name" in b for b in brands)
        assert all("slug" in b for b in brands)
        assert all("color" in b for b in brands)
        assert all("url" in b for b in brands)

    def test_get_all_brands_no_duplicates(self):
        """Test that get_all_brands has no duplicate slugs."""
        brands = self.service.get_all_brands()
        slugs = [b["slug"] for b in brands]

        assert len(slugs) == len(set(slugs))

    # =========================================================================
    # Emoji Categories Tests
    # =========================================================================

    def test_get_emoji_categories_returns_dict(self):
        """Test that get_emoji_categories returns grouped emojis."""
        categories = self.service.get_emoji_categories()

        assert isinstance(categories, dict)
        # Should have multiple emoji keys
        assert len(categories) > 20

    # =========================================================================
    # Singleton Instance Tests
    # =========================================================================

    def test_singleton_instance_works(self):
        """Test that the singleton instance works."""
        result = payee_icon_service.suggest_icon("Starbucks")

        assert result["icon_type"] == "brand"
        assert "starbucks" in result["icon_value"]


class TestPayeeIconAPIEndpoints:
    """Test payee icon API endpoints integration."""

    def test_suggest_icon_endpoint(self, client, auth_headers):
        """Test the icon suggestion endpoint."""
        response = client.get(
            "/api/v1/payees/icons/suggest",
            params={"name": "Starbucks"},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["icon_type"] == "brand"
        assert "starbucks" in data["icon_value"]
        assert data["confidence"] == 1.0

    def test_suggest_icon_endpoint_emoji_fallback(self, client, auth_headers):
        """Test icon suggestion endpoint with emoji fallback."""
        response = client.get(
            "/api/v1/payees/icons/suggest",
            params={"name": "Local Restaurant"},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["icon_type"] == "emoji"
        assert data["emoji"] == "🍽️"

    def test_suggest_icon_endpoint_requires_name(self, client, auth_headers):
        """Test that suggest endpoint requires name parameter."""
        response = client.get(
            "/api/v1/payees/icons/suggest",
            headers=auth_headers
        )

        assert response.status_code == 422  # Validation error

    def test_parse_icon_endpoint_brand(self, client, auth_headers):
        """Test the icon parsing endpoint with brand URL."""
        response = client.get(
            "/api/v1/payees/icons/parse",
            params={"logo_url": "https://cdn.simpleicons.org/starbucks/006241"},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "brand"

    def test_parse_icon_endpoint_emoji(self, client, auth_headers):
        """Test the icon parsing endpoint with emoji."""
        response = client.get(
            "/api/v1/payees/icons/parse",
            params={"logo_url": "emoji:☕"},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "emoji"
        assert data["value"] == "☕"

    def test_parse_icon_endpoint_none(self, client, auth_headers):
        """Test the icon parsing endpoint with no URL."""
        response = client.get(
            "/api/v1/payees/icons/parse",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "none"
        assert data["display_value"] == "🏪"

    def test_list_brands_endpoint(self, client, auth_headers):
        """Test the brands list endpoint."""
        response = client.get(
            "/api/v1/payees/icons/brands",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 100

    def test_icon_endpoints_require_auth(self, client):
        """Test that icon endpoints require authentication."""
        response = client.get("/api/v1/payees/icons/suggest", params={"name": "Test"})
        assert response.status_code == 401

        response = client.get("/api/v1/payees/icons/parse")
        assert response.status_code == 401

        response = client.get("/api/v1/payees/icons/brands")
        assert response.status_code == 401
