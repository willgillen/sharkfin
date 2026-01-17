from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, DateTime, Date, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class TransactionType(str, enum.Enum):
    """Transaction type enumeration."""
    DEBIT = "debit"    # Money out (expenses)
    CREDIT = "credit"  # Money in (income)
    TRANSFER = "transfer"  # Between accounts


class Transaction(Base):
    """Transaction model for financial transactions."""

    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True)

    # NEW: Foreign key to Payee entity
    payee_id = Column(Integer, ForeignKey("payees.id", ondelete="SET NULL"), nullable=True, index=True)

    type = Column(SQLEnum(TransactionType), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    date = Column(Date, nullable=False, index=True)

    # LEGACY: String payee field kept for backward compatibility during migration
    # Will be deprecated in future version
    payee = Column(String, nullable=True)

    description = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    # Financial Institution Transaction ID (for OFX/QFX imports)
    # Used for exact duplicate detection
    fitid = Column(String(255), nullable=True, index=True)

    # For transfers
    transfer_account_id = Column(Integer, ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # Relationships
    user = relationship("User", back_populates="transactions")
    account = relationship("Account", foreign_keys=[account_id], backref="transactions")
    category = relationship("Category", backref="transactions")
    transfer_account = relationship("Account", foreign_keys=[transfer_account_id])

    # NEW: Payee entity relationship
    payee_entity = relationship("Payee", back_populates="transactions")

    def __repr__(self):
        return f"<Transaction(id={self.id}, amount={self.amount}, date={self.date}, type='{self.type}')>"
