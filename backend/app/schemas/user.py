from pydantic import BaseModel, EmailStr, ConfigDict, Field
from typing import Optional, Dict, Any, Literal, List
from datetime import datetime


class UserPreferences(BaseModel):
    """
    Schema for user UI preferences.

    All fields are optional - missing values use defaults from UserPreferencesService.
    """

    # Display preferences
    date_format: Optional[Literal["MM/DD/YYYY", "DD/MM/YYYY", "YYYY-MM-DD", "MMM D, YYYY"]] = Field(
        default=None,
        description="Date display format"
    )
    number_format: Optional[Literal["1,234.56", "1.234,56", "1 234.56"]] = Field(
        default=None,
        description="Number display format"
    )
    currency_symbol: Optional[str] = Field(
        default=None,
        description="Currency symbol (e.g., $, €, £)"
    )
    currency_position: Optional[Literal["before", "after"]] = Field(
        default=None,
        description="Currency symbol position"
    )
    currency_decimals: Optional[int] = Field(
        default=None,
        ge=0,
        le=4,
        description="Number of decimal places for currency"
    )
    start_of_week: Optional[Literal["sunday", "monday"]] = Field(
        default=None,
        description="First day of the week"
    )

    # Transaction preferences
    transactions_sort_column: Optional[Literal["date", "payee", "amount", "category"]] = Field(
        default=None,
        description="Default sort column for transactions"
    )
    transactions_sort_order: Optional[Literal["asc", "desc"]] = Field(
        default=None,
        description="Default sort order for transactions"
    )
    transactions_rows_per_page: Optional[Literal[25, 50, 100]] = Field(
        default=None,
        description="Number of rows per page in transaction list"
    )
    transactions_visible_columns: Optional[Dict[str, bool]] = Field(
        default=None,
        description="Which columns to show in transactions table"
    )

    # Import preferences
    import_auto_create_payees: Optional[bool] = Field(
        default=None,
        description="Auto-create payees during import"
    )
    import_auto_apply_rules: Optional[bool] = Field(
        default=None,
        description="Auto-apply rules during import"
    )
    import_duplicate_strictness: Optional[Literal["strict", "moderate", "relaxed"]] = Field(
        default=None,
        description="Duplicate detection strictness"
    )
    import_default_account_id: Optional[int] = Field(
        default=None,
        description="Default account for imports"
    )

    # Appearance preferences
    icon_provider: Optional[Literal["simple_icons", "logo_dev"]] = Field(
        default=None,
        description="Preferred icon provider for merchant logos"
    )

    model_config = ConfigDict(extra="allow")  # Allow additional preferences


class UserPreferencesUpdate(BaseModel):
    """Schema for partial preference updates."""

    # All fields optional for partial updates
    date_format: Optional[str] = None
    number_format: Optional[str] = None
    currency_symbol: Optional[str] = None
    currency_position: Optional[str] = None
    currency_decimals: Optional[int] = None
    start_of_week: Optional[str] = None
    transactions_sort_column: Optional[str] = None
    transactions_sort_order: Optional[str] = None
    transactions_rows_per_page: Optional[int] = None
    transactions_visible_columns: Optional[Dict[str, bool]] = None
    import_auto_create_payees: Optional[bool] = None
    import_auto_apply_rules: Optional[bool] = None
    import_duplicate_strictness: Optional[str] = None
    import_default_account_id: Optional[int] = None
    icon_provider: Optional[str] = None

    model_config = ConfigDict(extra="forbid")  # Reject unknown keys


class UserPreferencesResponse(BaseModel):
    """Schema for preferences response with merged defaults."""

    # Display preferences
    date_format: str
    number_format: str
    currency_symbol: str
    currency_position: str
    currency_decimals: int
    start_of_week: str

    # Transaction preferences
    transactions_sort_column: str
    transactions_sort_order: str
    transactions_rows_per_page: int
    transactions_visible_columns: Dict[str, bool]

    # Import preferences
    import_auto_create_payees: bool
    import_auto_apply_rules: bool
    import_duplicate_strictness: str
    import_default_account_id: Optional[int]

    # Appearance preferences
    icon_provider: str


class PreferenceMetadata(BaseModel):
    """Metadata about a single preference for UI rendering."""
    type: str  # "text", "select", "toggle", "number", "column_toggles", "account_select"
    label: str
    description: str
    category: str
    default: Any
    options: Optional[List[Dict[str, Any]]] = None
    min: Optional[int] = None
    max: Optional[int] = None
    columns: Optional[List[str]] = None


class UserBase(BaseModel):
    """Base user schema with common attributes."""
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """Schema for creating a new user."""
    password: str


class UserUpdate(BaseModel):
    """Schema for updating user information."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    ui_preferences: Optional[Dict[str, Any]] = None


class UserInDB(UserBase):
    """Schema for user stored in database."""
    id: int
    is_active: bool
    is_superuser: bool
    ui_preferences: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class User(UserInDB):
    """Schema for user returned in API responses."""
    pass
