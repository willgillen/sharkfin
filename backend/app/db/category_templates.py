"""Category preset templates for initial setup."""
from typing import TypedDict, Optional


class CategoryTemplate(TypedDict):
    """Template for a category."""
    name: str
    type: str  # "income", "expense", "transfer"
    color: str
    icon: str
    parent: Optional[str]  # Parent category name, if subcategory


# Minimal preset - 7 categories for basic tracking
MINIMAL_CATEGORIES: list[CategoryTemplate] = [
    # Income
    {"name": "Salary", "type": "income", "color": "#10B981", "icon": "💰", "parent": None},
    {"name": "Other Income", "type": "income", "color": "#34D399", "icon": "💵", "parent": None},
    # Expense
    {"name": "Bills", "type": "expense", "color": "#EF4444", "icon": "📄", "parent": None},
    {"name": "Food", "type": "expense", "color": "#F97316", "icon": "🍽️", "parent": None},
    {"name": "Transportation", "type": "expense", "color": "#F59E0B", "icon": "🚗", "parent": None},
    {"name": "Shopping", "type": "expense", "color": "#EC4899", "icon": "🛍️", "parent": None},
    {"name": "Other", "type": "expense", "color": "#6B7280", "icon": "📦", "parent": None},
    # Transfer
    {"name": "Transfer", "type": "transfer", "color": "#6B7280", "icon": "🔄", "parent": None},
]

# Standard preset - 18 categories (matches current seed.py)
STANDARD_CATEGORIES: list[CategoryTemplate] = [
    # Income
    {"name": "Salary", "type": "income", "color": "#10B981", "icon": "💰", "parent": None},
    {"name": "Freelance", "type": "income", "color": "#34D399", "icon": "💼", "parent": None},
    {"name": "Investments", "type": "income", "color": "#6EE7B7", "icon": "📈", "parent": None},
    # Expense - Parent categories
    {"name": "Food & Dining", "type": "expense", "color": "#EF4444", "icon": "🍽️", "parent": None},
    {"name": "Transportation", "type": "expense", "color": "#F97316", "icon": "🚗", "parent": None},
    {"name": "Housing", "type": "expense", "color": "#DC2626", "icon": "🏠", "parent": None},
    {"name": "Utilities", "type": "expense", "color": "#B91C1C", "icon": "💡", "parent": None},
    {"name": "Entertainment", "type": "expense", "color": "#8B5CF6", "icon": "🎬", "parent": None},
    {"name": "Shopping", "type": "expense", "color": "#EC4899", "icon": "🛍️", "parent": None},
    {"name": "Healthcare", "type": "expense", "color": "#06B6D4", "icon": "🏥", "parent": None},
    # Subcategories
    {"name": "Groceries", "type": "expense", "color": "#F87171", "icon": "🛒", "parent": "Food & Dining"},
    {"name": "Restaurants", "type": "expense", "color": "#FCA5A5", "icon": "🍴", "parent": "Food & Dining"},
    {"name": "Coffee Shops", "type": "expense", "color": "#FECACA", "icon": "☕", "parent": "Food & Dining"},
    {"name": "Gas & Fuel", "type": "expense", "color": "#FB923C", "icon": "⛽", "parent": "Transportation"},
    {"name": "Parking", "type": "expense", "color": "#FDBA74", "icon": "🅿️", "parent": "Transportation"},
    {"name": "Rent/Mortgage", "type": "expense", "color": "#F87171", "icon": "🏘️", "parent": "Housing"},
    {"name": "Maintenance", "type": "expense", "color": "#FCA5A5", "icon": "🔧", "parent": "Housing"},
    # Transfer
    {"name": "Transfer", "type": "transfer", "color": "#6B7280", "icon": "🔄", "parent": None},
]

# Comprehensive preset - 30+ categories for detailed tracking
COMPREHENSIVE_CATEGORIES: list[CategoryTemplate] = [
    # Income
    {"name": "Salary", "type": "income", "color": "#10B981", "icon": "💰", "parent": None},
    {"name": "Freelance", "type": "income", "color": "#34D399", "icon": "💼", "parent": None},
    {"name": "Investments", "type": "income", "color": "#6EE7B7", "icon": "📈", "parent": None},
    {"name": "Gifts Received", "type": "income", "color": "#A7F3D0", "icon": "🎁", "parent": None},
    {"name": "Refunds", "type": "income", "color": "#D1FAE5", "icon": "💸", "parent": None},
    {"name": "Interest", "type": "income", "color": "#ECFDF5", "icon": "🏦", "parent": None},
    # Expense - Parent categories
    {"name": "Food & Dining", "type": "expense", "color": "#EF4444", "icon": "🍽️", "parent": None},
    {"name": "Transportation", "type": "expense", "color": "#F97316", "icon": "🚗", "parent": None},
    {"name": "Housing", "type": "expense", "color": "#DC2626", "icon": "🏠", "parent": None},
    {"name": "Utilities", "type": "expense", "color": "#B91C1C", "icon": "💡", "parent": None},
    {"name": "Entertainment", "type": "expense", "color": "#8B5CF6", "icon": "🎬", "parent": None},
    {"name": "Shopping", "type": "expense", "color": "#EC4899", "icon": "🛍️", "parent": None},
    {"name": "Healthcare", "type": "expense", "color": "#06B6D4", "icon": "🏥", "parent": None},
    {"name": "Personal Care", "type": "expense", "color": "#14B8A6", "icon": "💆", "parent": None},
    {"name": "Education", "type": "expense", "color": "#3B82F6", "icon": "📚", "parent": None},
    {"name": "Travel", "type": "expense", "color": "#6366F1", "icon": "✈️", "parent": None},
    {"name": "Insurance", "type": "expense", "color": "#8B5CF6", "icon": "🛡️", "parent": None},
    {"name": "Subscriptions", "type": "expense", "color": "#A855F7", "icon": "📱", "parent": None},
    {"name": "Pets", "type": "expense", "color": "#D946EF", "icon": "🐾", "parent": None},
    {"name": "Kids", "type": "expense", "color": "#EC4899", "icon": "👶", "parent": None},
    {"name": "Gifts & Donations", "type": "expense", "color": "#F43F5E", "icon": "🎁", "parent": None},
    # Subcategories - Food & Dining
    {"name": "Groceries", "type": "expense", "color": "#F87171", "icon": "🛒", "parent": "Food & Dining"},
    {"name": "Restaurants", "type": "expense", "color": "#FCA5A5", "icon": "🍴", "parent": "Food & Dining"},
    {"name": "Coffee Shops", "type": "expense", "color": "#FECACA", "icon": "☕", "parent": "Food & Dining"},
    {"name": "Fast Food", "type": "expense", "color": "#FEE2E2", "icon": "🍔", "parent": "Food & Dining"},
    {"name": "Alcohol & Bars", "type": "expense", "color": "#FECDD3", "icon": "🍺", "parent": "Food & Dining"},
    # Subcategories - Transportation
    {"name": "Gas & Fuel", "type": "expense", "color": "#FB923C", "icon": "⛽", "parent": "Transportation"},
    {"name": "Parking", "type": "expense", "color": "#FDBA74", "icon": "🅿️", "parent": "Transportation"},
    {"name": "Public Transit", "type": "expense", "color": "#FED7AA", "icon": "🚇", "parent": "Transportation"},
    {"name": "Rideshare", "type": "expense", "color": "#FFEDD5", "icon": "🚕", "parent": "Transportation"},
    {"name": "Car Maintenance", "type": "expense", "color": "#FFF7ED", "icon": "🔧", "parent": "Transportation"},
    # Subcategories - Housing
    {"name": "Rent/Mortgage", "type": "expense", "color": "#F87171", "icon": "🏘️", "parent": "Housing"},
    {"name": "Maintenance", "type": "expense", "color": "#FCA5A5", "icon": "🔧", "parent": "Housing"},
    {"name": "Furniture", "type": "expense", "color": "#FECACA", "icon": "🪑", "parent": "Housing"},
    {"name": "Cleaning", "type": "expense", "color": "#FEE2E2", "icon": "🧹", "parent": "Housing"},
    # Subcategories - Utilities
    {"name": "Electric", "type": "expense", "color": "#FCA5A5", "icon": "⚡", "parent": "Utilities"},
    {"name": "Gas", "type": "expense", "color": "#FECACA", "icon": "🔥", "parent": "Utilities"},
    {"name": "Water", "type": "expense", "color": "#FEE2E2", "icon": "💧", "parent": "Utilities"},
    {"name": "Internet", "type": "expense", "color": "#FECDD3", "icon": "📶", "parent": "Utilities"},
    {"name": "Phone", "type": "expense", "color": "#FFE4E6", "icon": "📞", "parent": "Utilities"},
    # Subcategories - Entertainment
    {"name": "Streaming", "type": "expense", "color": "#A78BFA", "icon": "📺", "parent": "Entertainment"},
    {"name": "Movies & Shows", "type": "expense", "color": "#C4B5FD", "icon": "🎬", "parent": "Entertainment"},
    {"name": "Games", "type": "expense", "color": "#DDD6FE", "icon": "🎮", "parent": "Entertainment"},
    {"name": "Sports & Fitness", "type": "expense", "color": "#EDE9FE", "icon": "🏋️", "parent": "Entertainment"},
    {"name": "Hobbies", "type": "expense", "color": "#F5F3FF", "icon": "🎨", "parent": "Entertainment"},
    # Transfer
    {"name": "Transfer", "type": "transfer", "color": "#6B7280", "icon": "🔄", "parent": None},
]


# Preset metadata for display
PRESET_INFO = {
    "minimal": {
        "id": "minimal",
        "name": "Minimal",
        "description": "Basic income/expense tracking with 7 essential categories",
        "category_count": len(MINIMAL_CATEGORIES),
    },
    "standard": {
        "id": "standard",
        "name": "Standard",
        "description": "Common categories with subcategories for detailed tracking",
        "category_count": len(STANDARD_CATEGORIES),
    },
    "comprehensive": {
        "id": "comprehensive",
        "name": "Comprehensive",
        "description": "Detailed tracking for every spending area with 45+ categories",
        "category_count": len(COMPREHENSIVE_CATEGORIES),
    },
    "empty": {
        "id": "empty",
        "name": "Start Empty",
        "description": "Create all categories manually from scratch",
        "category_count": 0,
    },
}


def get_categories_for_preset(preset: str) -> list[CategoryTemplate]:
    """Get category templates for a given preset."""
    presets = {
        "minimal": MINIMAL_CATEGORIES,
        "standard": STANDARD_CATEGORIES,
        "comprehensive": COMPREHENSIVE_CATEGORIES,
        "empty": [],
    }
    return presets.get(preset, STANDARD_CATEGORIES)
