from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    DATABASE_URL: str

    # Redis
    REDIS_URL: str

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Optional: Plaid Integration
    PLAID_CLIENT_ID: Optional[str] = None
    PLAID_SECRET: Optional[str] = None
    PLAID_ENV: str = "sandbox"

    # Optional: Email
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAIL_FROM: Optional[str] = None

    # Optional: Logo.dev Integration (for merchant icons)
    LOGO_DEV_API_KEY: Optional[str] = None

    @property
    def logo_dev_enabled(self) -> bool:
        """Logo.dev is enabled when an API key is configured."""
        return self.LOGO_DEV_API_KEY is not None

    # Application
    APP_NAME: str = "Shark Fin API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
