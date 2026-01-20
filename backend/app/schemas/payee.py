from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal


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


class PayeeTransaction(BaseModel):
    """Schema for a transaction in the payee's transaction list."""
    id: int
    date: date
    amount: Decimal
    type: str
    account_id: int
    account_name: str
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    description: Optional[str] = None

    class Config:
        from_attributes = True


class PayeeStats(BaseModel):
    """Schema for payee spending statistics."""
    total_spent_all_time: Decimal = Field(default=Decimal("0.00"))
    total_spent_this_month: Decimal = Field(default=Decimal("0.00"))
    total_spent_this_year: Decimal = Field(default=Decimal("0.00"))
    total_income_all_time: Decimal = Field(default=Decimal("0.00"))
    average_transaction_amount: Optional[Decimal] = None
    transaction_count: int = 0
    first_transaction_date: Optional[date] = None
    last_transaction_date: Optional[date] = None

    class Config:
        from_attributes = True
