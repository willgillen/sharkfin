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

        # Running balance is calculated over ALL transactions, then filtered for display
        # This ensures the balance shown reflects the true account state at each transaction
        # Opening: 1000.00
        # After Jan 5 (+100): 1100.00 (not displayed but included in running balance)
        # After Jan 10 (-50): 1050.00 (displayed)
        # After Jan 15 (+200): 1250.00 (displayed)
        # After Jan 20 (-75): 1175.00 (not displayed)
        assert Decimal(filtered_txs[0]["running_balance"]) == Decimal("1050.00")
        assert Decimal(filtered_txs[1]["running_balance"]) == Decimal("1250.00")

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

    def test_running_balance_not_calculated_when_sorting_by_amount(self, client, auth_headers, test_user, db_session):
        """Test that running balance is null when sorting by amount instead of date."""
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
            description="Large deposit"
        )
        tx2 = Transaction(
            user_id=test_user.id,
            account_id=account.id,
            type=TransactionType.DEBIT,
            amount=Decimal("50.00"),
            date=date(2026, 1, 10),
            description="Small expense"
        )
        db_session.add_all([tx1, tx2])
        db_session.commit()

        # Get transactions sorted by amount (not date)
        response = client.get(
            f"/api/v1/transactions?account_id={account.id}&sort_by=amount&sort_order=desc",
            headers=auth_headers
        )

        assert response.status_code == 200
        transactions = response.json()
        assert len(transactions) == 2

        # Running balance should be null when not sorting by date
        # because running balance only makes sense in chronological order
        assert transactions[0]["running_balance"] is None
        assert transactions[1]["running_balance"] is None

    def test_running_balance_not_calculated_when_sorting_by_payee(self, client, auth_headers, test_user, db_session):
        """Test that running balance is null when sorting by payee instead of date."""
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

        # Create transactions with different payees
        tx1 = Transaction(
            user_id=test_user.id,
            account_id=account.id,
            type=TransactionType.DEBIT,
            amount=Decimal("100.00"),
            date=date(2026, 1, 5),
            payee="Alpha Store",
            description="Purchase"
        )
        tx2 = Transaction(
            user_id=test_user.id,
            account_id=account.id,
            type=TransactionType.DEBIT,
            amount=Decimal("200.00"),
            date=date(2026, 1, 10),
            payee="Zeta Market",
            description="Groceries"
        )
        db_session.add_all([tx1, tx2])
        db_session.commit()

        # Get transactions sorted by payee (not date)
        response = client.get(
            f"/api/v1/transactions?account_id={account.id}&sort_by=payee&sort_order=asc",
            headers=auth_headers
        )

        assert response.status_code == 200
        transactions = response.json()
        assert len(transactions) == 2

        # Running balance should be null when not sorting by date
        assert transactions[0]["running_balance"] is None
        assert transactions[1]["running_balance"] is None

    def test_running_balance_with_display_order(self, client, auth_headers, test_user, db_session):
        """Test that display_order affects running balance calculation order."""
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

        # Create two transactions on the same day with explicit display_order
        # tx1 has higher display_order, so should be processed AFTER tx2
        tx1 = Transaction(
            user_id=test_user.id,
            account_id=account.id,
            type=TransactionType.CREDIT,
            amount=Decimal("500.00"),
            date=date(2026, 1, 5),
            description="Deposit (should be second)",
            display_order=2
        )
        tx2 = Transaction(
            user_id=test_user.id,
            account_id=account.id,
            type=TransactionType.DEBIT,
            amount=Decimal("200.00"),
            date=date(2026, 1, 5),
            description="Withdrawal (should be first)",
            display_order=1
        )
        db_session.add_all([tx1, tx2])
        db_session.commit()

        # Get transactions
        response = client.get(
            f"/api/v1/transactions?account_id={account.id}&sort_order=asc",
            headers=auth_headers
        )

        assert response.status_code == 200
        transactions = response.json()
        assert len(transactions) == 2

        # With display_order:
        # First (display_order=1): 1000.00 - 200.00 = 800.00 (withdrawal)
        # Second (display_order=2): 800.00 + 500.00 = 1300.00 (deposit)
        # Find the transactions by description to verify order
        withdrawal = next(t for t in transactions if "Withdrawal" in t["description"])
        deposit = next(t for t in transactions if "Deposit" in t["description"])

        assert Decimal(withdrawal["running_balance"]) == Decimal("800.00")
        assert Decimal(deposit["running_balance"]) == Decimal("1300.00")

    def test_running_balance_same_day_ordering_desc(self, client, auth_headers, test_user, db_session):
        """Test that same-day transactions are ordered correctly when sorting DESC.

        When sorting by date DESC (newest first), transactions on the same day
        should also be ordered DESC by display_order/id, so the running balance
        shown matches the chronological order (later transaction on top with higher balance).
        """
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

        # Create three transactions on the same day with explicit display_order
        # Simulating: Lowes withdrawal, then AmEx payment, then Schwab deposit
        tx1 = Transaction(
            user_id=test_user.id,
            account_id=account.id,
            type=TransactionType.DEBIT,
            amount=Decimal("500.00"),
            date=date(2026, 1, 5),
            description="Lowes (first chronologically)",
            display_order=1
        )
        tx2 = Transaction(
            user_id=test_user.id,
            account_id=account.id,
            type=TransactionType.DEBIT,
            amount=Decimal("200.00"),
            date=date(2026, 1, 5),
            description="AmEx (second chronologically)",
            display_order=2
        )
        tx3 = Transaction(
            user_id=test_user.id,
            account_id=account.id,
            type=TransactionType.CREDIT,
            amount=Decimal("1000.00"),
            date=date(2026, 1, 5),
            description="Schwab (third chronologically)",
            display_order=3
        )
        db_session.add_all([tx1, tx2, tx3])
        db_session.commit()

        # Get transactions sorted DESC (default - newest/latest first)
        response = client.get(
            f"/api/v1/transactions?account_id={account.id}&sort_order=desc",
            headers=auth_headers
        )

        assert response.status_code == 200
        transactions = response.json()
        assert len(transactions) == 3

        # Running balance calculation (chronological order):
        # 1. Lowes (display_order=1): 1000.00 - 500.00 = 500.00
        # 2. AmEx (display_order=2): 500.00 - 200.00 = 300.00
        # 3. Schwab (display_order=3): 300.00 + 1000.00 = 1300.00

        # When sorted DESC, the order should be: Schwab, AmEx, Lowes (reverse chronological)
        # So first in the list should be Schwab with highest balance
        assert transactions[0]["description"] == "Schwab (third chronologically)"
        assert Decimal(transactions[0]["running_balance"]) == Decimal("1300.00")

        assert transactions[1]["description"] == "AmEx (second chronologically)"
        assert Decimal(transactions[1]["running_balance"]) == Decimal("300.00")

        assert transactions[2]["description"] == "Lowes (first chronologically)"
        assert Decimal(transactions[2]["running_balance"]) == Decimal("500.00")

    def test_running_balance_with_payee_filter(self, client, auth_headers, test_user, db_session):
        """Test that running balance reflects true account state even when filtering by payee.

        When filtering by payee, the running balance should still show the correct
        balance at each transaction (including effects of all other transactions),
        not just the cumulative sum of filtered transactions.
        """
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

        # Create transactions with different payees
        # Chronological order:
        # Jan 2: Uber -$20 -> balance 980
        # Jan 3: Grocery Store -$100 -> balance 880
        # Jan 4: Uber -$15 -> balance 865
        # Jan 5: Paycheck +$2000 -> balance 2865
        # Jan 6: Uber -$25 -> balance 2840
        tx1 = Transaction(
            user_id=test_user.id,
            account_id=account.id,
            type=TransactionType.DEBIT,
            amount=Decimal("20.00"),
            date=date(2026, 1, 2),
            payee="Uber",
            description="Uber ride"
        )
        tx2 = Transaction(
            user_id=test_user.id,
            account_id=account.id,
            type=TransactionType.DEBIT,
            amount=Decimal("100.00"),
            date=date(2026, 1, 3),
            payee="Grocery Store",
            description="Weekly groceries"
        )
        tx3 = Transaction(
            user_id=test_user.id,
            account_id=account.id,
            type=TransactionType.DEBIT,
            amount=Decimal("15.00"),
            date=date(2026, 1, 4),
            payee="Uber",
            description="Uber ride"
        )
        tx4 = Transaction(
            user_id=test_user.id,
            account_id=account.id,
            type=TransactionType.CREDIT,
            amount=Decimal("2000.00"),
            date=date(2026, 1, 5),
            payee="Employer Inc",
            description="Paycheck"
        )
        tx5 = Transaction(
            user_id=test_user.id,
            account_id=account.id,
            type=TransactionType.DEBIT,
            amount=Decimal("25.00"),
            date=date(2026, 1, 6),
            payee="Uber",
            description="Uber ride"
        )
        db_session.add_all([tx1, tx2, tx3, tx4, tx5])
        db_session.commit()

        # Filter by Uber payee
        response = client.get(
            f"/api/v1/transactions?account_id={account.id}&payee_search=Uber&sort_order=asc",
            headers=auth_headers
        )

        assert response.status_code == 200
        transactions = response.json()
        assert len(transactions) == 3  # Only Uber transactions

        # Running balances should reflect the TRUE account balance at each Uber transaction
        # NOT just the cumulative sum of Uber transactions
        # Jan 2 Uber: 1000 - 20 = 980
        assert Decimal(transactions[0]["running_balance"]) == Decimal("980.00")
        # Jan 4 Uber: 980 - 100 (grocery) - 15 = 865
        assert Decimal(transactions[1]["running_balance"]) == Decimal("865.00")
        # Jan 6 Uber: 865 + 2000 (paycheck) - 25 = 2840
        assert Decimal(transactions[2]["running_balance"]) == Decimal("2840.00")

    def test_running_balance_with_category_filter(self, client, auth_headers, test_user, db_session):
        """Test that running balance reflects true account state even when filtering by category."""
        from app.models.account import Account
        from app.models.category import Category, CategoryType
        from app.models.transaction import Transaction, TransactionType

        # Create account
        account = Account(
            user_id=test_user.id,
            name="Test Checking",
            type=AccountType.CHECKING,
            currency="USD",
            opening_balance=Decimal("500.00"),
            opening_balance_date=date(2026, 1, 1)
        )
        db_session.add(account)
        db_session.commit()
        db_session.refresh(account)

        # Create categories
        food_category = Category(user_id=test_user.id, name="Food", type=CategoryType.EXPENSE)
        transport_category = Category(user_id=test_user.id, name="Transport", type=CategoryType.EXPENSE)
        db_session.add_all([food_category, transport_category])
        db_session.commit()
        db_session.refresh(food_category)
        db_session.refresh(transport_category)

        # Create transactions
        # Jan 2: Food -$30 -> balance 470
        # Jan 3: Transport -$20 -> balance 450
        # Jan 4: Food -$50 -> balance 400
        tx1 = Transaction(
            user_id=test_user.id,
            account_id=account.id,
            type=TransactionType.DEBIT,
            amount=Decimal("30.00"),
            date=date(2026, 1, 2),
            category_id=food_category.id,
            description="Lunch"
        )
        tx2 = Transaction(
            user_id=test_user.id,
            account_id=account.id,
            type=TransactionType.DEBIT,
            amount=Decimal("20.00"),
            date=date(2026, 1, 3),
            category_id=transport_category.id,
            description="Bus fare"
        )
        tx3 = Transaction(
            user_id=test_user.id,
            account_id=account.id,
            type=TransactionType.DEBIT,
            amount=Decimal("50.00"),
            date=date(2026, 1, 4),
            category_id=food_category.id,
            description="Dinner"
        )
        db_session.add_all([tx1, tx2, tx3])
        db_session.commit()

        # Filter by Food category
        response = client.get(
            f"/api/v1/transactions?account_id={account.id}&category_id={food_category.id}&sort_order=asc",
            headers=auth_headers
        )

        assert response.status_code == 200
        transactions = response.json()
        assert len(transactions) == 2  # Only Food transactions

        # Running balances should reflect the TRUE account balance
        # Jan 2 Food: 500 - 30 = 470
        assert Decimal(transactions[0]["running_balance"]) == Decimal("470.00")
        # Jan 4 Food: 470 - 20 (transport) - 50 = 400
        assert Decimal(transactions[1]["running_balance"]) == Decimal("400.00")
