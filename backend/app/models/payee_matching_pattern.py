"""
Payee Matching Pattern Model

Stores learned patterns for intelligent payee matching during imports.
Each pattern represents a way to identify a specific payee from transaction descriptions.
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Numeric, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class PayeeMatchingPattern(Base):
    """
    Learned pattern for matching transaction descriptions to payees.

    Patterns are created from:
    - User's import decisions (when they accept a match or create a payee)
    - Known merchant configurations
    - Manual pattern creation

    The system learns over time by increasing confidence_score and match_count
    when patterns successfully match transactions.
    """
    __tablename__ = "payee_matching_patterns"

    id = Column(Integer, primary_key=True, index=True)
    payee_id = Column(
        Integer,
        ForeignKey("payees.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Pattern data
    pattern_type = Column(String(50), nullable=False)
    # Pattern types:
    #   'description_contains' - Simple substring match (case-insensitive)
    #   'description_regex' - Regex pattern match
    #   'exact_match' - Exact canonical name match
    #   'fuzzy_match_base' - Base name for fuzzy Levenshtein matching

    pattern_value = Column(String(500), nullable=False)
    # The actual pattern text (e.g., "UBER", "STARBUCKS", "COUNTRY STORE")

    # Learning metadata
    confidence_score = Column(
        Numeric(precision=3, scale=2),
        nullable=False,
        default=0.80
    )
    # Confidence score from 0.00 to 1.00
    # Increases when pattern successfully matches and user accepts
    # Decreases when user rejects a match

    match_count = Column(Integer, nullable=False, default=0)
    # How many times this pattern has successfully matched

    last_matched_at = Column(DateTime(timezone=True), nullable=True)
    # Last time this pattern was used to match a transaction

    # Source tracking
    source = Column(String(50), nullable=False)
    # Source of pattern:
    #   'import_learning' - Learned from user's import decisions
    #   'user_created' - Manually created by user
    #   'known_merchant' - From known_merchants.json
    #   'migration' - Created during data migration

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    payee = relationship("Payee", back_populates="patterns")
    user = relationship("User", back_populates="payee_patterns")

    # Indexes for performance
    __table_args__ = (
        # Unique constraint: one pattern_value of each type per payee
        Index(
            'idx_payee_patterns_unique',
            'payee_id', 'pattern_type', 'pattern_value',
            unique=True
        ),
        # Index for pattern matching queries
        Index('idx_payee_patterns_user_payee', 'user_id', 'payee_id'),
        # Index for contains queries on pattern_value
        Index('idx_payee_patterns_value', 'pattern_value'),
    )

    def __repr__(self):
        return (
            f"<PayeeMatchingPattern("
            f"id={self.id}, "
            f"payee_id={self.payee_id}, "
            f"type='{self.pattern_type}', "
            f"value='{self.pattern_value}', "
            f"confidence={self.confidence_score})>"
        )
