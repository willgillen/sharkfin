from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional
from datetime import datetime, date
from decimal import Decimal
from app.models.account import AccountType


class AccountBase(BaseModel):
    """Base account schema with common attributes."""
    name: str
    type: AccountType
    institution: Optional[str] = None
    account_number: Optional[str] = None
    currency: str = "USD"
    opening_balance: Decimal = Decimal("0.00")
    opening_balance_date: Optional[date] = None
    notes: Optional[str] = None

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Validate currency is 3-character ISO 4217 code."""
        if len(v) != 3 or not v.isupper():
            raise ValueError("Currency must be 3-character ISO 4217 code (e.g., USD, EUR, GBP)")
        return v

    @field_validator("account_number")
    @classmethod
    def validate_account_number(cls, v: Optional[str]) -> Optional[str]:
        """Validate account number is max 4 digits."""
        if v is not None and len(v) > 4:
            raise ValueError("Account number must be 4 digits or less (last 4 digits)")
        return v


class AccountCreate(AccountBase):
    """Schema for creating a new account."""
    pass


class AccountUpdate(BaseModel):
    """Schema for updating account information."""
    name: Optional[str] = None
    type: Optional[AccountType] = None
    institution: Optional[str] = None
    account_number: Optional[str] = None
    currency: Optional[str] = None
    opening_balance: Optional[Decimal] = None
    opening_balance_date: Optional[date] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: Optional[str]) -> Optional[str]:
        """Validate currency is 3-character ISO 4217 code."""
        if v is not None:
            if len(v) != 3 or not v.isupper():
                raise ValueError("Currency must be 3-character ISO 4217 code (e.g., USD, EUR, GBP)")
        return v

    @field_validator("account_number")
    @classmethod
    def validate_account_number(cls, v: Optional[str]) -> Optional[str]:
        """Validate account number is max 4 digits."""
        if v is not None and len(v) > 4:
            raise ValueError("Account number must be 4 digits or less (last 4 digits)")
        return v


class AccountInDB(AccountBase):
    """Schema for account stored in database."""
    id: int
    user_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class Account(AccountInDB):
    """Schema for account returned in API responses."""
    current_balance: Decimal = Decimal("0.00")  # Calculated field, set by API
