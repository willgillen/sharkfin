from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User as UserModel
from app.models.account import Account as AccountModel
from app.schemas.account import Account, AccountCreate, AccountUpdate

router = APIRouter()


def _account_to_response(account: AccountModel, db: Session) -> dict:
    """Convert account model to response dict with calculated balance."""
    return {
        "id": account.id,
        "user_id": account.user_id,
        "name": account.name,
        "type": account.type,
        "institution": account.institution,
        "account_number": account.account_number,
        "currency": account.currency,
        "opening_balance": account.opening_balance,
        "opening_balance_date": account.opening_balance_date,
        "current_balance": account.calculate_balance(db),  # Calculated field
        "is_active": account.is_active,
        "notes": account.notes,
        "created_at": account.created_at,
        "updated_at": account.updated_at,
    }


@router.post("", response_model=Account, status_code=status.HTTP_201_CREATED)
def create_account(
    account_data: AccountCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Create a new account for the current user.

    Args:
        account_data: Account creation data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Created account object with calculated balance
    """
    db_account = AccountModel(
        **account_data.model_dump(),
        user_id=current_user.id
    )

    db.add(db_account)
    db.commit()
    db.refresh(db_account)

    return _account_to_response(db_account, db)


@router.get("", response_model=List[Account])
def get_accounts(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = 100
):
    """
    Get all accounts for the current user.

    Args:
        db: Database session
        current_user: Current authenticated user
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        List of user's accounts with calculated balances
    """
    accounts = db.query(AccountModel).filter(
        AccountModel.user_id == current_user.id
    ).offset(skip).limit(limit).all()

    return [_account_to_response(account, db) for account in accounts]


@router.get("/{account_id}", response_model=Account)
def get_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Get a specific account by ID.

    Args:
        account_id: Account ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Account object with calculated balance

    Raises:
        HTTPException: If account not found or doesn't belong to user
    """
    account = db.query(AccountModel).filter(
        AccountModel.id == account_id,
        AccountModel.user_id == current_user.id
    ).first()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )

    return _account_to_response(account, db)


@router.put("/{account_id}", response_model=Account)
def update_account(
    account_id: int,
    account_data: AccountUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Update an account.

    Args:
        account_id: Account ID
        account_data: Account update data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Updated account object with calculated balance

    Raises:
        HTTPException: If account not found or doesn't belong to user
    """
    account = db.query(AccountModel).filter(
        AccountModel.id == account_id,
        AccountModel.user_id == current_user.id
    ).first()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )

    # Update only provided fields
    update_data = account_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(account, field, value)

    db.commit()
    db.refresh(account)

    return _account_to_response(account, db)


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Delete an account.

    Args:
        account_id: Account ID
        db: Database session
        current_user: Current authenticated user

    Raises:
        HTTPException: If account not found or doesn't belong to user
    """
    account = db.query(AccountModel).filter(
        AccountModel.id == account_id,
        AccountModel.user_id == current_user.id
    ).first()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )

    db.delete(account)
    db.commit()

    return None
