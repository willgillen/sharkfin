import pytest
from decimal import Decimal
from datetime import date
from app.models.account import AccountType


class TestTransactionRunningBalance:
    """Test running balance calculation in transaction API."""

    def test_running_balance_with_account_filter(self, client, auth_headers, test_user, db_session):
        """Test that running balance is calculated when filtering by account."""
        from app.models.account import Account
        from app.models.transaction import Transaction, TransactionType

        # Create account with opening balance
        account = Account(
            user_id=test_user.id,
            name="Test Checking",
            type=AccountType.CHECKING,
            currency="USD",
            opening_balance=Decimal("1000.00"),
            opening_balance_date=date(2026, 1, 1)
        )
        db_session.add(account)
        db_session.commit()
        db_session.refresh(account)

        # Create transactions
        tx1 = Transaction(
            user_id=test_user.id,
            account_id=account.id,
            type=TransactionType.CREDIT,
            amount=Decimal("500.00"),
            date=date(2026, 1, 5),
            description="Salary"
        )
        tx2 = Transaction(
            user_id=test_user.id,
            account_id=account.id,
            type=TransactionType.DEBIT,
            amount=Decimal("200.00"),
            date=date(2026, 1, 10),
            description="Groceries"
        )
        tx3 = Transaction(
            user_id=test_user.id,
            account_id=account.id,
            type=TransactionType.DEBIT,
            amount=Decimal("100.00"),
            date=date(2026, 1, 15),
            description="Gas"
        )
        db_session.add_all([tx1, tx2, tx3])
        db_session.commit()

        # Get transactions with running balance
        response = client.get(
            f"/api/v1/transactions?account_id={account.id}&sort_order=asc",
            headers=auth_headers
        )

        assert response.status_code == 200
        transactions = response.json()
        assert len(transactions) == 3

        # Verify running balances
        # Starting: 1000.00
        # After tx1 (credit 500): 1500.00
        # After tx2 (debit 200): 1300.00
        # After tx3 (debit 100): 1200.00
        assert Decimal(transactions[0]["running_balance"]) == Decimal("1500.00")
        assert Decimal(transactions[1]["running_balance"]) == Decimal("1300.00")
        assert Decimal(transactions[2]["running_balance"]) == Decimal("1200.00")

    def test_running_balance_not_present_without_account_filter(self, client, auth_headers, test_user, db_session):
        """Test that running balance is not calculated when not filtering by account."""
        from app.models.account import Account
        from app.models.transaction import Transaction, TransactionType

        # Create account
        account = Account(
            user_id=test_user.id,
            name="Test Checking",
            type=AccountType.CHECKING,
            currency="USD",
            opening_balance=Decimal("1000.00")
        )
        db_session.add(account)
        db_session.commit()
        db_session.refresh(account)

        # Create transaction
        tx = Transaction(
            user_id=test_user.id,
            account_id=account.id,
            type=TransactionType.CREDIT,
            amount=Decimal("500.00"),
            date=date(2026, 1, 5),
            description="Salary"
        )
        db_session.add(tx)
        db_session.commit()

        # Get transactions without account filter
        response = client.get(
            "/api/v1/transactions",
            headers=auth_headers
        )

        assert response.status_code == 200
        transactions = response.json()
        assert len(transactions) >= 1

        # Running balance should be null
        assert transactions[0]["running_balance"] is None

    def test_running_balance_with_transfers(self, client, auth_headers, test_user, db_session):
        """Test running balance calculation with transfer transactions."""
        from app.models.account import Account
        from app.models.transaction import Transaction, TransactionType

        # Create two accounts
        account1 = Account(
            user_id=test_user.id,
            name="Checking",
            type=AccountType.CHECKING,
            currency="USD",
            opening_balance=Decimal("1000.00"),
            opening_balance_date=date(2026, 1, 1)
        )
        account2 = Account(
            user_id=test_user.id,
            name="Savings",
            type=AccountType.SAVINGS,
            currency="USD",
            opening_balance=Decimal("5000.00"),
            opening_balance_date=date(2026, 1, 1)
        )
        db_session.add_all([account1, account2])
        db_session.commit()
        db_session.refresh(account1)
        db_session.refresh(account2)

        # Create transfer from account1 to account2
        transfer = Transaction(
            user_id=test_user.id,
            account_id=account1.id,  # Source
            transfer_account_id=account2.id,  # Destination
            type=TransactionType.TRANSFER,
            amount=Decimal("300.00"),
            date=date(2026, 1, 10),
            description="Transfer to savings"
        )
        db_session.add(transfer)
        db_session.commit()

        # Get transactions for account1 (source)
        response1 = client.get(
            f"/api/v1/transactions?account_id={account1.id}",
            headers=auth_headers
        )

        assert response1.status_code == 200
        transactions1 = response1.json()
        assert len(transactions1) == 1
        # 1000.00 - 300.00 = 700.00
        assert Decimal(transactions1[0]["running_balance"]) == Decimal("700.00")

        # Get transactions for account2 (destination)
        response2 = client.get(
            f"/api/v1/transactions?account_id={account2.id}",
            headers=auth_headers
        )

        assert response2.status_code == 200
        transactions2 = response2.json()
        assert len(transactions2) == 1
        # 5000.00 + 300.00 = 5300.00
        assert Decimal(transactions2[0]["running_balance"]) == Decimal("5300.00")

    def test_running_balance_respects_opening_balance_date(self, client, auth_headers, test_user, db_session):
        """Test that running balance only includes transactions after opening_balance_date."""
        from app.models.account import Account
        from app.models.transaction import Transaction, TransactionType

        # Create account with opening balance date
        account = Account(
            user_id=test_user.id,
            name="Test Checking",
            type=AccountType.CHECKING,
            currency="USD",
            opening_balance=Decimal("1000.00"),
            opening_balance_date=date(2026, 1, 15)  # Mid-month
        )
        db_session.add(account)
        db_session.commit()
        db_session.refresh(account)

        # Create transactions before and after opening_balance_date
        tx_before = Transaction(
            user_id=test_user.id,
            account_id=account.id,
            type=TransactionType.CREDIT,
            amount=Decimal("500.00"),
            date=date(2026, 1, 10),  # Before opening_balance_date
            description="Should be ignored"
        )
        tx_after = Transaction(
            user_id=test_user.id,
            account_id=account.id,
            type=TransactionType.DEBIT,
            amount=Decimal("200.00"),
            date=date(2026, 1, 20),  # After opening_balance_date
            description="Should be counted"
        )
        db_session.add_all([tx_before, tx_after])
        db_session.commit()

        # Get transactions
        response = client.get(
            f"/api/v1/transactions?account_id={account.id}&sort_order=asc",
            headers=auth_headers
        )

        assert response.status_code == 200
        transactions = response.json()
        # Should only return tx_after (tx_before is before opening_balance_date)
        assert len(transactions) == 1
        # 1000.00 - 200.00 = 800.00
        assert Decimal(transactions[0]["running_balance"]) == Decimal("800.00")

    def test_running_balance_with_date_filters(self, client, auth_headers, test_user, db_session):
        """Test running balance calculation with date range filters."""
        from app.models.account import Account
        from app.models.transaction import Transaction, TransactionType

        # Create account
        account = Account(
            user_id=test_user.id,
            name="Test Checking",
            type=AccountType.CHECKING,
            currency="USD",
            opening_balance=Decimal("1000.00"),
            opening_balance_date=date(2026, 1, 1)
        )
        db_session.add(account)
        db_session.commit()
        db_session.refresh(account)

        # Create multiple transactions
        transactions = [
            Transaction(user_id=test_user.id, account_id=account.id, type=TransactionType.CREDIT,
                       amount=Decimal("100.00"), date=date(2026, 1, 5), description="Jan 5"),
            Transaction(user_id=test_user.id, account_id=account.id, type=TransactionType.DEBIT,
                       amount=Decimal("50.00"), date=date(2026, 1, 10), description="Jan 10"),
            Transaction(user_id=test_user.id, account_id=account.id, type=TransactionType.CREDIT,
                       amount=Decimal("200.00"), date=date(2026, 1, 15), description="Jan 15"),
            Transaction(user_id=test_user.id, account_id=account.id, type=TransactionType.DEBIT,
                       amount=Decimal("75.00"), date=date(2026, 1, 20), description="Jan 20"),
        ]
        db_session.add_all(transactions)
        db_session.commit()

        # Filter to mid-month (Jan 10-15)
        response = client.get(
            f"/api/v1/transactions?account_id={account.id}&start_date=2026-01-10&end_date=2026-01-15&sort_order=asc",
            headers=auth_headers
        )

        assert response.status_code == 200
        filtered_txs = response.json()
        assert len(filtered_txs) == 2

        # Running balance calculates from opening balance using only filtered transactions
        # Opening: 1000.00
        # After Jan 10 (-50): 950.00
        # After Jan 15 (+200): 1150.00
        # (Jan 5 transaction is excluded by date filter)
        assert Decimal(filtered_txs[0]["running_balance"]) == Decimal("950.00")
        assert Decimal(filtered_txs[1]["running_balance"]) == Decimal("1150.00")

    def test_running_balance_with_pagination(self, client, auth_headers, test_user, db_session):
        """Test that running balance works correctly with pagination."""
        from app.models.account import Account
        from app.models.transaction import Transaction, TransactionType

        # Create account
        account = Account(
            user_id=test_user.id,
            name="Test Checking",
            type=AccountType.CHECKING,
            currency="USD",
            opening_balance=Decimal("1000.00"),
            opening_balance_date=date(2026, 1, 1)
        )
        db_session.add(account)
        db_session.commit()
        db_session.refresh(account)

        # Create 10 transactions
        for i in range(10):
            tx = Transaction(
                user_id=test_user.id,
                account_id=account.id,
                type=TransactionType.CREDIT,
                amount=Decimal("100.00"),
                date=date(2026, 1, i + 1),
                description=f"Transaction {i + 1}"
            )
            db_session.add(tx)
        db_session.commit()

        # Get first page (5 transactions)
        response1 = client.get(
            f"/api/v1/transactions?account_id={account.id}&sort_order=asc&limit=5",
            headers=auth_headers
        )

        assert response1.status_code == 200
        page1 = response1.json()
        assert len(page1) == 5
        # First transaction: 1000 + 100 = 1100
        # Fifth transaction: 1000 + 500 = 1500
        assert Decimal(page1[0]["running_balance"]) == Decimal("1100.00")
        assert Decimal(page1[4]["running_balance"]) == Decimal("1500.00")

        # Get second page (skip 5, take 5)
        response2 = client.get(
            f"/api/v1/transactions?account_id={account.id}&sort_order=asc&skip=5&limit=5",
            headers=auth_headers
        )

        assert response2.status_code == 200
        page2 = response2.json()
        assert len(page2) == 5
        # Sixth transaction: 1000 + 600 = 1600
        # Tenth transaction: 1000 + 1000 = 2000
        assert Decimal(page2[0]["running_balance"]) == Decimal("1600.00")
        assert Decimal(page2[4]["running_balance"]) == Decimal("2000.00")
