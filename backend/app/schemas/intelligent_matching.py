"""
Pydantic schemas for intelligent payee matching.

Used for the new intelligent import flow that supports:
- Pattern-based matching to existing payees
- Fuzzy matching with confidence tiers
- Learning from user decisions
"""
from typing import List, Optional
from pydantic import BaseModel, Field
from decimal import Decimal


# ============================================================================
# Response Schemas (Analysis Results)
# ============================================================================

class AlternativeMatchSchema(BaseModel):
    """A potential payee match shown as an alternative to user."""
    payee_id: int
    payee_name: str
    confidence: float = Field(ge=0.0, le=1.0)

    class Config:
        from_attributes = True


class TransactionPayeeAnalysisSchema(BaseModel):
    """Result of analyzing one transaction for payee matching."""
    transaction_index: int
    original_description: str
    extracted_payee_name: str
    extraction_confidence: float = Field(ge=0.0, le=1.0)

    # Matching results
    match_type: str = Field(
        description="HIGH_CONFIDENCE, LOW_CONFIDENCE, or NO_MATCH"
    )
    matched_payee_id: Optional[int] = None
    matched_payee_name: Optional[str] = None
    match_confidence: float = Field(ge=0.0, le=1.0)
    match_reason: str

    # Suggested category (from known merchants or matched payee's default)
    suggested_category: Optional[str] = Field(
        None,
        description="Category name from known merchants config or matched payee's default category"
    )

    # Alternatives for user selection
    alternative_matches: List[AlternativeMatchSchema] = []

    class Config:
        from_attributes = True


class IntelligentAnalysisSummarySchema(BaseModel):
    """Summary statistics for intelligent analysis."""
    high_confidence_matches: int
    low_confidence_matches: int
    new_payees_needed: int
    total_transactions: int

    # Breakdown of which existing payees were matched and how often
    existing_payees_matched: List[dict] = Field(
        description="List of {payee_id, name, count} for matched payees"
    )


class IntelligentPayeeAnalysisResponse(BaseModel):
    """Response from /analyze-payees-intelligent endpoint."""
    analyses: List[TransactionPayeeAnalysisSchema]
    summary: IntelligentAnalysisSummarySchema


# ============================================================================
# Request Schemas (Import Execution with Decisions)
# ============================================================================

class PayeeAssignmentDecision(BaseModel):
    """User's decision for one transaction's payee assignment."""
    transaction_index: int
    original_description: str

    # User can choose EITHER existing payee OR create new one
    payee_id: Optional[int] = Field(
        None,
        description="Existing payee ID if user selected existing payee"
    )
    new_payee_name: Optional[str] = Field(
        None,
        description="New payee name if user wants to create new payee"
    )
    new_payee_category: Optional[str] = Field(
        None,
        description="Category name for new payee (from suggested_category or user selection)"
    )

    # Whether to create/strengthen pattern from this decision
    create_pattern: bool = Field(
        True,
        description="Whether to learn from this decision (default: True)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "transaction_index": 0,
                "original_description": "UBER TRIP 12345 SF CA",
                "payee_id": 42,
                "new_payee_name": None,
                "new_payee_category": None,
                "create_pattern": True
            }
        }


class ImportWithPayeeDecisionsRequest(BaseModel):
    """Request for executing import with user's payee decisions."""
    account_id: int
    skip_rows: List[int] = Field(
        default_factory=list,
        description="Row indices to skip (0-indexed)"
    )

    # Per-transaction payee assignments from user's review
    payee_assignments: List[PayeeAssignmentDecision] = Field(
        description="User's payee decisions for each transaction"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "account_id": 1,
                "skip_rows": [2, 5],
                "payee_assignments": [
                    {
                        "transaction_index": 0,
                        "original_description": "UBER TRIP 12345",
                        "payee_id": 42,
                        "new_payee_name": None,
                        "create_pattern": True
                    },
                    {
                        "transaction_index": 1,
                        "original_description": "LOCAL BAKERY COFFEE",
                        "payee_id": None,
                        "new_payee_name": "Local Bakery",
                        "create_pattern": True
                    }
                ]
            }
        }


# ============================================================================
# Pattern Management Schemas (Future use)
# ============================================================================

class PayeePatternSchema(BaseModel):
    """Schema for payee matching pattern."""
    id: int
    payee_id: int
    pattern_type: str
    pattern_value: str
    confidence_score: Decimal
    match_count: int
    source: str

    class Config:
        from_attributes = True


class CreatePatternRequest(BaseModel):
    """Request to manually create a pattern for a payee."""
    payee_id: int
    pattern_type: str = Field(
        description="description_contains, exact_match, fuzzy_match_base, description_regex"
    )
    pattern_value: str
    confidence_score: Optional[Decimal] = Field(
        default=Decimal("0.80"),
        ge=Decimal("0.00"),
        le=Decimal("1.00")
    )
