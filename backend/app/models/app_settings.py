"""
AppSettings model for storing application-wide configuration.

This table stores global settings that apply to the entire application,
such as API keys for third-party services.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.sql import func
from app.core.database import Base


class AppSettings(Base):
    """
    Application-wide settings storage.

    Uses a key-value pattern for flexibility. Sensitive values like API keys
    are stored encrypted or masked when returned via API.
    """

    __tablename__ = "app_settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, index=True, nullable=False)
    value = Column(Text, nullable=True)
    description = Column(String(500), nullable=True)
    is_secret = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    def __repr__(self):
        return f"<AppSettings(key='{self.key}')>"


# Well-known setting keys
class SettingKeys:
    """Constants for well-known setting keys."""
    LOGO_DEV_API_KEY = "logo_dev_api_key"
