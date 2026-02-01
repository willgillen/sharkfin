from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User as UserModel
from app.schemas.user import (
    User,
    UserUpdate,
    UserPreferencesResponse,
    UserPreferencesUpdate,
    PreferenceMetadata,
)
from app.services.user_preferences_service import (
    UserPreferencesService,
    PREFERENCE_CATEGORIES,
)

router = APIRouter()


@router.get("/me", response_model=User)
def get_current_user_info(current_user: UserModel = Depends(get_current_active_user)):
    """
    Get current logged-in user information.

    Args:
        current_user: Current authenticated and active user

    Returns:
        Current user object
    """
    return current_user


# =============================================================================
# Preferences Endpoints
# =============================================================================

@router.get("/me/preferences", response_model=UserPreferencesResponse)
def get_user_preferences(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
):
    """
    Get all user preferences with defaults applied.

    Returns a complete preferences object with user values merged over defaults.
    Missing preferences will have their default values.
    """
    service = UserPreferencesService(db)
    return service.get_user_preferences(current_user)


@router.get("/me/preferences/metadata")
def get_preferences_metadata():
    """
    Get metadata about all available preferences.

    Returns information about each preference including type, label,
    description, options, and default value. Useful for rendering
    settings UI dynamically.
    """
    return {
        "categories": PREFERENCE_CATEGORIES,
        "preferences": UserPreferencesService.get_preference_metadata(),
    }


@router.get("/me/preferences/{category}")
def get_preferences_by_category(
    category: str,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
):
    """
    Get preferences for a specific category.

    Categories: display, transactions, import, appearance
    """
    service = UserPreferencesService(db)
    try:
        return service.get_preferences_by_category(current_user, category)
    except KeyError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/me/preferences", response_model=UserPreferencesResponse)
def update_user_preferences(
    preferences: UserPreferencesUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
):
    """
    Update user preferences (partial update).

    Only the provided fields will be updated; other preferences remain unchanged.
    Use DELETE /me/preferences/{key} to reset a preference to its default.
    """
    service = UserPreferencesService(db)

    # Convert Pydantic model to dict, excluding None values
    updates = {k: v for k, v in preferences.model_dump().items() if v is not None}

    if not updates:
        # No updates provided, just return current preferences
        return service.get_user_preferences(current_user)

    try:
        service.set_preferences(current_user, updates)
        return service.get_user_preferences(current_user)
    except KeyError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/me/preferences/{key}")
def reset_preference(
    key: str,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
):
    """
    Reset a single preference to its default value.

    The preference will be removed from the user's stored preferences,
    causing it to use the default value.
    """
    service = UserPreferencesService(db)
    try:
        service.reset_preference(current_user, key)
        return {"message": f"Preference '{key}' reset to default"}
    except KeyError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/me/preferences")
def reset_all_preferences(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
):
    """
    Reset all preferences to their default values.

    This clears all stored user preferences, reverting everything to defaults.
    """
    service = UserPreferencesService(db)
    service.reset_all_preferences(current_user)
    return {"message": "All preferences reset to defaults"}


@router.delete("/me/preferences/category/{category}")
def reset_category_preferences(
    category: str,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
):
    """
    Reset all preferences in a category to their default values.

    Categories: display, transactions, import, appearance
    """
    service = UserPreferencesService(db)
    try:
        service.reset_category(current_user, category)
        return {"message": f"Preferences in category '{category}' reset to defaults"}
    except KeyError as e:
        raise HTTPException(status_code=400, detail=str(e))
