"""
Account Balance Service

Handles balance calculations for accounts based on transactions.
All balances are calculated on-the-fly from opening_balance + transactions,
ensuring single source of truth and data integrity.
"""
from typing import Dict, Optional
from datetime import date
from decimal import Decimal
from sqlalchemy.orm import Session

from app.models.account import Account


class AccountBalanceService:
    """Service for calculating account balances from transactions."""

    def __init__(self, db: Session):
        self.db = db

    def get_current_balance(self, account_id: int) -> Decimal:
        """
        Get the current balance for an account.

        Args:
            account_id: Account ID

        Returns:
            Current balance as Decimal

        Raises:
            ValueError: If account not found
        """
        account = self.db.query(Account).filter(Account.id == account_id).first()
        if not account:
            raise ValueError(f"Account {account_id} not found")

        return account.calculate_balance(self.db)

    def get_balance_as_of(self, account_id: int, as_of_date: date) -> Decimal:
        """
        Get the balance for an account as of a specific date.

        Args:
            account_id: Account ID
            as_of_date: Date to calculate balance as of

        Returns:
            Balance as of the specified date

        Raises:
            ValueError: If account not found
        """
        account = self.db.query(Account).filter(Account.id == account_id).first()
        if not account:
            raise ValueError(f"Account {account_id} not found")

        return account.calculate_balance(self.db, as_of_date=as_of_date)

    def get_all_account_balances(self, user_id: int) -> Dict[int, Decimal]:
        """
        Get current balances for all accounts belonging to a user.

        This is optimized for bulk operations like dashboard display.

        Args:
            user_id: User ID

        Returns:
            Dictionary mapping account_id -> current_balance
        """
        accounts = self.db.query(Account).filter(Account.user_id == user_id).all()

        balances = {}
        for account in accounts:
            balances[account.id] = account.calculate_balance(self.db)

        return balances

    def recalculate_opening_balance(
        self,
        account_id: int,
        actual_balance: Decimal,
        actual_balance_date: Optional[date] = None
    ) -> None:
        """
        Recalculate the opening balance based on a known actual balance.

        This is used for reconciliation when the user has a bank statement showing
        a specific balance on a specific date. We work backwards to calculate what
        the opening balance should be.

        Args:
            account_id: Account ID
            actual_balance: The actual balance from bank statement
            actual_balance_date: Date of the actual balance (default: today)

        Raises:
            ValueError: If account not found
        """
        account = self.db.query(Account).filter(Account.id == account_id).first()
        if not account:
            raise ValueError(f"Account {account_id} not found")

        if actual_balance_date is None:
            actual_balance_date = date.today()

        # Calculate what the balance would be based on current opening_balance
        calculated_balance = account.calculate_balance(self.db, as_of_date=actual_balance_date)

        # The difference is how much we need to adjust the opening balance
        adjustment = actual_balance - calculated_balance

        # Apply the adjustment
        account.opening_balance += adjustment

        # Update the opening_balance_date to the reconciliation date
        account.opening_balance_date = actual_balance_date

        self.db.commit()
