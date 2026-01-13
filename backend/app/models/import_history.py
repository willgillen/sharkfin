from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class ImportHistory(Base):
    __tablename__ = "import_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True)

    # Import metadata
    import_type = Column(String(20), nullable=False)  # csv, ofx, qfx
    filename = Column(String(255), nullable=False)
    file_size = Column(Integer)

    # Results
    total_rows = Column(Integer, nullable=False)
    imported_count = Column(Integer, default=0)
    duplicate_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)

    # Status
    status = Column(String(20), default="pending")  # pending, completed, failed, cancelled
    error_message = Column(Text)

    # Timestamps
    started_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    completed_at = Column(DateTime(timezone=True))

    # Rollback
    can_rollback = Column(Boolean, default=True)

    # Relationships
    user = relationship("User", back_populates="import_history")
    account = relationship("Account")
    imported_transactions = relationship(
        "ImportedTransaction",
        back_populates="import_history",
        cascade="all, delete-orphan"
    )


class ImportedTransaction(Base):
    __tablename__ = "imported_transactions"

    id = Column(Integer, primary_key=True, index=True)
    import_id = Column(Integer, ForeignKey("import_history.id", ondelete="CASCADE"), nullable=False, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id", ondelete="SET NULL"))
    row_number = Column(Integer)  # Original row number in the import file

    # Relationships
    import_history = relationship("ImportHistory", back_populates="imported_transactions")
    transaction = relationship("Transaction")
