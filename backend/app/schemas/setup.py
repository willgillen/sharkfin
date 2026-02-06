"""Setup wizard schemas."""
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class SetupStatus(BaseModel):
    """Response for setup status check."""
    setup_required: bool
    setup_completed: bool


class SetupRequest(BaseModel):
    """Request to complete initial setup."""
    # Admin user details
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: str = Field(..., min_length=1)

    # Seeding options
    create_default_categories: bool = True
    category_preset: str = Field(
        default="standard",
        pattern="^(minimal|standard|comprehensive|empty)$"
    )
    create_sample_data: bool = False


class SetupResponse(BaseModel):
    """Response after completing setup."""
    success: bool
    message: str
    user_id: int
    categories_created: int
    sample_data_created: bool


class CategoryPresetInfo(BaseModel):
    """Information about a category preset."""
    id: str
    name: str
    description: str
    category_count: int


class AvailablePresetsResponse(BaseModel):
    """Response listing available category presets."""
    presets: list[CategoryPresetInfo]
