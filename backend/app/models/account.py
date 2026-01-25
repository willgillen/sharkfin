from sqlalchemy import Boolean, Column, Integer, String, Numeric, ForeignKey, DateTime, Date, Enum as SQLEnum, case
from sqlalchemy.orm import relationship, Session
from sqlalchemy.sql import func
import enum
from datetime import date as date_type
from decimal import Decimal
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
    current_balance = Column(Numeric(15, 2), default=0, nullable=False)  # DEPRECATED: Will be removed after balance refactor
    opening_balance = Column(Numeric(15, 2), default=0, nullable=False)  # Fixed balance at opening_balance_date
    opening_balance_date = Column(Date, nullable=True)  # Date of opening balance (NULL = from account creation)
    is_active = Column(Boolean, default=True, nullable=False)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # Relationships
    user = relationship("User", back_populates="accounts")

    def calculate_balance(self, db: Session, as_of_date: date_type = None) -> Decimal:
        """
        Calculate the current balance based on opening_balance + transactions.

        Args:
            db: Database session
            as_of_date: Optional date to calculate balance as of (default: today)

        Returns:
            Calculated balance as Decimal
        """
        from app.models.transaction import Transaction, TransactionType

        # Start with opening balance
        balance = self.opening_balance

        # Build query for transactions affecting this account
        query = db.query(
            func.sum(
                case(
                    # Credit: money in (adds to balance)
                    (Transaction.type == TransactionType.CREDIT, Transaction.amount),
                    # Debit: money out (subtracts from balance)
                    (Transaction.type == TransactionType.DEBIT, -Transaction.amount),
                    # Transfer out: subtract from this account
                    ((Transaction.type == TransactionType.TRANSFER) & (Transaction.account_id == self.id), -Transaction.amount),
                    # Transfer in: add to this account
                    ((Transaction.type == TransactionType.TRANSFER) & (Transaction.transfer_account_id == self.id), Transaction.amount),
                    else_=0
                )
            )
        ).filter(
            (Transaction.account_id == self.id) | (Transaction.transfer_account_id == self.id)
        )

        # Filter by opening_balance_date if set
        if self.opening_balance_date:
            query = query.filter(Transaction.date >= self.opening_balance_date)

        # Filter by as_of_date if provided
        if as_of_date:
            query = query.filter(Transaction.date <= as_of_date)

        # Get the sum (returns None if no transactions)
        transaction_sum = query.scalar()

        if transaction_sum:
            balance += transaction_sum

        return balance

    def __repr__(self):
        return f"<Account(id={self.id}, name='{self.name}', type='{self.type}')>"
