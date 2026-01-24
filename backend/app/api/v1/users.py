from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User as UserModel
from app.schemas.user import User, UserUpdate

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


@router.patch("/me/preferences", response_model=User)
def update_user_preferences(
    preferences: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Update user UI preferences.

    Args:
        preferences: UI preferences dictionary (e.g., visible columns, theme, etc.)
        db: Database session
        current_user: Current authenticated user

    Returns:
        Updated user object
    """
    current_user.ui_preferences = preferences
    db.commit()
    db.refresh(current_user)
    return current_user
