from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class PayeeBase(BaseModel):
    """Base Payee schema with common fields."""
    canonical_name: str = Field(..., min_length=1, max_length=200)
    default_category_id: Optional[int] = None
    payee_type: Optional[str] = Field(None, max_length=50)
    logo_url: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = None


class PayeeCreate(PayeeBase):
    """Schema for creating a new payee."""
    pass


class PayeeUpdate(BaseModel):
    """Schema for updating a payee (all fields optional)."""
    canonical_name: Optional[str] = Field(None, min_length=1, max_length=200)
    default_category_id: Optional[int] = None
    payee_type: Optional[str] = Field(None, max_length=50)
    logo_url: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = None


class Payee(PayeeBase):
    """Schema for returning a payee (includes computed fields)."""
    id: int
    user_id: int
    transaction_count: int
    last_used_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PayeeWithCategory(Payee):
    """Payee with default category details for autocomplete."""
    default_category_name: Optional[str] = None

    class Config:
        from_attributes = True
