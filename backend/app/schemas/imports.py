from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class ImportType(str, Enum):
    CSV = "csv"
    OFX = "ofx"
    QFX = "qfx"


class ImportStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# CSV Column Mapping
class CSVColumnMapping(BaseModel):
    date: str = Field(..., description="Column name for transaction date")
    amount: str = Field(..., description="Column name for amount")
    description: Optional[str] = Field(None, description="Column name for description")
    payee: Optional[str] = Field(None, description="Column name for payee")
    category: Optional[str] = Field(None, description="Column name for category")
    notes: Optional[str] = Field(None, description="Column name for notes")


# Upload response
class CSVPreviewResponse(BaseModel):
    columns: List[str]
    sample_rows: List[Dict[str, Any]]
    detected_format: Optional[str] = None  # "mint", "chase", "bofa", "generic"
    suggested_mapping: Optional[CSVColumnMapping] = None
    row_count: int


class OFXPreviewResponse(BaseModel):
    account_name: str
    account_type: str
    account_number: Optional[str] = None
    bank_name: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    transaction_count: int
    sample_transactions: List[Dict[str, Any]]


# Duplicate detection
class PotentialDuplicate(BaseModel):
    existing_transaction_id: int
    existing_date: str
    existing_amount: str
    existing_description: Optional[str] = None
    new_transaction: Dict[str, Any]
    confidence_score: float  # 0.0 to 1.0


class DuplicatesResponse(BaseModel):
    duplicates: List[PotentialDuplicate]
    total_new_transactions: int
    total_duplicates: int


class ImportPreviewRequest(BaseModel):
    account_id: int
    column_mapping: Optional[CSVColumnMapping] = None
    skip_duplicates: List[int] = Field(default_factory=list)  # Row numbers to skip


class ImportExecuteRequest(BaseModel):
    account_id: int
    column_mapping: Optional[CSVColumnMapping] = None
    skip_rows: List[int] = Field(default_factory=list)  # Rows to skip (duplicates)


class ImportExecuteResponse(BaseModel):
    import_id: int
    status: ImportStatus
    total_rows: int
    imported_count: int
    duplicate_count: int
    error_count: int
    message: str


# Import history
class ImportHistoryResponse(BaseModel):
    id: int
    import_type: ImportType
    filename: str
    file_size: Optional[int] = None
    account_id: Optional[int] = None
    account_name: Optional[str] = None
    total_rows: int
    imported_count: int
    duplicate_count: int
    error_count: int
    status: ImportStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    can_rollback: bool
    original_file_name: Optional[str] = None
    original_file_size: Optional[int] = None
    has_file_data: bool = False

    class Config:
        from_attributes = True


# Smart Rule Suggestions during Import
class SmartRuleSuggestionResponse(BaseModel):
    """Smart rule suggestion detected during import analysis."""
    suggested_name: str
    payee_pattern: str
    payee_match_type: str
    matching_row_indices: List[int]
    sample_descriptions: List[str]
    confidence: float
    detected_merchant: Optional[str] = None
    extracted_payee_name: Optional[str] = None
    extraction_confidence: Optional[float] = None


class AnalyzeImportForRulesRequest(BaseModel):
    """Request to analyze import data for smart rule suggestions."""
    transactions: List[Dict[str, Any]]
    min_occurrences: int = Field(default=2, ge=1, description="Minimum times pattern must appear")
    min_confidence: float = Field(default=0.6, ge=0.0, le=1.0, description="Minimum confidence score")


class AnalyzeImportForRulesResponse(BaseModel):
    """Response with smart rule suggestions."""
    suggestions: List[SmartRuleSuggestionResponse]
    total_transactions_analyzed: int
    total_suggestions: int
