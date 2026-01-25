from sqlalchemy import Boolean, Column, Integer, String, Numeric, ForeignKey, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class AccountType(str, enum.Enum):
    """Account type enumeration."""
    CHECKING = "checking"
    SAVINGS = "savings"
    CREDIT_CARD = "credit_card"
    LOAN = "loan"
    INVESTMENT = "investment"
    CASH = "cash"
    OTHER = "other"


class Account(Base):
    """Account model for financial accounts."""

    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    type = Column(SQLEnum(AccountType), nullable=False)
    institution = Column(String, nullable=True)  # Financial institution name (e.g., "Chase", "Bank of America")
    account_number = Column(String(4), nullable=True)  # Last 4 digits of account number for identification
    currency = Column(String(3), default="USD", nullable=False)  # ISO 4217 currency code
    current_balance = Column(Numeric(15, 2), default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # Relationships
    user = relationship("User", back_populates="accounts")

    def __repr__(self):
        return f"<Account(id={self.id}, name='{self.name}', type='{self.type}')>"
