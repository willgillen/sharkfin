from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional
from datetime import datetime
from app.models.category import CategoryType


class CategoryBase(BaseModel):
    """Base category schema with common attributes."""
    name: str
    type: CategoryType
    parent_id: Optional[int] = None
    color: Optional[str] = None
    icon: Optional[str] = None

    @field_validator("color")
    @classmethod
    def validate_color(cls, v: Optional[str]) -> Optional[str]:
        """Validate color is hex format #RRGGBB."""
        if v is not None:
            if not (len(v) == 7 and v.startswith("#")):
                raise ValueError("Color must be hex format #RRGGBB")
        return v


class CategoryCreate(CategoryBase):
    """Schema for creating a new category."""
    pass


class CategoryUpdate(BaseModel):
    """Schema for updating category information."""
    name: Optional[str] = None
    type: Optional[CategoryType] = None
    parent_id: Optional[int] = None
    color: Optional[str] = None
    icon: Optional[str] = None

    @field_validator("color")
    @classmethod
    def validate_color(cls, v: Optional[str]) -> Optional[str]:
        """Validate color is hex format #RRGGBB."""
        if v is not None:
            if not (len(v) == 7 and v.startswith("#")):
                raise ValueError("Color must be hex format #RRGGBB")
        return v


class CategoryInDB(CategoryBase):
    """Schema for category stored in database."""
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class Category(CategoryInDB):
    """Schema for category returned in API responses."""
    pass
