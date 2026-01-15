from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Payee(Base):
    """
    Payee entity for normalizing transaction payees/sources.

    Stores canonical payee names with metadata such as default category,
    payee type, and usage statistics. Supports both expense payees and
    income sources through a unified entity.
    """
    __tablename__ = "payees"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Core identity
    canonical_name = Column(String(200), nullable=False)

    # Metadata
    default_category_id = Column(
        Integer,
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True
    )
    payee_type = Column(String(50), nullable=True)  # 'grocery', 'restaurant', 'gas', etc.
    logo_url = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)

    # Usage statistics
    transaction_count = Column(Integer, default=0, nullable=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        onupdate=func.now(),
        nullable=True
    )

    # Relationships
    user = relationship("User", back_populates="payees")
    default_category = relationship("Category")
    transactions = relationship("Transaction", back_populates="payee_entity")

    # Table args for indexes
    __table_args__ = (
        # Unique constraint: one canonical name per user
        Index('idx_payees_unique_user_canonical', 'user_id', 'canonical_name', unique=True),
        # Autocomplete optimization: search by user and rank by usage
        Index('idx_payees_autocomplete', 'user_id', 'transaction_count', 'last_used_at'),
    )

    def __repr__(self):
        return f"<Payee(id={self.id}, name='{self.canonical_name}', user_id={self.user_id})>"
