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

router = APIRouter()


@router.post("", response_model=Transaction, status_code=status.HTTP_201_CREATED)
def create_transaction(
    transaction_data: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """Create a new transaction for the authenticated user."""
    db_transaction = TransactionModel(
        **transaction_data.model_dump(),
        user_id=current_user.id
    )
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction


@router.get("", response_model=List[Transaction])
def get_transactions(
    account_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """Get all transactions for the authenticated user with optional filters."""
    query = db.query(TransactionModel).filter(TransactionModel.user_id == current_user.id)

    if account_id:
        query = query.filter(TransactionModel.account_id == account_id)

    if start_date:
        query = query.filter(TransactionModel.date >= start_date)

    if end_date:
        query = query.filter(TransactionModel.date <= end_date)

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

    # Update only provided fields
    update_data = transaction_data.model_dump(exclude_unset=True)
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


@router.get("/suggestions/payees", response_model=List[str])
def get_payee_suggestions(
    q: Optional[str] = Query(None, min_length=1),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """Get payee suggestions for autocomplete based on transaction history."""
    query = db.query(TransactionModel.payee).filter(
        TransactionModel.user_id == current_user.id,
        TransactionModel.payee.isnot(None),
        TransactionModel.payee != ""
    )

    # Filter by search query if provided
    if q:
        query = query.filter(TransactionModel.payee.ilike(f"%{q}%"))

    # Group by payee and order by frequency (most used first)
    payees = query.group_by(TransactionModel.payee)\
        .order_by(desc(func.count(TransactionModel.payee)))\
        .limit(limit)\
        .all()

    return [payee[0] for payee in payees]


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
