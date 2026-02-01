"""
Settings API endpoints.

Provides endpoints for retrieving application configuration and
available features that may depend on server-side settings.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.icon_provider_service import get_icon_provider_service
from app.services.app_settings_service import AppSettingsService
from app.schemas.app_settings import LogoDevSettings, LogoDevSettingsUpdate

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/icon-providers")
def get_icon_providers(db: Session = Depends(get_db)):
    """
    Get information about available icon providers.

    Returns which icon providers are available and their configuration status.
    This is used by the frontend to show/hide the icon provider selection
    based on whether logo.dev is configured on the server.
    """
    service = get_icon_provider_service(db)
    return service.get_icon_provider_status()


@router.get("/logo-dev", response_model=LogoDevSettings)
def get_logo_dev_settings(db: Session = Depends(get_db)):
    """
    Get Logo.dev configuration status.

    Returns whether an API key is configured (without revealing the key itself).
    """
    settings_service = AppSettingsService(db)
    return LogoDevSettings(
        api_key_configured=settings_service.is_logo_dev_configured(),
        description="Logo.dev API key for high-quality merchant logos",
    )


@router.put("/logo-dev", response_model=LogoDevSettings)
def update_logo_dev_settings(
    settings: LogoDevSettingsUpdate,
    db: Session = Depends(get_db),
):
    """
    Update Logo.dev API key.

    Set the API key to enable Logo.dev integration, or set to empty/null to disable.
    """
    settings_service = AppSettingsService(db)

    # Handle empty string as "clear the key"
    api_key = settings.api_key
    if api_key == "":
        api_key = None

    settings_service.set_logo_dev_api_key(api_key)

    # Clear the cached icon provider service so it picks up the new key
    from app.services import icon_provider_service
    icon_provider_service._icon_provider_service = None

    return LogoDevSettings(
        api_key_configured=settings_service.is_logo_dev_configured(),
        description="Logo.dev API key for high-quality merchant logos",
    )
