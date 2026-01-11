from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional
from datetime import datetime, date
from decimal import Decimal
from app.models.transaction import TransactionType


class TransactionBase(BaseModel):
    """Base transaction schema with common attributes."""
    account_id: int
    category_id: Optional[int] = None
    type: TransactionType
    amount: Decimal
    date: date
    payee: Optional[str] = None
    description: Optional[str] = None
    notes: Optional[str] = None
    transfer_account_id: Optional[int] = None

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        """Validate amount is positive."""
        if v <= 0:
            raise ValueError("Amount must be positive")
        return v

    @field_validator("transfer_account_id")
    @classmethod
    def validate_transfer(cls, v: Optional[int], info) -> Optional[int]:
        """Validate transfer_account_id is only set for transfer transactions."""
        if v is not None and info.data.get("type") != TransactionType.TRANSFER:
            raise ValueError("transfer_account_id can only be set for transfer transactions")
        return v


class TransactionCreate(TransactionBase):
    """Schema for creating a new transaction."""
    pass


class TransactionUpdate(BaseModel):
    """Schema for updating transaction information."""
    account_id: Optional[int] = None
    category_id: Optional[int] = None
    type: Optional[TransactionType] = None
    amount: Optional[Decimal] = None
    date: Optional[date] = None
    payee: Optional[str] = None
    description: Optional[str] = None
    notes: Optional[str] = None
    transfer_account_id: Optional[int] = None

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """Validate amount is positive."""
        if v is not None and v <= 0:
            raise ValueError("Amount must be positive")
        return v


class TransactionInDB(TransactionBase):
    """Schema for transaction stored in database."""
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class Transaction(TransactionInDB):
    """Schema for transaction returned in API responses."""
    pass
