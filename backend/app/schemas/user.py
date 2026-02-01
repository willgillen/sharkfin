from pydantic import BaseModel, EmailStr, ConfigDict, Field
from typing import Optional, Dict, Any, Literal
from datetime import datetime


class UserPreferences(BaseModel):
    """Schema for user UI preferences."""

    # Icon provider preference
    icon_provider: Literal["simple_icons", "logo_dev"] = Field(
        default="simple_icons",
        description="Preferred icon provider for merchant logos"
    )

    # Transaction display preferences
    transactions_visible_columns: Optional[Dict[str, bool]] = Field(
        default=None,
        description="Which columns to show in transactions table"
    )

    model_config = ConfigDict(extra="allow")  # Allow additional preferences


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
