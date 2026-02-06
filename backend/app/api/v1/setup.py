"""Setup wizard API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.schemas.setup import (
    SetupStatus,
    SetupRequest,
    SetupResponse,
    CategoryPresetInfo,
    AvailablePresetsResponse,
)
from app.services.setup_service import SetupService
from app.db.category_templates import PRESET_INFO

router = APIRouter()


@router.get("/status", response_model=SetupStatus)
def get_setup_status(db: Session = Depends(get_db)):
    """
    Check if initial setup is required.

    Returns setup_required=True if no users exist in the database.
    This endpoint is public (no authentication required).
    """
    user_count = db.query(User).count()
    return SetupStatus(
        setup_required=user_count == 0,
        setup_completed=user_count > 0
    )


@router.get("/presets", response_model=AvailablePresetsResponse)
def get_available_presets(db: Session = Depends(get_db)):
    """
    Get available category presets.

    Returns list of available preset options with metadata.
    This endpoint is public (no authentication required).
    """
    # Verify setup is still required
    user_count = db.query(User).count()
    if user_count > 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Setup has already been completed"
        )

    presets = [
        CategoryPresetInfo(
            id=info["id"],
            name=info["name"],
            description=info["description"],
            category_count=info["category_count"]
        )
        for info in PRESET_INFO.values()
    ]

    return AvailablePresetsResponse(presets=presets)


@router.post("/complete", response_model=SetupResponse, status_code=status.HTTP_201_CREATED)
def complete_setup(
    setup_data: SetupRequest,
    db: Session = Depends(get_db)
):
    """
    Complete initial setup.

    Creates the admin user, seeds categories based on preset,
    and optionally creates sample data.

    This endpoint is public but only works when no users exist.
    """
    # Verify setup is still required
    user_count = db.query(User).count()
    if user_count > 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Setup has already been completed"
        )

    # Validate preset
    if setup_data.category_preset not in PRESET_INFO:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid category preset: {setup_data.category_preset}"
        )

    try:
        # Create admin user
        admin_user = SetupService.create_admin_user(
            db=db,
            email=setup_data.email,
            password=setup_data.password,
            full_name=setup_data.full_name
        )

        # Seed categories if requested
        categories_created = 0
        if setup_data.create_default_categories:
            categories_created = SetupService.seed_categories(
                db=db,
                user_id=admin_user.id,
                preset=setup_data.category_preset
            )

        # Seed sample data if requested
        sample_data_created = False
        if setup_data.create_sample_data:
            # Sample data requires categories
            if categories_created > 0:
                sample_data_created = SetupService.seed_sample_data(
                    db=db,
                    user_id=admin_user.id
                )

        return SetupResponse(
            success=True,
            message="Setup completed successfully",
            user_id=admin_user.id,
            categories_created=categories_created,
            sample_data_created=sample_data_created
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Setup failed: {str(e)}"
        )
