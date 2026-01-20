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


# Pattern Management Schemas

class PayeePatternBase(BaseModel):
    """Base schema for payee matching patterns."""
    pattern_type: str = Field(
        ...,
        description="Pattern type: description_contains, exact_match, fuzzy_match_base"
    )
    pattern_value: str = Field(..., min_length=1, max_length=500)
    confidence_score: Decimal = Field(
        default=Decimal("0.80"),
        ge=Decimal("0.00"),
        le=Decimal("1.00")
    )


class PayeePatternCreate(PayeePatternBase):
    """Schema for creating a new pattern."""
    pass


class PayeePatternUpdate(BaseModel):
    """Schema for updating a pattern."""
    pattern_type: Optional[str] = None
    pattern_value: Optional[str] = Field(None, min_length=1, max_length=500)
    confidence_score: Optional[Decimal] = Field(
        None,
        ge=Decimal("0.00"),
        le=Decimal("1.00")
    )


class PayeePattern(PayeePatternBase):
    """Schema for returning a pattern."""
    id: int
    payee_id: int
    match_count: int = 0
    last_matched_at: Optional[datetime] = None
    source: str
    created_at: datetime

    class Config:
        from_attributes = True


class PatternTestRequest(BaseModel):
    """Schema for testing a pattern against a description."""
    description: str = Field(..., min_length=1, max_length=500)


class PatternTestResult(BaseModel):
    """Schema for pattern test result."""
    matches: bool
    pattern_type: str
    pattern_value: str
    description: str
    match_details: Optional[str] = None
