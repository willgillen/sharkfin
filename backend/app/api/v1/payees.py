from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.schemas.payee import (
    Payee, PayeeCreate, PayeeUpdate, PayeeWithCategory,
    PayeeTransaction, PayeeStats,
    PayeePattern, PayeePatternCreate, PayeePatternUpdate,
    PatternTestRequest, PatternTestResult,
    IconSuggestion, IconParsed
)
from app.services.payee_service import PayeeService
from app.services.payee_icon_service import payee_icon_service

router = APIRouter()


@router.get("", response_model=List[PayeeWithCategory])
def get_payees(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    q: Optional[str] = Query(None, description="Search query for payee name"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> List[PayeeWithCategory]:
    """
    Get all payees for the current user.

    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return (default: 100, max: 500)
    - **q**: Optional search query to filter by payee name

    Returns payees with default_category_name included for display.
    """
    service = PayeeService(db)

    if q:
        # If search query provided, use search_payees
        payees = service.search_payees(
            user_id=current_user.id,
            query=q,
            limit=limit
        )
    else:
        # Otherwise, get all payees with pagination
        payees = service.get_all(
            user_id=current_user.id,
            skip=skip,
            limit=limit
        )

    # Enrich with category information
    results = []
    for payee in payees:
        payee_dict = {
            "id": payee.id,
            "user_id": payee.user_id,
            "canonical_name": payee.canonical_name,
            "default_category_id": payee.default_category_id,
            "payee_type": payee.payee_type,
            "logo_url": payee.logo_url,
            "notes": payee.notes,
            "transaction_count": payee.transaction_count,
            "last_used_at": payee.last_used_at,
            "created_at": payee.created_at,
            "updated_at": payee.updated_at,
            "default_category_name": None
        }

        # Add category name if available
        if payee.default_category:
            payee_dict["default_category_name"] = payee.default_category.name

        results.append(PayeeWithCategory(**payee_dict))

    return results


@router.get("/autocomplete", response_model=List[PayeeWithCategory])
def autocomplete_payees(
    q: str = Query(..., min_length=1, description="Search query for autocomplete"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> List[PayeeWithCategory]:
    """
    Autocomplete endpoint for payee search in transaction forms.

    Returns payees ranked by:
    1. Exact name match
    2. Starts with query
    3. Contains query
    4. Usage frequency and recency

    Includes default category information for each payee.
    """
    service = PayeeService(db)
    payees = service.search_payees(
        user_id=current_user.id,
        query=q,
        limit=limit
    )

    # Enrich with category information
    results = []
    for payee in payees:
        payee_dict = {
            "id": payee.id,
            "user_id": payee.user_id,
            "canonical_name": payee.canonical_name,
            "default_category_id": payee.default_category_id,
            "payee_type": payee.payee_type,
            "logo_url": payee.logo_url,
            "notes": payee.notes,
            "transaction_count": payee.transaction_count,
            "last_used_at": payee.last_used_at,
            "created_at": payee.created_at,
            "updated_at": payee.updated_at,
            "default_category_name": None
        }

        # Add category name if available
        if payee.default_category:
            payee_dict["default_category_name"] = payee.default_category.name

        results.append(PayeeWithCategory(**payee_dict))

    return results


@router.post("", response_model=Payee)
def create_payee(
    payee_data: PayeeCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Payee:
    """
    Create a new payee.

    Note: This uses get_or_create internally to avoid duplicates.
    If a payee with the same canonical name already exists, it will be returned.
    """
    service = PayeeService(db)
    return service.create(
        user_id=current_user.id,
        payee_data=payee_data
    )


@router.get("/{payee_id}", response_model=Payee)
def get_payee(
    payee_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Payee:
    """
    Get a specific payee by ID.
    """
    service = PayeeService(db)
    payee = service.get_by_id(payee_id, current_user.id)

    if not payee:
        raise HTTPException(status_code=404, detail="Payee not found")

    return payee


@router.put("/{payee_id}", response_model=Payee)
def update_payee(
    payee_id: int,
    payee_data: PayeeUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Payee:
    """
    Update a payee's metadata.

    You can update:
    - canonical_name
    - default_category_id
    - payee_type
    - logo_url
    - notes
    """
    service = PayeeService(db)
    payee = service.update(
        payee_id=payee_id,
        user_id=current_user.id,
        payee_data=payee_data
    )

    if not payee:
        raise HTTPException(status_code=404, detail="Payee not found")

    return payee


@router.get("/{payee_id}/transactions", response_model=List[PayeeTransaction])
def get_payee_transactions(
    payee_id: int,
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> List[PayeeTransaction]:
    """
    Get recent transactions for a specific payee.

    - **payee_id**: ID of the payee
    - **limit**: Maximum number of transactions to return (default: 50, max: 100)

    Returns transactions sorted by date (newest first) with account and category names.
    """
    service = PayeeService(db)

    # Verify payee exists first
    payee = service.get_by_id(payee_id, current_user.id)
    if not payee:
        raise HTTPException(status_code=404, detail="Payee not found")

    transactions = service.get_transactions(
        payee_id=payee_id,
        user_id=current_user.id,
        limit=limit
    )

    return [PayeeTransaction(**txn) for txn in transactions]


@router.get("/{payee_id}/stats", response_model=PayeeStats)
def get_payee_stats(
    payee_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> PayeeStats:
    """
    Get spending statistics for a specific payee.

    Returns:
    - Total spent all time (debit transactions)
    - Total spent this month
    - Total spent this year
    - Total income all time (credit transactions)
    - Average transaction amount
    - Total transaction count
    - First and last transaction dates
    """
    service = PayeeService(db)
    stats = service.get_stats(payee_id, current_user.id)

    if stats is None:
        raise HTTPException(status_code=404, detail="Payee not found")

    return PayeeStats(**stats)


@router.delete("/{payee_id}")
def delete_payee(
    payee_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> dict:
    """
    Delete a payee.

    Note: This will set transactions.payee_id to NULL for all transactions
    referencing this payee (due to ON DELETE SET NULL constraint).
    """
    service = PayeeService(db)
    success = service.delete(payee_id, current_user.id)

    if not success:
        raise HTTPException(status_code=404, detail="Payee not found")

    return {"message": "Payee deleted successfully"}


# ============================================================================
# Pattern Management Endpoints
# ============================================================================

@router.get("/{payee_id}/patterns", response_model=List[PayeePattern])
def get_payee_patterns(
    payee_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> List[PayeePattern]:
    """
    Get all matching patterns for a specific payee.

    Returns patterns sorted by confidence score (highest first).

    Pattern types:
    - **description_contains**: Substring match in transaction description
    - **exact_match**: Exact match of extracted payee name
    - **fuzzy_match_base**: Base name for fuzzy Levenshtein matching
    - **description_regex**: Regex pattern match (advanced)
    """
    service = PayeeService(db)

    # Verify payee exists first
    payee = service.get_by_id(payee_id, current_user.id)
    if not payee:
        raise HTTPException(status_code=404, detail="Payee not found")

    patterns = service.get_patterns(payee_id, current_user.id)
    return patterns


@router.post("/{payee_id}/patterns", response_model=PayeePattern)
def create_payee_pattern(
    payee_id: int,
    pattern_data: PayeePatternCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> PayeePattern:
    """
    Create a new matching pattern for a payee.

    If a pattern with the same type and value already exists, it will be
    updated with the new confidence score instead of creating a duplicate.

    Pattern types:
    - **description_contains**: Substring match (case-insensitive)
    - **exact_match**: Exact match of extracted payee name
    - **fuzzy_match_base**: Base for fuzzy matching (80% similarity threshold)
    - **description_regex**: Regex pattern (advanced users)
    """
    service = PayeeService(db)

    # Verify payee exists first
    payee = service.get_by_id(payee_id, current_user.id)
    if not payee:
        raise HTTPException(status_code=404, detail="Payee not found")

    # Validate pattern type
    valid_types = ["description_contains", "exact_match", "fuzzy_match_base", "description_regex"]
    if pattern_data.pattern_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid pattern type. Must be one of: {', '.join(valid_types)}"
        )

    # Validate pattern value length for description_contains
    if (pattern_data.pattern_type == "description_contains" and
            len(pattern_data.pattern_value) < 4):
        raise HTTPException(
            status_code=400,
            detail="Pattern value must be at least 4 characters for description_contains type"
        )

    pattern = service.create_pattern(
        payee_id=payee_id,
        user_id=current_user.id,
        pattern_type=pattern_data.pattern_type,
        pattern_value=pattern_data.pattern_value,
        confidence_score=float(pattern_data.confidence_score)
    )

    return pattern


@router.put("/patterns/{pattern_id}", response_model=PayeePattern)
def update_payee_pattern(
    pattern_id: int,
    pattern_data: PayeePatternUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> PayeePattern:
    """
    Update an existing matching pattern.

    Can update:
    - pattern_type
    - pattern_value
    - confidence_score
    """
    service = PayeeService(db)

    # Validate pattern type if provided
    if pattern_data.pattern_type is not None:
        valid_types = ["description_contains", "exact_match", "fuzzy_match_base", "description_regex"]
        if pattern_data.pattern_type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid pattern type. Must be one of: {', '.join(valid_types)}"
            )

    pattern = service.update_pattern(
        pattern_id=pattern_id,
        user_id=current_user.id,
        pattern_type=pattern_data.pattern_type,
        pattern_value=pattern_data.pattern_value,
        confidence_score=float(pattern_data.confidence_score) if pattern_data.confidence_score else None
    )

    if not pattern:
        raise HTTPException(status_code=404, detail="Pattern not found")

    return pattern


@router.delete("/patterns/{pattern_id}")
def delete_payee_pattern(
    pattern_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> dict:
    """
    Delete a matching pattern.

    This will NOT affect existing transactions, only future matching.
    """
    service = PayeeService(db)
    success = service.delete_pattern(pattern_id, current_user.id)

    if not success:
        raise HTTPException(status_code=404, detail="Pattern not found")

    return {"message": "Pattern deleted successfully"}


@router.post("/patterns/test", response_model=PatternTestResult)
def test_pattern(
    pattern_type: str = Query(
        ...,
        description="Pattern type to test"
    ),
    pattern_value: str = Query(
        ...,
        description="Pattern value to test"
    ),
    test_data: PatternTestRequest = ...,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> PatternTestResult:
    """
    Test a pattern against a transaction description.

    Useful for previewing whether a pattern will match before creating it.

    Returns whether the pattern matches and details about the match.
    """
    service = PayeeService(db)

    # Validate pattern type
    valid_types = ["description_contains", "exact_match", "fuzzy_match_base", "description_regex"]
    if pattern_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid pattern type. Must be one of: {', '.join(valid_types)}"
        )

    result = service.test_pattern(
        pattern_type=pattern_type,
        pattern_value=pattern_value,
        description=test_data.description
    )

    return PatternTestResult(**result)


# ============================================================================
# Icon Suggestion Endpoints
# ============================================================================

@router.get("/icons/suggest", response_model=IconSuggestion)
def suggest_icon(
    name: str = Query(..., min_length=1, description="Payee name to suggest icon for"),
    current_user: User = Depends(deps.get_current_user),
) -> IconSuggestion:
    """
    Suggest an icon (brand logo or emoji) for a payee name.

    - First attempts to match against 500+ known brand names
    - Falls back to emoji suggestions based on keywords
    - Returns CDN URL for brand logos or emoji format for emojis

    The returned `icon_value` can be stored directly in the payee's `logo_url` field.
    Brand icons: Full CDN URL (e.g., "https://cdn.simpleicons.org/starbucks/006241")
    Emoji icons: "emoji:{char}" format (e.g., "emoji:☕")
    """
    result = payee_icon_service.suggest_icon(name)
    return IconSuggestion(**result)


@router.get("/icons/parse", response_model=IconParsed)
def parse_icon(
    logo_url: Optional[str] = Query(None, description="Logo URL to parse"),
    current_user: User = Depends(deps.get_current_user),
) -> IconParsed:
    """
    Parse a stored logo_url into its display components.

    - For brand logos: returns the CDN URL
    - For emojis: extracts the emoji character
    - For custom URLs: returns as-is
    - For empty/null: returns the default emoji

    Use this to determine how to render a payee's icon in the UI.
    """
    result = payee_icon_service.parse_logo_url(logo_url)
    return IconParsed(**result)


@router.get("/icons/brands", response_model=List[dict])
def list_brands(
    current_user: User = Depends(deps.get_current_user),
) -> List[dict]:
    """
    Get a list of all available brand icons.

    Returns brands with their Simple Icons slugs and CDN URLs.
    Useful for documentation or brand picker UI.
    """
    return payee_icon_service.get_all_brands()
