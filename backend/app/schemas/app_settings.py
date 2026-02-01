"""Schemas for application settings."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class AppSettingBase(BaseModel):
    """Base schema for app settings."""
    key: str = Field(..., max_length=100)
    value: Optional[str] = None
    description: Optional[str] = Field(None, max_length=500)
    is_secret: bool = False


class AppSettingCreate(AppSettingBase):
    """Schema for creating an app setting."""
    pass


class AppSettingUpdate(BaseModel):
    """Schema for updating an app setting."""
    value: Optional[str] = None
    description: Optional[str] = Field(None, max_length=500)


class AppSetting(AppSettingBase):
    """Schema for app setting returned in API responses."""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AppSettingPublic(BaseModel):
    """
    Public schema for app settings - masks secret values.

    Used when returning settings to the frontend to avoid
    exposing sensitive values like API keys.
    """
    key: str
    value: Optional[str] = None
    value_set: bool = False  # Indicates if a value is configured (without revealing it)
    description: Optional[str] = None
    is_secret: bool = False

    class Config:
        from_attributes = True


class LogoDevSettingsUpdate(BaseModel):
    """Schema specifically for updating Logo.dev API key."""
    api_key: Optional[str] = Field(None, description="Logo.dev API key. Set to empty string to clear.")


class LogoDevSettings(BaseModel):
    """Schema for Logo.dev settings response."""
    api_key_configured: bool = False
    description: str = "Logo.dev API key for high-quality merchant logos"
