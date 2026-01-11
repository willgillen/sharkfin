from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, DateTime, Date, Enum as SQLEnum, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class BudgetPeriod(str, enum.Enum):
    """Budget period enumeration."""
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class Budget(Base):
    """Budget model for financial budgets."""

    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=False, index=True)

    name = Column(String, nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)  # Budget limit
    period = Column(SQLEnum(BudgetPeriod), nullable=False, default=BudgetPeriod.MONTHLY)

    start_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=True, index=True)  # NULL means ongoing

    rollover = Column(Boolean, default=False, nullable=False)  # Allow unused amounts to carry forward
    alert_enabled = Column(Boolean, default=True, nullable=False)
    alert_threshold = Column(Numeric(5, 2), default=90.0, nullable=False)  # Alert at 90%

    notes = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # Relationships
    user = relationship("User", back_populates="budgets")
    category = relationship("Category", backref="budgets")

    def __repr__(self):
        return f"<Budget(id={self.id}, name='{self.name}', amount={self.amount}, period='{self.period}')>"
