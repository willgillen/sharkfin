"""
Service for managing application-wide settings.
"""
from typing import Optional
from sqlalchemy.orm import Session

from app.models.app_settings import AppSettings, SettingKeys


class AppSettingsService:
    """Service for managing application settings."""

    def __init__(self, db: Session):
        self.db = db

    def get_setting(self, key: str) -> Optional[AppSettings]:
        """Get a setting by key."""
        return self.db.query(AppSettings).filter(AppSettings.key == key).first()

    def get_setting_value(self, key: str) -> Optional[str]:
        """Get just the value of a setting by key."""
        setting = self.get_setting(key)
        return setting.value if setting else None

    def set_setting(
        self,
        key: str,
        value: Optional[str],
        description: Optional[str] = None,
        is_secret: bool = False,
    ) -> AppSettings:
        """Set a setting value, creating it if it doesn't exist."""
        setting = self.get_setting(key)

        if setting:
            setting.value = value
            if description is not None:
                setting.description = description
        else:
            setting = AppSettings(
                key=key,
                value=value,
                description=description,
                is_secret=is_secret,
            )
            self.db.add(setting)

        self.db.commit()
        self.db.refresh(setting)
        return setting

    def delete_setting(self, key: str) -> bool:
        """Delete a setting by key."""
        setting = self.get_setting(key)
        if setting:
            self.db.delete(setting)
            self.db.commit()
            return True
        return False

    def get_logo_dev_api_key(self) -> Optional[str]:
        """Get the Logo.dev API key."""
        return self.get_setting_value(SettingKeys.LOGO_DEV_API_KEY)

    def set_logo_dev_api_key(self, api_key: Optional[str]) -> AppSettings:
        """Set the Logo.dev API key."""
        return self.set_setting(
            key=SettingKeys.LOGO_DEV_API_KEY,
            value=api_key if api_key else None,
            description="Logo.dev API key for high-quality merchant logos",
            is_secret=True,
        )

    def is_logo_dev_configured(self) -> bool:
        """Check if Logo.dev API key is configured."""
        api_key = self.get_logo_dev_api_key()
        return api_key is not None and len(api_key) > 0


def get_logo_dev_api_key_from_db(db: Session) -> Optional[str]:
    """
    Convenience function to get Logo.dev API key from database.

    This is used by the IconProviderService to check for API key.
    """
    service = AppSettingsService(db)
    return service.get_logo_dev_api_key()
