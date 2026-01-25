import pytest
from decimal import Decimal
from datetime import date
from app.models.account import AccountType


class TestAccountBalanceCalculation:
    """Test balance calculation functionality with opening_balance."""

    def test_create_account_with_opening_balance(self, client, auth_headers):
        """Test creating account with opening_balance and opening_balance_date."""
        account_data = {
            "name": "New Account",
            "type": "checking",
            "currency": "USD",
            "opening_balance": "2500.50",
            "opening_balance_date": "2026-01-01",
            "notes": "Account with opening balance"
        }

        response = client.post(
            "/api/v1/accounts",
            json=account_data,
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == account_data["name"]
        assert Decimal(data["opening_balance"]) == Decimal(account_data["opening_balance"])
        assert data["opening_balance_date"] == account_data["opening_balance_date"]
        # With no transactions, current_balance should equal opening_balance
        assert Decimal(data["current_balance"]) == Decimal(account_data["opening_balance"])

    def test_balance_calculation_with_no_transactions(self, client, auth_headers, test_user, db_session):
        """Test that balance equals opening_balance when there are no transactions."""
        from app.models.account import Account

        account = Account(
            user_id=test_user.id,
            name="Empty Account",
            type=AccountType.SAVINGS,
            currency="USD",
            opening_balance=Decimal("1000.00"),
            opening_balance_date=None
        )
        db_session.add(account)
        db_session.commit()
        db_session.refresh(account)

        response = client.get(f"/api/v1/accounts/{account.id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert Decimal(data["current_balance"]) == Decimal("1000.00")
        assert Decimal(data["opening_balance"]) == Decimal("1000.00")

    def test_balance_calculation_with_credit_transactions(self, client, auth_headers, test_user, db_session):
        """Test that credit transactions add to the balance."""
        from app.models.account import Account
        from app.models.transaction import Transaction, TransactionType

        account = Account(
            user_id=test_user.id,
            name="Test Account",
            type=AccountType.CHECKING,
            currency="USD",
            opening_balance=Decimal("1000.00"),
            opening_balance_date=date(2026, 1, 1)
        )
        db_session.add(account)
        db_session.commit()
        db_session.refresh(account)

        # Add credit transactions
        tx1 = Transaction(
            user_id=test_user.id,
            account_id=account.id,
            type=TransactionType.CREDIT,
            amount=Decimal("500.00"),
            date=date(2026, 1, 15),
            description="Deposit"
        )
        tx2 = Transaction(
            user_id=test_user.id,
            account_id=account.id,
            type=TransactionType.CREDIT,
            amount=Decimal("250.00"),
            date=date(2026, 1, 20),
            description="Another deposit"
        )
        db_session.add_all([tx1, tx2])
        db_session.commit()

        response = client.get(f"/api/v1/accounts/{account.id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        # 1000.00 opening + 500.00 + 250.00 = 1750.00
        assert Decimal(data["current_balance"]) == Decimal("1750.00")

    def test_balance_calculation_with_debit_transactions(self, client, auth_headers, test_user, db_session):
        """Test that debit transactions subtract from the balance."""
        from app.models.account import Account
        from app.models.transaction import Transaction, TransactionType

        account = Account(
            user_id=test_user.id,
            name="Test Account",
            type=AccountType.CHECKING,
            currency="USD",
            opening_balance=Decimal("1000.00"),
            opening_balance_date=date(2026, 1, 1)
        )
        db_session.add(account)
        db_session.commit()
        db_session.refresh(account)

        # Add debit transactions
        tx1 = Transaction(
            user_id=test_user.id,
            account_id=account.id,
            type=TransactionType.DEBIT,
            amount=Decimal("200.00"),
            date=date(2026, 1, 15),
            description="Withdrawal"
        )
        tx2 = Transaction(
            user_id=test_user.id,
            account_id=account.id,
            type=TransactionType.DEBIT,
            amount=Decimal("150.00"),
            date=date(2026, 1, 20),
            description="Payment"
        )
        db_session.add_all([tx1, tx2])
        db_session.commit()

        response = client.get(f"/api/v1/accounts/{account.id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        # 1000.00 opening - 200.00 - 150.00 = 650.00
        assert Decimal(data["current_balance"]) == Decimal("650.00")

    def test_balance_calculation_with_mixed_transactions(self, client, auth_headers, test_user, db_session):
        """Test balance calculation with both credit and debit transactions."""
        from app.models.account import Account
        from app.models.transaction import Transaction, TransactionType

        account = Account(
            user_id=test_user.id,
            name="Test Account",
            type=AccountType.CHECKING,
            currency="USD",
            opening_balance=Decimal("1000.00"),
            opening_balance_date=date(2026, 1, 1)
        )
        db_session.add(account)
        db_session.commit()
        db_session.refresh(account)

        # Add mixed transactions
        transactions = [
            Transaction(user_id=test_user.id, account_id=account.id, type=TransactionType.CREDIT,
                       amount=Decimal("500.00"), date=date(2026, 1, 5), description="Salary"),
            Transaction(user_id=test_user.id, account_id=account.id, type=TransactionType.DEBIT,
                       amount=Decimal("200.00"), date=date(2026, 1, 10), description="Groceries"),
            Transaction(user_id=test_user.id, account_id=account.id, type=TransactionType.CREDIT,
                       amount=Decimal("100.00"), date=date(2026, 1, 15), description="Refund"),
            Transaction(user_id=test_user.id, account_id=account.id, type=TransactionType.DEBIT,
                       amount=Decimal("300.00"), date=date(2026, 1, 20), description="Rent"),
        ]
        db_session.add_all(transactions)
        db_session.commit()

        response = client.get(f"/api/v1/accounts/{account.id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        # 1000.00 + 500.00 - 200.00 + 100.00 - 300.00 = 1100.00
        assert Decimal(data["current_balance"]) == Decimal("1100.00")

    def test_balance_calculation_with_transfer_transactions(self, client, auth_headers, test_user, db_session):
        """Test balance calculation with transfer transactions affecting both accounts."""
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
            account_id=account1.id,  # Source account
            transfer_account_id=account2.id,  # Destination account
            type=TransactionType.TRANSFER,
            amount=Decimal("300.00"),
            date=date(2026, 1, 15),
            description="Transfer to savings"
        )
        db_session.add(transfer)
        db_session.commit()

        # Check account1 balance (should decrease)
        response1 = client.get(f"/api/v1/accounts/{account1.id}", headers=auth_headers)
        assert response1.status_code == 200
        data1 = response1.json()
        # 1000.00 - 300.00 (transfer out) = 700.00
        assert Decimal(data1["current_balance"]) == Decimal("700.00")

        # Check account2 balance (should increase)
        response2 = client.get(f"/api/v1/accounts/{account2.id}", headers=auth_headers)
        assert response2.status_code == 200
        data2 = response2.json()
        # 5000.00 + 300.00 (transfer in) = 5300.00
        assert Decimal(data2["current_balance"]) == Decimal("5300.00")

    def test_balance_calculation_respects_opening_balance_date(self, client, auth_headers, test_user, db_session):
        """Test that transactions before opening_balance_date are ignored."""
        from app.models.account import Account
        from app.models.transaction import Transaction, TransactionType

        account = Account(
            user_id=test_user.id,
            name="Test Account",
            type=AccountType.CHECKING,
            currency="USD",
            opening_balance=Decimal("1000.00"),
            opening_balance_date=date(2026, 1, 15)  # Opening balance is as of Jan 15
        )
        db_session.add(account)
        db_session.commit()
        db_session.refresh(account)

        # Add transactions before and after opening_balance_date
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
            type=TransactionType.CREDIT,
            amount=Decimal("200.00"),
            date=date(2026, 1, 20),  # After opening_balance_date
            description="Should be counted"
        )
        db_session.add_all([tx_before, tx_after])
        db_session.commit()

        response = client.get(f"/api/v1/accounts/{account.id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        # Only tx_after should be counted: 1000.00 + 200.00 = 1200.00
        assert Decimal(data["current_balance"]) == Decimal("1200.00")

    def test_update_opening_balance_for_reconciliation(self, client, auth_headers, test_user, db_session):
        """Test updating opening_balance to reconcile with bank statement."""
        from app.models.account import Account

        account = Account(
            user_id=test_user.id,
            name="Reconciliation Test",
            type=AccountType.CHECKING,
            currency="USD",
            opening_balance=Decimal("1000.00"),
            opening_balance_date=date(2026, 1, 1)
        )
        db_session.add(account)
        db_session.commit()
        db_session.refresh(account)

        # Update opening balance to reconcile
        update_data = {
            "opening_balance": "1500.00",
            "opening_balance_date": "2026-01-15"
        }

        response = client.put(
            f"/api/v1/accounts/{account.id}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert Decimal(data["opening_balance"]) == Decimal("1500.00")
        assert data["opening_balance_date"] == "2026-01-15"
        assert Decimal(data["current_balance"]) == Decimal("1500.00")

    def test_account_list_includes_calculated_balance(self, client, auth_headers, test_user, db_session):
        """Test that listing accounts includes calculated balances for all accounts."""
        from app.models.account import Account
        from app.models.transaction import Transaction, TransactionType

        # Create two accounts with transactions
        account1 = Account(
            user_id=test_user.id,
            name="Account 1",
            type=AccountType.CHECKING,
            currency="USD",
            opening_balance=Decimal("1000.00"),
            opening_balance_date=date(2026, 1, 1)
        )
        account2 = Account(
            user_id=test_user.id,
            name="Account 2",
            type=AccountType.SAVINGS,
            currency="USD",
            opening_balance=Decimal("5000.00"),
            opening_balance_date=date(2026, 1, 1)
        )
        db_session.add_all([account1, account2])
        db_session.commit()
        db_session.refresh(account1)
        db_session.refresh(account2)

        # Add transactions
        tx1 = Transaction(
            user_id=test_user.id,
            account_id=account1.id,
            type=TransactionType.CREDIT,
            amount=Decimal("500.00"),
            date=date(2026, 1, 15),
            description="Deposit"
        )
        tx2 = Transaction(
            user_id=test_user.id,
            account_id=account2.id,
            type=TransactionType.DEBIT,
            amount=Decimal("1000.00"),
            date=date(2026, 1, 20),
            description="Withdrawal"
        )
        db_session.add_all([tx1, tx2])
        db_session.commit()

        response = client.get("/api/v1/accounts", headers=auth_headers)

        assert response.status_code == 200
        accounts = response.json()
        assert len(accounts) == 2

        # Find accounts by name
        acc1_data = next(a for a in accounts if a["name"] == "Account 1")
        acc2_data = next(a for a in accounts if a["name"] == "Account 2")

        # Verify calculated balances
        assert Decimal(acc1_data["current_balance"]) == Decimal("1500.00")  # 1000 + 500
        assert Decimal(acc2_data["current_balance"]) == Decimal("4000.00")  # 5000 - 1000
