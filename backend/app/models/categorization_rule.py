from sqlalchemy import Column, Integer, String, Boolean, Numeric, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class CategorizationRule(Base):
    """
    Rules for automatically categorizing transactions based on patterns.

    Rules are evaluated in priority order (higher priority first).
    All non-null conditions must match for a rule to apply.
    """
    __tablename__ = "categorization_rules"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Rule metadata
    name = Column(String(255), nullable=False)
    priority = Column(Integer, default=0, nullable=False)  # Higher = runs first
    enabled = Column(Boolean, default=True, nullable=False)

    # Conditions (all must match, NULL = skip condition)
    # Payee matching
    payee_pattern = Column(String(255), nullable=True)
    payee_match_type = Column(String(20), nullable=True)  # 'contains', 'starts_with', 'ends_with', 'regex', 'exact'

    # Description matching
    description_pattern = Column(String(255), nullable=True)
    description_match_type = Column(String(20), nullable=True)

    # Amount conditions
    amount_min = Column(Numeric(10, 2), nullable=True)
    amount_max = Column(Numeric(10, 2), nullable=True)

    # Transaction type filter
    transaction_type = Column(String(20), nullable=True)  # 'DEBIT', 'CREDIT', 'TRANSFER'

    # Actions (what to apply when rule matches)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    new_payee = Column(String(200), nullable=True)  # Optional: rename payee
    notes_append = Column(String(1000), nullable=True)  # Optional: add to notes

    # Statistics and metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_matched_at = Column(DateTime(timezone=True), nullable=True)
    match_count = Column(Integer, default=0, nullable=False)

    # Auto-learning metadata
    auto_created = Column(Boolean, default=False, nullable=False)  # True if created by learning algorithm
    confidence_score = Column(Numeric(3, 2), nullable=True)  # For auto-created rules: 0.00 to 1.00

    # Relationships
    user = relationship("User", back_populates="categorization_rules")
    category = relationship("Category")

    # Indexes for performance
    __table_args__ = (
        Index('idx_rules_user_enabled_priority', 'user_id', 'enabled', 'priority'),
        Index('idx_rules_user_category', 'user_id', 'category_id'),
    )

    def __repr__(self):
        return f"<CategorizationRule(id={self.id}, name='{self.name}', priority={self.priority}, enabled={self.enabled})>"
