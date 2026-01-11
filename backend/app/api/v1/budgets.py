from typing import List
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User as UserModel
from app.models.budget import Budget as BudgetModel
from app.models.transaction import Transaction as TransactionModel, TransactionType
from app.schemas.budget import Budget, BudgetCreate, BudgetUpdate, BudgetWithProgress

router = APIRouter()


@router.post("", response_model=Budget, status_code=status.HTTP_201_CREATED)
def create_budget(
    budget_data: BudgetCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """Create a new budget for the authenticated user."""
    db_budget = BudgetModel(
        **budget_data.model_dump(),
        user_id=current_user.id
    )
    db.add(db_budget)
    db.commit()
    db.refresh(db_budget)
    return db_budget


@router.get("", response_model=List[Budget])
def get_budgets(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """Get all budgets for the authenticated user."""
    return db.query(BudgetModel).filter(BudgetModel.user_id == current_user.id).all()


@router.get("/{budget_id}", response_model=Budget)
def get_budget(
    budget_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """Get a specific budget by ID."""
    budget = db.query(BudgetModel).filter(
        BudgetModel.id == budget_id,
        BudgetModel.user_id == current_user.id
    ).first()

    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found"
        )

    return budget


@router.get("/{budget_id}/progress", response_model=BudgetWithProgress)
def get_budget_progress(
    budget_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """Get budget with spending progress information."""
    budget = db.query(BudgetModel).filter(
        BudgetModel.id == budget_id,
        BudgetModel.user_id == current_user.id
    ).first()

    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found"
        )

    # Calculate spent amount for this budget's category and time period
    query = db.query(func.sum(TransactionModel.amount)).filter(
        TransactionModel.user_id == current_user.id,
        TransactionModel.category_id == budget.category_id,
        TransactionModel.type == TransactionType.DEBIT,
        TransactionModel.date >= budget.start_date
    )

    # Add end_date filter if budget has an end_date
    if budget.end_date:
        query = query.filter(TransactionModel.date <= budget.end_date)

    spent = query.scalar() or Decimal("0.00")

    # Calculate remaining and percentage
    remaining = budget.amount - spent
    percentage = (spent / budget.amount * 100) if budget.amount > 0 else Decimal("0.00")
    is_over_budget = spent > budget.amount

    # Convert budget to dict and add progress fields
    budget_dict = {
        "id": budget.id,
        "user_id": budget.user_id,
        "category_id": budget.category_id,
        "name": budget.name,
        "amount": budget.amount,
        "period": budget.period,
        "start_date": budget.start_date,
        "end_date": budget.end_date,
        "rollover": budget.rollover,
        "alert_enabled": budget.alert_enabled,
        "alert_threshold": budget.alert_threshold,
        "notes": budget.notes,
        "created_at": budget.created_at,
        "updated_at": budget.updated_at,
        "spent": spent,
        "remaining": remaining,
        "percentage": percentage,
        "is_over_budget": is_over_budget
    }

    return budget_dict


@router.put("/{budget_id}", response_model=Budget)
def update_budget(
    budget_id: int,
    budget_data: BudgetUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """Update a budget."""
    budget = db.query(BudgetModel).filter(
        BudgetModel.id == budget_id,
        BudgetModel.user_id == current_user.id
    ).first()

    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found"
        )

    # Update only provided fields
    update_data = budget_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(budget, field, value)

    db.commit()
    db.refresh(budget)
    return budget


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget(
    budget_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """Delete a budget."""
    budget = db.query(BudgetModel).filter(
        BudgetModel.id == budget_id,
        BudgetModel.user_id == current_user.id
    ).first()

    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found"
        )

    db.delete(budget)
    db.commit()
    return None
