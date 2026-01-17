from typing import List, Optional, Dict
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User as UserModel
from app.models.transaction import Transaction as TransactionModel
from app.schemas.transaction import Transaction, TransactionCreate, TransactionUpdate
from app.services.payee_service import PayeeService

router = APIRouter()


@router.post("", response_model=Transaction, status_code=status.HTTP_201_CREATED)
def create_transaction(
    transaction_data: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """Create a new transaction for the authenticated user."""
    # Handle payee entity creation
    payee_id = transaction_data.payee_id

    # If payee string provided but no payee_id, create/find payee entity
    if transaction_data.payee and not payee_id:
        payee_service = PayeeService(db)
        payee = payee_service.get_or_create(
            user_id=current_user.id,
            canonical_name=transaction_data.payee
        )
        payee_id = payee.id
        # Increment usage statistics
        payee_service.increment_usage(payee.id)

    # Create transaction with payee_id
    transaction_dict = transaction_data.model_dump(exclude={'payee_id', 'payee'})
    transaction_dict['payee_id'] = payee_id
    transaction_dict['payee'] = transaction_data.payee  # Keep legacy field for now

    db_transaction = TransactionModel(
        **transaction_dict,
        user_id=current_user.id
    )
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)

    # Increment payee usage after transaction creation
    if payee_id and not transaction_data.payee:
        # Only increment if using existing payee_id (not already incremented above)
        payee_service = PayeeService(db)
        payee_service.increment_usage(payee_id)

    return db_transaction


@router.get("", response_model=List[Transaction])
def get_transactions(
    account_id: Optional[int] = Query(None, description="Filter by account ID"),
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    start_date: Optional[date] = Query(None, description="Filter transactions on or after this date"),
    end_date: Optional[date] = Query(None, description="Filter transactions on or before this date"),
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    sort_by: str = Query("date", description="Field to sort by (date, amount, payee)"),
    sort_order: str = Query("desc", description="Sort order (asc or desc)"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """Get transactions for the authenticated user with filtering, sorting, and pagination.

    Default behavior: Returns up to 100 most recent transactions sorted by date (newest first).
    """
    query = db.query(TransactionModel).filter(TransactionModel.user_id == current_user.id)

    # Apply filters
    if account_id:
        query = query.filter(TransactionModel.account_id == account_id)

    if category_id:
        query = query.filter(TransactionModel.category_id == category_id)

    if start_date:
        query = query.filter(TransactionModel.date >= start_date)

    if end_date:
        query = query.filter(TransactionModel.date <= end_date)

    # Apply sorting
    sort_column = TransactionModel.date  # Default
    if sort_by == "amount":
        sort_column = TransactionModel.amount
    elif sort_by == "payee":
        sort_column = TransactionModel.payee
    elif sort_by == "date":
        sort_column = TransactionModel.date

    if sort_order.lower() == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    # Apply pagination
    query = query.offset(skip).limit(limit)

    return query.all()


@router.get("/{transaction_id}", response_model=Transaction)
def get_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """Get a specific transaction by ID."""
    transaction = db.query(TransactionModel).filter(
        TransactionModel.id == transaction_id,
        TransactionModel.user_id == current_user.id
    ).first()

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )

    return transaction


@router.put("/{transaction_id}", response_model=Transaction)
def update_transaction(
    transaction_id: int,
    transaction_data: TransactionUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """Update a transaction."""
    transaction = db.query(TransactionModel).filter(
        TransactionModel.id == transaction_id,
        TransactionModel.user_id == current_user.id
    ).first()

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )

    # Handle payee entity creation/update
    update_data = transaction_data.model_dump(exclude_unset=True)

    # If payee string provided, create/find payee entity
    if 'payee' in update_data and update_data['payee'] and 'payee_id' not in update_data:
        payee_service = PayeeService(db)
        payee = payee_service.get_or_create(
            user_id=current_user.id,
            canonical_name=update_data['payee']
        )
        update_data['payee_id'] = payee.id
        payee_service.increment_usage(payee.id)

    # Update fields
    for field, value in update_data.items():
        setattr(transaction, field, value)

    db.commit()
    db.refresh(transaction)
    return transaction


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """Delete a transaction."""
    transaction = db.query(TransactionModel).filter(
        TransactionModel.id == transaction_id,
        TransactionModel.user_id == current_user.id
    ).first()

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )

    db.delete(transaction)
    db.commit()
    return None


@router.get("/suggestions/payees")
def get_payee_suggestions(
    q: Optional[str] = Query(None, min_length=1),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Get payee suggestions for autocomplete.
    Now uses Payee entity autocomplete with category suggestions.
    """
    from app.schemas.payee import PayeeWithCategory

    payee_service = PayeeService(db)

    if q:
        # Use Payee entity search
        payees = payee_service.search_payees(user_id=current_user.id, query=q, limit=limit)
    else:
        # Get most frequently used payees
        payees = payee_service.get_all(user_id=current_user.id, skip=0, limit=limit)

    # Enrich with category information
    results = []
    for payee in payees:
        payee_dict = {
            "id": payee.id,
            "canonical_name": payee.canonical_name,
            "default_category_id": payee.default_category_id,
            "transaction_count": payee.transaction_count,
            "default_category_name": None
        }

        if payee.default_category:
            payee_dict["default_category_name"] = payee.default_category.name

        results.append(payee_dict)

    return results


@router.get("/suggestions/category", response_model=Dict[str, Optional[int]])
def get_category_suggestion(
    payee: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """Get suggested category for a payee based on transaction history."""
    # Find the most frequently used category for this payee
    result = db.query(
        TransactionModel.category_id,
        func.count(TransactionModel.category_id).label('count')
    ).filter(
        TransactionModel.user_id == current_user.id,
        TransactionModel.payee.ilike(f"%{payee}%"),
        TransactionModel.category_id.isnot(None)
    ).group_by(TransactionModel.category_id)\
     .order_by(desc('count'))\
     .first()

    if result:
        return {"category_id": result[0]}

    return {"category_id": None}
