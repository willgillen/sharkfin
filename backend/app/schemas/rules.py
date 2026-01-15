from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from decimal import Decimal
from enum import Enum


class MatchType(str, Enum):
    """Text matching methods for payee and description patterns"""
    CONTAINS = "contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    EXACT = "exact"
    REGEX = "regex"


class TransactionTypeFilter(str, Enum):
    """Transaction type filter options"""
    DEBIT = "DEBIT"
    CREDIT = "CREDIT"
    TRANSFER = "TRANSFER"


# Base schema with common fields
class CategorizationRuleBase(BaseModel):
    """Base schema for categorization rules"""
    name: str = Field(..., min_length=1, max_length=255, description="Rule name")
    priority: int = Field(default=0, description="Priority (higher = runs first)")
    enabled: bool = Field(default=True, description="Whether rule is active")

    # Conditions
    payee_pattern: Optional[str] = Field(None, max_length=255, description="Payee pattern to match")
    payee_match_type: Optional[MatchType] = Field(None, description="How to match payee")
    description_pattern: Optional[str] = Field(None, max_length=255, description="Description pattern to match")
    description_match_type: Optional[MatchType] = Field(None, description="How to match description")
    amount_min: Optional[Decimal] = Field(None, ge=0, description="Minimum amount")
    amount_max: Optional[Decimal] = Field(None, ge=0, description="Maximum amount")
    transaction_type: Optional[TransactionTypeFilter] = Field(None, description="Transaction type filter")

    # Actions
    category_id: Optional[int] = Field(None, description="Category to assign")
    new_payee: Optional[str] = Field(None, max_length=200, description="New payee name to set")
    notes_append: Optional[str] = Field(None, max_length=1000, description="Text to append to notes")

    @field_validator('amount_max')
    @classmethod
    def validate_amount_range(cls, v, info):
        """Ensure amount_max >= amount_min if both are set"""
        if v is not None and info.data.get('amount_min') is not None:
            if v < info.data['amount_min']:
                raise ValueError('amount_max must be greater than or equal to amount_min')
        return v

    @field_validator('payee_match_type')
    @classmethod
    def validate_payee_match_type(cls, v, info):
        """If payee_pattern is set, match_type is required"""
        if info.data.get('payee_pattern') and not v:
            raise ValueError('payee_match_type is required when payee_pattern is set')
        return v

    @field_validator('description_match_type')
    @classmethod
    def validate_description_match_type(cls, v, info):
        """If description_pattern is set, match_type is required"""
        if info.data.get('description_pattern') and not v:
            raise ValueError('description_match_type is required when description_pattern is set')
        return v


class CategorizationRuleCreate(CategorizationRuleBase):
    """Schema for creating a new rule"""
    pass


class CategorizationRuleUpdate(BaseModel):
    """Schema for updating an existing rule (all fields optional)"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    priority: Optional[int] = None
    enabled: Optional[bool] = None

    # Conditions
    payee_pattern: Optional[str] = Field(None, max_length=255)
    payee_match_type: Optional[MatchType] = None
    description_pattern: Optional[str] = Field(None, max_length=255)
    description_match_type: Optional[MatchType] = None
    amount_min: Optional[Decimal] = Field(None, ge=0)
    amount_max: Optional[Decimal] = Field(None, ge=0)
    transaction_type: Optional[TransactionTypeFilter] = None

    # Actions
    category_id: Optional[int] = None
    new_payee: Optional[str] = Field(None, max_length=200)
    notes_append: Optional[str] = Field(None, max_length=1000)


class CategorizationRuleResponse(CategorizationRuleBase):
    """Schema for rule responses"""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    last_matched_at: Optional[datetime] = None
    match_count: int
    auto_created: bool
    confidence_score: Optional[Decimal] = None

    class Config:
        from_attributes = True


class RuleMatchResult(BaseModel):
    """Result of matching a transaction against rules"""
    matched: bool
    rule_id: Optional[int] = None
    rule_name: Optional[str] = None
    actions_applied: dict = Field(default_factory=dict)


class RuleTestRequest(BaseModel):
    """Request to test a rule against sample data"""
    payee: Optional[str] = None
    description: Optional[str] = None
    amount: Decimal
    transaction_type: TransactionTypeFilter


class RuleTestResponse(BaseModel):
    """Response from testing a rule"""
    matches: bool
    matched_conditions: list[str] = Field(default_factory=list)
    actions_to_apply: dict = Field(default_factory=dict)


class BulkApplyRulesRequest(BaseModel):
    """Request to apply rules to transactions"""
    transaction_ids: Optional[list[int]] = Field(None, description="Specific transaction IDs, or None for all uncategorized")
    rule_ids: Optional[list[int]] = Field(None, description="Specific rule IDs, or None for all enabled rules")
    overwrite_existing: bool = Field(False, description="Whether to overwrite existing categories")


class BulkApplyRulesResponse(BaseModel):
    """Response from bulk applying rules"""
    total_processed: int
    categorized_count: int
    skipped_count: int
    rules_used: int
    transactions_updated: list[int] = Field(default_factory=list)


class RuleSuggestion(BaseModel):
    """Suggested rule based on user behavior"""
    suggested_name: str
    payee_pattern: Optional[str] = None
    payee_match_type: Optional[MatchType] = None
    description_pattern: Optional[str] = None
    description_match_type: Optional[MatchType] = None
    category_id: int
    category_name: str
    confidence_score: Decimal
    sample_count: int  # Number of transactions this pattern was found in
    priority: int = 100  # Suggested priority
