from typing import List, Optional, Dict
from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc, case, literal_column, over
from sqlalchemy.sql import select

from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User as UserModel
from app.models.transaction import Transaction as TransactionModel, TransactionType
from app.models.account import Account as AccountModel
from app.schemas.transaction import Transaction, TransactionCreate, TransactionUpdate
from app.services.payee_service import PayeeService


def _transaction_to_response(transaction: TransactionModel, running_balance: Optional[Decimal] = None) -> dict:
    """Convert transaction model to response dict with payee info from linked entity."""
    result = {
        "id": transaction.id,
        "user_id": transaction.user_id,
        "account_id": transaction.account_id,
        "category_id": transaction.category_id,
        "type": transaction.type,
        "amount": transaction.amount,
        "date": transaction.date,
        "payee_id": transaction.payee_id,
        "payee": transaction.payee,  # Legacy field
        "description": transaction.description,
        "notes": transaction.notes,
        "transfer_account_id": transaction.transfer_account_id,
        "is_starred": transaction.is_starred,
        "created_at": transaction.created_at,
        "updated_at": transaction.updated_at,
        # Get payee info from linked Payee entity
        "payee_name": transaction.payee_entity.canonical_name if transaction.payee_entity else None,
        "payee_logo_url": transaction.payee_entity.logo_url if transaction.payee_entity else None,
        # Running balance (only present when filtering by account)
        "running_balance": running_balance,
    }
    return result

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

    # Reload with payee relationship for response
    db_transaction = db.query(TransactionModel).options(
        joinedload(TransactionModel.payee_entity)
    ).filter(TransactionModel.id == db_transaction.id).first()

    return _transaction_to_response(db_transaction)


@router.get("", response_model=List[Transaction])
def get_transactions(
    account_id: Optional[int] = Query(None, description="Filter by account ID"),
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    type: Optional[str] = Query(None, description="Filter by transaction type (debit, credit, transfer)"),
    is_starred: Optional[bool] = Query(None, description="Filter by starred status"),
    payee_search: Optional[str] = Query(None, description="Search by payee name or description"),
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
    When filtering by account_id, includes running_balance for each transaction.
    """

    # If filtering by account, calculate running balance using window function
    if account_id:
        # Get account's opening balance
        account = db.query(AccountModel).filter(
            AccountModel.id == account_id,
            AccountModel.user_id == current_user.id
        ).first()

        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found"
            )

        # Build transaction amount delta based on type
        # For the account being viewed:
        # - CREDIT adds to balance
        # - DEBIT subtracts from balance
        # - TRANSFER: if this is the source account, subtract; if destination, add
        amount_delta = case(
            (TransactionModel.type == TransactionType.CREDIT, TransactionModel.amount),
            (TransactionModel.type == TransactionType.DEBIT, -TransactionModel.amount),
            # For transfers, check if this account is source or destination
            ((TransactionModel.type == TransactionType.TRANSFER) & (TransactionModel.account_id == account_id), -TransactionModel.amount),
            ((TransactionModel.type == TransactionType.TRANSFER) & (TransactionModel.transfer_account_id == account_id), TransactionModel.amount),
            else_=literal_column("0")
        )

        # Create window function to calculate cumulative sum
        # Order by date, then id for consistent ordering
        running_sum_window = over(
            func.sum(amount_delta),
            order_by=[TransactionModel.date.asc(), TransactionModel.id.asc()]
        )

        # Build subquery with running balance
        # Filter transactions that affect this account (either as primary account or transfer destination)
        base_query = db.query(
            TransactionModel,
            (account.opening_balance + func.coalesce(running_sum_window, 0)).label('running_balance')
        ).filter(
            TransactionModel.user_id == current_user.id
        ).filter(
            (TransactionModel.account_id == account_id) |
            (TransactionModel.transfer_account_id == account_id)
        )

        # Apply date filters for running balance calculation
        if account.opening_balance_date:
            base_query = base_query.filter(TransactionModel.date >= account.opening_balance_date)

        if start_date:
            base_query = base_query.filter(TransactionModel.date >= start_date)

        if end_date:
            base_query = base_query.filter(TransactionModel.date <= end_date)

        # Apply other filters
        if category_id:
            base_query = base_query.filter(TransactionModel.category_id == category_id)

        if type:
            base_query = base_query.filter(TransactionModel.type == type)

        if is_starred is not None:
            base_query = base_query.filter(TransactionModel.is_starred == is_starred)

        if payee_search:
            search_pattern = f"%{payee_search}%"
            base_query = base_query.filter(
                (TransactionModel.payee.ilike(search_pattern)) |
                (TransactionModel.description.ilike(search_pattern))
            )

        # Create subquery
        subquery = base_query.subquery()

        # Now query from subquery with sorting and pagination
        # Join back to get payee_entity relationship
        results = db.query(
            TransactionModel,
            subquery.c.running_balance
        ).join(
            subquery,
            TransactionModel.id == subquery.c.id
        ).options(
            joinedload(TransactionModel.payee_entity)
        )

        # Apply sorting
        sort_column = subquery.c.date  # Default
        if sort_by == "amount":
            sort_column = subquery.c.amount
        elif sort_by == "payee":
            sort_column = subquery.c.payee
        elif sort_by == "date":
            sort_column = subquery.c.date

        if sort_order.lower() == "asc":
            results = results.order_by(sort_column.asc())
        else:
            results = results.order_by(sort_column.desc())

        # Apply pagination
        results = results.offset(skip).limit(limit).all()

        # Convert to response format with running balance
        return [_transaction_to_response(t[0], t[1]) for t in results]

    else:
        # Original logic when not filtering by account (no running balance)
        # Eager load payee_entity to get payee_name without N+1 queries
        query = db.query(TransactionModel).options(
            joinedload(TransactionModel.payee_entity)
        ).filter(TransactionModel.user_id == current_user.id)

        # Apply filters
        if category_id:
            query = query.filter(TransactionModel.category_id == category_id)

        if type:
            query = query.filter(TransactionModel.type == type)

        if is_starred is not None:
            query = query.filter(TransactionModel.is_starred == is_starred)

        if payee_search:
            # Search in both payee field and description
            search_pattern = f"%{payee_search}%"
            query = query.filter(
                (TransactionModel.payee.ilike(search_pattern)) |
                (TransactionModel.description.ilike(search_pattern))
            )

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

        transactions = query.all()
        # Convert to response format with payee_name from linked entity
        return [_transaction_to_response(t) for t in transactions]


@router.get("/{transaction_id}", response_model=Transaction)
def get_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """Get a specific transaction by ID."""
    transaction = db.query(TransactionModel).options(
        joinedload(TransactionModel.payee_entity)
    ).filter(
        TransactionModel.id == transaction_id,
        TransactionModel.user_id == current_user.id
    ).first()

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )

    return _transaction_to_response(transaction)


@router.put("/{transaction_id}", response_model=Transaction)
def update_transaction(
    transaction_id: int,
    transaction_data: TransactionUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """Update a transaction."""
    transaction = db.query(TransactionModel).options(
        joinedload(TransactionModel.payee_entity)
    ).filter(
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
    return _transaction_to_response(transaction)


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


@router.patch("/{transaction_id}/star", response_model=Transaction)
def toggle_star(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """Toggle the starred status of a transaction."""
    transaction = db.query(TransactionModel).options(
        joinedload(TransactionModel.payee_entity)
    ).filter(
        TransactionModel.id == transaction_id,
        TransactionModel.user_id == current_user.id
    ).first()

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )

    # Toggle the starred status
    transaction.is_starred = not transaction.is_starred
    db.commit()
    db.refresh(transaction)

    return _transaction_to_response(transaction)
