from fastapi import APIRouter, Depends
from app.api.deps import get_current_active_user
from app.models.user import User as UserModel
from app.schemas.user import User

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
