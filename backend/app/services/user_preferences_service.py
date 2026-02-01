"""
User Preferences Service

Provides typed access to user preferences stored in the ui_preferences JSONB column.
Handles default values, validation, and partial updates.
"""
from typing import Optional, Dict, Any, List, Literal
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.models.user import User


# =============================================================================
# Default Preferences
# =============================================================================

class DefaultPreferences:
    """Default values for all user preferences."""

    # Display preferences
    DATE_FORMAT: str = "MM/DD/YYYY"
    NUMBER_FORMAT: str = "1,234.56"
    CURRENCY_SYMBOL: str = "$"
    CURRENCY_POSITION: str = "before"  # "before" or "after"
    CURRENCY_DECIMALS: int = 2
    START_OF_WEEK: str = "sunday"  # "sunday" or "monday"

    # Transaction preferences
    TRANSACTIONS_SORT_COLUMN: str = "date"
    TRANSACTIONS_SORT_ORDER: str = "desc"
    TRANSACTIONS_ROWS_PER_PAGE: int = 50
    TRANSACTIONS_VISIBLE_COLUMNS: Dict[str, bool] = {
        "date": True,
        "payee": True,
        "category": True,
        "account": True,
        "amount": True,
        "notes": False,
        "tags": False,
    }

    # Import preferences
    IMPORT_AUTO_CREATE_PAYEES: bool = True
    IMPORT_AUTO_APPLY_RULES: bool = True
    IMPORT_DUPLICATE_STRICTNESS: str = "moderate"  # "strict", "moderate", "relaxed"
    IMPORT_DEFAULT_ACCOUNT_ID: Optional[int] = None

    # Icon provider
    ICON_PROVIDER: str = "simple_icons"  # "simple_icons" or "logo_dev"

    @classmethod
    def get_all_defaults(cls) -> Dict[str, Any]:
        """Get all default preferences as a dictionary."""
        return {
            # Display
            "date_format": cls.DATE_FORMAT,
            "number_format": cls.NUMBER_FORMAT,
            "currency_symbol": cls.CURRENCY_SYMBOL,
            "currency_position": cls.CURRENCY_POSITION,
            "currency_decimals": cls.CURRENCY_DECIMALS,
            "start_of_week": cls.START_OF_WEEK,
            # Transactions
            "transactions_sort_column": cls.TRANSACTIONS_SORT_COLUMN,
            "transactions_sort_order": cls.TRANSACTIONS_SORT_ORDER,
            "transactions_rows_per_page": cls.TRANSACTIONS_ROWS_PER_PAGE,
            "transactions_visible_columns": cls.TRANSACTIONS_VISIBLE_COLUMNS.copy(),
            # Import
            "import_auto_create_payees": cls.IMPORT_AUTO_CREATE_PAYEES,
            "import_auto_apply_rules": cls.IMPORT_AUTO_APPLY_RULES,
            "import_duplicate_strictness": cls.IMPORT_DUPLICATE_STRICTNESS,
            "import_default_account_id": cls.IMPORT_DEFAULT_ACCOUNT_ID,
            # Icon provider
            "icon_provider": cls.ICON_PROVIDER,
        }


# =============================================================================
# Preference Categories
# =============================================================================

PREFERENCE_CATEGORIES = {
    "display": [
        "date_format",
        "number_format",
        "currency_symbol",
        "currency_position",
        "currency_decimals",
        "start_of_week",
    ],
    "transactions": [
        "transactions_sort_column",
        "transactions_sort_order",
        "transactions_rows_per_page",
        "transactions_visible_columns",
    ],
    "import": [
        "import_auto_create_payees",
        "import_auto_apply_rules",
        "import_duplicate_strictness",
        "import_default_account_id",
    ],
    "appearance": [
        "icon_provider",
    ],
}

# All valid preference keys
ALL_PREFERENCE_KEYS = set()
for keys in PREFERENCE_CATEGORIES.values():
    ALL_PREFERENCE_KEYS.update(keys)


# =============================================================================
# User Preferences Service
# =============================================================================

class UserPreferencesService:
    """
    Service for managing user preferences.

    Preferences are stored in the user's ui_preferences JSONB column.
    This service provides typed access with default value handling.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_user_preferences(self, user: User) -> Dict[str, Any]:
        """
        Get all preferences for a user, merged with defaults.

        Returns a complete preferences dictionary with user values
        overriding defaults where set.
        """
        defaults = DefaultPreferences.get_all_defaults()
        user_prefs = user.ui_preferences or {}

        # Merge user preferences over defaults
        merged = defaults.copy()
        for key, value in user_prefs.items():
            if key in ALL_PREFERENCE_KEYS:
                merged[key] = value

        return merged

    def get_preference(self, user: User, key: str) -> Any:
        """
        Get a single preference value for a user.

        Returns the user's value if set, otherwise the default.
        Raises KeyError if the preference key is not valid.
        """
        if key not in ALL_PREFERENCE_KEYS:
            raise KeyError(f"Unknown preference key: {key}")

        defaults = DefaultPreferences.get_all_defaults()
        user_prefs = user.ui_preferences or {}

        return user_prefs.get(key, defaults.get(key))

    def get_preferences_by_category(self, user: User, category: str) -> Dict[str, Any]:
        """
        Get all preferences for a specific category.

        Args:
            user: The user to get preferences for
            category: One of "display", "transactions", "import", "appearance"

        Returns:
            Dictionary of preference key-value pairs for the category
        """
        if category not in PREFERENCE_CATEGORIES:
            raise KeyError(f"Unknown preference category: {category}")

        all_prefs = self.get_user_preferences(user)
        category_keys = PREFERENCE_CATEGORIES[category]

        return {key: all_prefs[key] for key in category_keys}

    def set_preference(self, user: User, key: str, value: Any) -> User:
        """
        Set a single preference value for a user.

        Args:
            user: The user to update
            key: The preference key
            value: The new value

        Returns:
            The updated user object
        """
        if key not in ALL_PREFERENCE_KEYS:
            raise KeyError(f"Unknown preference key: {key}")

        # Initialize ui_preferences if None
        if user.ui_preferences is None:
            user.ui_preferences = {}

        # Update the preference
        user.ui_preferences[key] = value

        # Mark the column as modified (needed for JSONB)
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(user, "ui_preferences")

        self.db.commit()
        self.db.refresh(user)

        return user

    def set_preferences(self, user: User, preferences: Dict[str, Any]) -> User:
        """
        Set multiple preferences at once (partial update).

        Only updates the keys provided; other preferences remain unchanged.

        Args:
            user: The user to update
            preferences: Dictionary of preference key-value pairs

        Returns:
            The updated user object
        """
        # Validate all keys first
        invalid_keys = set(preferences.keys()) - ALL_PREFERENCE_KEYS
        if invalid_keys:
            raise KeyError(f"Unknown preference keys: {invalid_keys}")

        # Initialize ui_preferences if None
        if user.ui_preferences is None:
            user.ui_preferences = {}

        # Update preferences
        for key, value in preferences.items():
            user.ui_preferences[key] = value

        # Mark the column as modified (needed for JSONB)
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(user, "ui_preferences")

        self.db.commit()
        self.db.refresh(user)

        return user

    def reset_preference(self, user: User, key: str) -> User:
        """
        Reset a single preference to its default value.

        Args:
            user: The user to update
            key: The preference key to reset

        Returns:
            The updated user object
        """
        if key not in ALL_PREFERENCE_KEYS:
            raise KeyError(f"Unknown preference key: {key}")

        if user.ui_preferences and key in user.ui_preferences:
            del user.ui_preferences[key]

            # Mark the column as modified (needed for JSONB)
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(user, "ui_preferences")

            self.db.commit()
            self.db.refresh(user)

        return user

    def reset_all_preferences(self, user: User) -> User:
        """
        Reset all preferences to defaults.

        Args:
            user: The user to update

        Returns:
            The updated user object
        """
        user.ui_preferences = {}

        # Mark the column as modified (needed for JSONB)
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(user, "ui_preferences")

        self.db.commit()
        self.db.refresh(user)

        return user

    def reset_category(self, user: User, category: str) -> User:
        """
        Reset all preferences in a category to defaults.

        Args:
            user: The user to update
            category: The category to reset

        Returns:
            The updated user object
        """
        if category not in PREFERENCE_CATEGORIES:
            raise KeyError(f"Unknown preference category: {category}")

        if user.ui_preferences:
            for key in PREFERENCE_CATEGORIES[category]:
                if key in user.ui_preferences:
                    del user.ui_preferences[key]

            # Mark the column as modified (needed for JSONB)
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(user, "ui_preferences")

            self.db.commit()
            self.db.refresh(user)

        return user

    # =========================================================================
    # Typed Getters for Common Preferences
    # =========================================================================

    def get_date_format(self, user: User) -> str:
        """Get the user's preferred date format."""
        return self.get_preference(user, "date_format")

    def get_number_format(self, user: User) -> str:
        """Get the user's preferred number format."""
        return self.get_preference(user, "number_format")

    def get_currency_symbol(self, user: User) -> str:
        """Get the user's preferred currency symbol."""
        return self.get_preference(user, "currency_symbol")

    def get_icon_provider(self, user: User) -> str:
        """Get the user's preferred icon provider."""
        return self.get_preference(user, "icon_provider")

    def get_transactions_sort(self, user: User) -> tuple[str, str]:
        """Get the user's preferred transaction sort (column, order)."""
        return (
            self.get_preference(user, "transactions_sort_column"),
            self.get_preference(user, "transactions_sort_order"),
        )

    def get_transactions_rows_per_page(self, user: User) -> int:
        """Get the user's preferred rows per page for transactions."""
        return self.get_preference(user, "transactions_rows_per_page")

    def get_transactions_visible_columns(self, user: User) -> Dict[str, bool]:
        """Get the user's preferred visible columns for transactions."""
        return self.get_preference(user, "transactions_visible_columns")

    def get_import_auto_create_payees(self, user: User) -> bool:
        """Get whether to auto-create payees during import."""
        return self.get_preference(user, "import_auto_create_payees")

    def get_import_auto_apply_rules(self, user: User) -> bool:
        """Get whether to auto-apply rules during import."""
        return self.get_preference(user, "import_auto_apply_rules")

    def get_import_duplicate_strictness(self, user: User) -> str:
        """Get the duplicate detection strictness level."""
        return self.get_preference(user, "import_duplicate_strictness")

    @staticmethod
    def get_preference_metadata() -> Dict[str, Dict[str, Any]]:
        """
        Get metadata about all preferences for UI rendering.

        Returns information about each preference including:
        - type: The input type (text, select, toggle, number)
        - label: Human-readable label
        - description: Help text
        - options: For select types, the available options
        - default: The default value
        """
        defaults = DefaultPreferences.get_all_defaults()

        return {
            # Display preferences
            "date_format": {
                "type": "select",
                "label": "Date Format",
                "description": "How dates are displayed throughout the app",
                "category": "display",
                "options": [
                    {"value": "MM/DD/YYYY", "label": "MM/DD/YYYY (01/31/2026)"},
                    {"value": "DD/MM/YYYY", "label": "DD/MM/YYYY (31/01/2026)"},
                    {"value": "YYYY-MM-DD", "label": "YYYY-MM-DD (2026-01-31)"},
                    {"value": "MMM D, YYYY", "label": "MMM D, YYYY (Jan 31, 2026)"},
                ],
                "default": defaults["date_format"],
            },
            "number_format": {
                "type": "select",
                "label": "Number Format",
                "description": "How numbers and amounts are formatted",
                "category": "display",
                "options": [
                    {"value": "1,234.56", "label": "1,234.56 (US/UK)"},
                    {"value": "1.234,56", "label": "1.234,56 (EU)"},
                    {"value": "1 234.56", "label": "1 234.56 (Space separator)"},
                ],
                "default": defaults["number_format"],
            },
            "currency_symbol": {
                "type": "text",
                "label": "Currency Symbol",
                "description": "Symbol to display with amounts (e.g., $, €, £)",
                "category": "display",
                "default": defaults["currency_symbol"],
            },
            "currency_position": {
                "type": "select",
                "label": "Currency Position",
                "description": "Where to display the currency symbol",
                "category": "display",
                "options": [
                    {"value": "before", "label": "Before amount ($100)"},
                    {"value": "after", "label": "After amount (100$)"},
                ],
                "default": defaults["currency_position"],
            },
            "currency_decimals": {
                "type": "number",
                "label": "Decimal Places",
                "description": "Number of decimal places for amounts",
                "category": "display",
                "min": 0,
                "max": 4,
                "default": defaults["currency_decimals"],
            },
            "start_of_week": {
                "type": "select",
                "label": "Start of Week",
                "description": "First day of the week for calendars and reports",
                "category": "display",
                "options": [
                    {"value": "sunday", "label": "Sunday"},
                    {"value": "monday", "label": "Monday"},
                ],
                "default": defaults["start_of_week"],
            },

            # Transaction preferences
            "transactions_sort_column": {
                "type": "select",
                "label": "Default Sort Column",
                "description": "Which column to sort transactions by default",
                "category": "transactions",
                "options": [
                    {"value": "date", "label": "Date"},
                    {"value": "payee", "label": "Payee"},
                    {"value": "amount", "label": "Amount"},
                    {"value": "category", "label": "Category"},
                ],
                "default": defaults["transactions_sort_column"],
            },
            "transactions_sort_order": {
                "type": "select",
                "label": "Default Sort Order",
                "description": "Sort direction for transactions",
                "category": "transactions",
                "options": [
                    {"value": "desc", "label": "Newest first"},
                    {"value": "asc", "label": "Oldest first"},
                ],
                "default": defaults["transactions_sort_order"],
            },
            "transactions_rows_per_page": {
                "type": "select",
                "label": "Rows Per Page",
                "description": "Number of transactions to show per page",
                "category": "transactions",
                "options": [
                    {"value": 25, "label": "25"},
                    {"value": 50, "label": "50"},
                    {"value": 100, "label": "100"},
                ],
                "default": defaults["transactions_rows_per_page"],
            },
            "transactions_visible_columns": {
                "type": "column_toggles",
                "label": "Visible Columns",
                "description": "Which columns to show in the transactions table",
                "category": "transactions",
                "columns": ["date", "payee", "category", "account", "amount", "notes", "tags"],
                "default": defaults["transactions_visible_columns"],
            },

            # Import preferences
            "import_auto_create_payees": {
                "type": "toggle",
                "label": "Auto-Create Payees",
                "description": "Automatically create new payees during import",
                "category": "import",
                "default": defaults["import_auto_create_payees"],
            },
            "import_auto_apply_rules": {
                "type": "toggle",
                "label": "Auto-Apply Rules",
                "description": "Automatically apply matching rules during import",
                "category": "import",
                "default": defaults["import_auto_apply_rules"],
            },
            "import_duplicate_strictness": {
                "type": "select",
                "label": "Duplicate Detection",
                "description": "How strictly to check for duplicate transactions",
                "category": "import",
                "options": [
                    {"value": "strict", "label": "Strict (exact match required)"},
                    {"value": "moderate", "label": "Moderate (recommended)"},
                    {"value": "relaxed", "label": "Relaxed (date + amount only)"},
                ],
                "default": defaults["import_duplicate_strictness"],
            },
            "import_default_account_id": {
                "type": "account_select",
                "label": "Default Import Account",
                "description": "Default account to import transactions into",
                "category": "import",
                "default": defaults["import_default_account_id"],
            },

            # Appearance preferences
            "icon_provider": {
                "type": "select",
                "label": "Icon Provider",
                "description": "Source for merchant and payee logos",
                "category": "appearance",
                "options": [
                    {"value": "simple_icons", "label": "Simple Icons (default)"},
                    {"value": "logo_dev", "label": "Logo.dev (requires API key)"},
                ],
                "default": defaults["icon_provider"],
            },
        }
