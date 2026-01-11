from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional
from datetime import datetime, date
from decimal import Decimal
from app.models.budget import BudgetPeriod


class BudgetBase(BaseModel):
    """Base budget schema with common attributes."""
    category_id: int
    name: str
    amount: Decimal
    period: BudgetPeriod
    start_date: date
    end_date: Optional[date] = None
    rollover: bool = False
    alert_enabled: bool = True
    alert_threshold: Decimal = Decimal("90.0")
    notes: Optional[str] = None

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        """Validate amount is positive."""
        if v <= 0:
            raise ValueError("Budget amount must be positive")
        return v

    @field_validator("alert_threshold")
    @classmethod
    def validate_alert_threshold(cls, v: Decimal) -> Decimal:
        """Validate alert threshold is between 0 and 100."""
        if v < 0 or v > 100:
            raise ValueError("Alert threshold must be between 0 and 100")
        return v

    @field_validator("end_date")
    @classmethod
    def validate_end_date(cls, v: Optional[date], info) -> Optional[date]:
        """Validate end_date is after start_date."""
        if v is not None and "start_date" in info.data:
            start_date = info.data["start_date"]
            if v <= start_date:
                raise ValueError("End date must be after start date")
        return v


class BudgetCreate(BudgetBase):
    """Schema for creating a new budget."""
    pass


class BudgetUpdate(BaseModel):
    """Schema for updating budget information."""
    category_id: Optional[int] = None
    name: Optional[str] = None
    amount: Optional[Decimal] = None
    period: Optional[BudgetPeriod] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    rollover: Optional[bool] = None
    alert_enabled: Optional[bool] = None
    alert_threshold: Optional[Decimal] = None
    notes: Optional[str] = None

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """Validate amount is positive."""
        if v is not None and v <= 0:
            raise ValueError("Budget amount must be positive")
        return v

    @field_validator("alert_threshold")
    @classmethod
    def validate_alert_threshold(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """Validate alert threshold is between 0 and 100."""
        if v is not None and (v < 0 or v > 100):
            raise ValueError("Alert threshold must be between 0 and 100")
        return v


class BudgetInDB(BudgetBase):
    """Schema for budget stored in database."""
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class Budget(BudgetInDB):
    """Schema for budget returned in API responses."""
    pass


class BudgetWithProgress(Budget):
    """Schema for budget with progress information."""
    spent: Decimal
    remaining: Decimal
    percentage: Decimal
    is_over_budget: bool
