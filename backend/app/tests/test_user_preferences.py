"""
Tests for UserPreferencesService and preferences API endpoints.
"""
import pytest
from sqlalchemy.orm import Session
from app.models.user import User
from app.services.user_preferences_service import (
    UserPreferencesService,
    DefaultPreferences,
    ALL_PREFERENCE_KEYS,
    PREFERENCE_CATEGORIES,
)


class TestUserPreferencesService:
    """Tests for UserPreferencesService."""

    def test_get_preferences_returns_defaults_for_new_user(self, db_session: Session, test_user: User):
        """New user should get all default preferences."""
        # Ensure user has no preferences set
        test_user.ui_preferences = None
        db_session.commit()

        service = UserPreferencesService(db_session)
        prefs = service.get_user_preferences(test_user)

        # Check that all defaults are present
        defaults = DefaultPreferences.get_all_defaults()
        for key, default_value in defaults.items():
            assert key in prefs
            assert prefs[key] == default_value

    def test_get_preferences_merges_user_values_over_defaults(self, db_session: Session, test_user: User):
        """User values should override defaults."""
        test_user.ui_preferences = {
            "date_format": "YYYY-MM-DD",
            "icon_provider": "logo_dev",
        }
        db_session.commit()

        service = UserPreferencesService(db_session)
        prefs = service.get_user_preferences(test_user)

        # User-set values
        assert prefs["date_format"] == "YYYY-MM-DD"
        assert prefs["icon_provider"] == "logo_dev"

        # Default values for unset preferences
        assert prefs["number_format"] == DefaultPreferences.NUMBER_FORMAT
        assert prefs["transactions_rows_per_page"] == DefaultPreferences.TRANSACTIONS_ROWS_PER_PAGE

    def test_get_single_preference(self, db_session: Session, test_user: User):
        """Should get a single preference value."""
        test_user.ui_preferences = {"date_format": "DD/MM/YYYY"}
        db_session.commit()

        service = UserPreferencesService(db_session)

        # User-set value
        assert service.get_preference(test_user, "date_format") == "DD/MM/YYYY"

        # Default value
        assert service.get_preference(test_user, "number_format") == DefaultPreferences.NUMBER_FORMAT

    def test_get_single_preference_invalid_key_raises(self, db_session: Session, test_user: User):
        """Should raise KeyError for invalid preference key."""
        service = UserPreferencesService(db_session)

        with pytest.raises(KeyError, match="Unknown preference key"):
            service.get_preference(test_user, "invalid_key")

    def test_get_preferences_by_category(self, db_session: Session, test_user: User):
        """Should get preferences for a specific category."""
        test_user.ui_preferences = {
            "date_format": "YYYY-MM-DD",
            "transactions_rows_per_page": 100,
        }
        db_session.commit()

        service = UserPreferencesService(db_session)

        # Display category
        display_prefs = service.get_preferences_by_category(test_user, "display")
        assert "date_format" in display_prefs
        assert display_prefs["date_format"] == "YYYY-MM-DD"
        assert "transactions_rows_per_page" not in display_prefs

        # Transactions category
        txn_prefs = service.get_preferences_by_category(test_user, "transactions")
        assert "transactions_rows_per_page" in txn_prefs
        assert txn_prefs["transactions_rows_per_page"] == 100

    def test_get_preferences_by_invalid_category_raises(self, db_session: Session, test_user: User):
        """Should raise KeyError for invalid category."""
        service = UserPreferencesService(db_session)

        with pytest.raises(KeyError, match="Unknown preference category"):
            service.get_preferences_by_category(test_user, "invalid_category")

    def test_set_single_preference(self, db_session: Session, test_user: User):
        """Should set a single preference value."""
        test_user.ui_preferences = None
        db_session.commit()

        service = UserPreferencesService(db_session)
        service.set_preference(test_user, "date_format", "DD/MM/YYYY")

        # Verify it was set
        assert test_user.ui_preferences["date_format"] == "DD/MM/YYYY"
        assert service.get_preference(test_user, "date_format") == "DD/MM/YYYY"

    def test_set_single_preference_invalid_key_raises(self, db_session: Session, test_user: User):
        """Should raise KeyError for invalid preference key."""
        service = UserPreferencesService(db_session)

        with pytest.raises(KeyError, match="Unknown preference key"):
            service.set_preference(test_user, "invalid_key", "value")

    def test_set_multiple_preferences(self, db_session: Session, test_user: User):
        """Should set multiple preferences at once."""
        test_user.ui_preferences = None
        db_session.commit()

        service = UserPreferencesService(db_session)
        service.set_preferences(test_user, {
            "date_format": "YYYY-MM-DD",
            "number_format": "1.234,56",
            "transactions_rows_per_page": 100,
        })

        # Verify all were set
        assert test_user.ui_preferences["date_format"] == "YYYY-MM-DD"
        assert test_user.ui_preferences["number_format"] == "1.234,56"
        assert test_user.ui_preferences["transactions_rows_per_page"] == 100

    def test_set_multiple_preferences_partial_update(self, db_session: Session, test_user: User):
        """Should only update provided preferences, not clear others."""
        test_user.ui_preferences = {
            "date_format": "MM/DD/YYYY",
            "icon_provider": "logo_dev",
        }
        db_session.commit()

        service = UserPreferencesService(db_session)
        service.set_preferences(test_user, {
            "number_format": "1.234,56",
        })

        # New value set
        assert test_user.ui_preferences["number_format"] == "1.234,56"
        # Existing values preserved
        assert test_user.ui_preferences["date_format"] == "MM/DD/YYYY"
        assert test_user.ui_preferences["icon_provider"] == "logo_dev"

    def test_set_multiple_preferences_invalid_key_raises(self, db_session: Session, test_user: User):
        """Should raise KeyError if any key is invalid."""
        service = UserPreferencesService(db_session)

        with pytest.raises(KeyError, match="Unknown preference keys"):
            service.set_preferences(test_user, {
                "date_format": "YYYY-MM-DD",
                "invalid_key": "value",
            })

    def test_reset_single_preference(self, db_session: Session, test_user: User):
        """Should reset a preference to its default."""
        test_user.ui_preferences = {
            "date_format": "YYYY-MM-DD",
            "icon_provider": "logo_dev",
        }
        db_session.commit()

        service = UserPreferencesService(db_session)
        service.reset_preference(test_user, "date_format")

        # Preference removed from stored values
        assert "date_format" not in test_user.ui_preferences
        # Other preferences preserved
        assert test_user.ui_preferences["icon_provider"] == "logo_dev"
        # Getting the preference returns the default
        assert service.get_preference(test_user, "date_format") == DefaultPreferences.DATE_FORMAT

    def test_reset_all_preferences(self, db_session: Session, test_user: User):
        """Should reset all preferences to defaults."""
        test_user.ui_preferences = {
            "date_format": "YYYY-MM-DD",
            "icon_provider": "logo_dev",
            "transactions_rows_per_page": 100,
        }
        db_session.commit()

        service = UserPreferencesService(db_session)
        service.reset_all_preferences(test_user)

        # All preferences cleared
        assert test_user.ui_preferences == {}

        # Getting preferences returns all defaults
        prefs = service.get_user_preferences(test_user)
        defaults = DefaultPreferences.get_all_defaults()
        for key, value in defaults.items():
            assert prefs[key] == value

    def test_reset_category_preferences(self, db_session: Session, test_user: User):
        """Should reset all preferences in a category."""
        test_user.ui_preferences = {
            "date_format": "YYYY-MM-DD",
            "number_format": "1.234,56",
            "transactions_rows_per_page": 100,
            "icon_provider": "logo_dev",
        }
        db_session.commit()

        service = UserPreferencesService(db_session)
        service.reset_category(test_user, "display")

        # Display preferences cleared
        assert "date_format" not in test_user.ui_preferences
        assert "number_format" not in test_user.ui_preferences
        # Other preferences preserved
        assert test_user.ui_preferences["transactions_rows_per_page"] == 100
        assert test_user.ui_preferences["icon_provider"] == "logo_dev"

    def test_typed_getters(self, db_session: Session, test_user: User):
        """Test typed getter methods."""
        test_user.ui_preferences = {
            "date_format": "DD/MM/YYYY",
            "transactions_sort_column": "amount",
            "transactions_sort_order": "asc",
            "import_auto_create_payees": False,
        }
        db_session.commit()

        service = UserPreferencesService(db_session)

        assert service.get_date_format(test_user) == "DD/MM/YYYY"
        assert service.get_transactions_sort(test_user) == ("amount", "asc")
        assert service.get_import_auto_create_payees(test_user) is False

        # Default values
        assert service.get_number_format(test_user) == DefaultPreferences.NUMBER_FORMAT
        assert service.get_transactions_rows_per_page(test_user) == DefaultPreferences.TRANSACTIONS_ROWS_PER_PAGE

    def test_preference_metadata_has_all_keys(self):
        """Preference metadata should cover all preference keys."""
        metadata = UserPreferencesService.get_preference_metadata()

        for key in ALL_PREFERENCE_KEYS:
            assert key in metadata, f"Missing metadata for preference: {key}"
            assert "type" in metadata[key]
            assert "label" in metadata[key]
            assert "description" in metadata[key]
            assert "category" in metadata[key]
            assert "default" in metadata[key]

    def test_preference_categories_complete(self):
        """All preference keys should be in a category."""
        categorized_keys = set()
        for keys in PREFERENCE_CATEGORIES.values():
            categorized_keys.update(keys)

        assert categorized_keys == ALL_PREFERENCE_KEYS


class TestPreferencesAPIEndpoints:
    """Tests for preferences API endpoints."""

    def test_get_preferences_endpoint(self, client, auth_headers):
        """GET /api/v1/users/me/preferences should return merged preferences."""
        response = client.get(
            "/api/v1/users/me/preferences",
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.json()
        # Should have all default keys
        assert "date_format" in data
        assert "number_format" in data
        assert "transactions_rows_per_page" in data
        assert "icon_provider" in data

    def test_get_preferences_metadata_endpoint(self, client, auth_headers):
        """GET /api/v1/users/me/preferences/metadata should return metadata."""
        response = client.get(
            "/api/v1/users/me/preferences/metadata",
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.json()
        assert "categories" in data
        assert "preferences" in data
        assert "display" in data["categories"]
        assert "date_format" in data["preferences"]

    def test_get_preferences_by_category_endpoint(self, client, auth_headers):
        """GET /api/v1/users/me/preferences/{category} should return category prefs."""
        response = client.get(
            "/api/v1/users/me/preferences/display",
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.json()
        assert "date_format" in data
        assert "number_format" in data
        # Should not have transaction preferences
        assert "transactions_rows_per_page" not in data

    def test_update_preferences_endpoint(self, client, auth_headers):
        """PATCH /api/v1/users/me/preferences should update preferences."""
        response = client.patch(
            "/api/v1/users/me/preferences",
            headers=auth_headers,
            json={"date_format": "YYYY-MM-DD", "transactions_rows_per_page": 100},
        )
        assert response.status_code == 200

        data = response.json()
        assert data["date_format"] == "YYYY-MM-DD"
        assert data["transactions_rows_per_page"] == 100

    def test_reset_preference_endpoint(self, client, auth_headers):
        """DELETE /api/v1/users/me/preferences/{key} should reset a preference."""
        # First set a preference
        client.patch(
            "/api/v1/users/me/preferences",
            headers=auth_headers,
            json={"date_format": "YYYY-MM-DD"},
        )

        # Then reset it
        response = client.delete(
            "/api/v1/users/me/preferences/date_format",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert "reset to default" in response.json()["message"]

        # Verify it's back to default
        prefs_response = client.get(
            "/api/v1/users/me/preferences",
            headers=auth_headers,
        )
        assert prefs_response.json()["date_format"] == DefaultPreferences.DATE_FORMAT

    def test_reset_all_preferences_endpoint(self, client, auth_headers):
        """DELETE /api/v1/users/me/preferences should reset all preferences."""
        # First set some preferences
        client.patch(
            "/api/v1/users/me/preferences",
            headers=auth_headers,
            json={"date_format": "YYYY-MM-DD", "icon_provider": "logo_dev"},
        )

        # Reset all
        response = client.delete(
            "/api/v1/users/me/preferences",
            headers=auth_headers,
        )
        assert response.status_code == 200

        # Verify all are defaults
        prefs_response = client.get(
            "/api/v1/users/me/preferences",
            headers=auth_headers,
        )
        data = prefs_response.json()
        assert data["date_format"] == DefaultPreferences.DATE_FORMAT
        assert data["icon_provider"] == DefaultPreferences.ICON_PROVIDER

    def test_reset_category_endpoint(self, client, auth_headers):
        """DELETE /api/v1/users/me/preferences/category/{cat} should reset category."""
        # First set preferences in multiple categories
        client.patch(
            "/api/v1/users/me/preferences",
            headers=auth_headers,
            json={
                "date_format": "YYYY-MM-DD",
                "transactions_rows_per_page": 100,
            },
        )

        # Reset display category
        response = client.delete(
            "/api/v1/users/me/preferences/category/display",
            headers=auth_headers,
        )
        assert response.status_code == 200

        # Verify display is reset but transactions preserved
        prefs_response = client.get(
            "/api/v1/users/me/preferences",
            headers=auth_headers,
        )
        data = prefs_response.json()
        assert data["date_format"] == DefaultPreferences.DATE_FORMAT
        assert data["transactions_rows_per_page"] == 100
