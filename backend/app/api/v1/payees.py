from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.schemas.payee import (
    Payee, PayeeCreate, PayeeUpdate, PayeeWithCategory,
    PayeeTransaction, PayeeStats
)
from app.services.payee_service import PayeeService

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
