import pytest
from decimal import Decimal
from datetime import date
from app.models.transaction import TransactionType
from app.models.account import AccountType
from app.models.category import CategoryType


class TestTransactionCRUD:
    """Test CRUD operations for transactions."""

    def test_create_transaction(self, client, auth_headers, test_user, db_session):
        """Test creating a new transaction."""
        from app.models.account import Account
        from app.models.category import Category

        # Create account and category first
        account = Account(
            user_id=test_user.id,
            name="Checking",
            type=AccountType.CHECKING,
            currency="USD"
        )
        category = Category(
            user_id=test_user.id,
            name="Groceries",
            type=CategoryType.EXPENSE
        )
        db_session.add_all([account, category])
        db_session.commit()
        db_session.refresh(account)
        db_session.refresh(category)

        transaction_data = {
            "account_id": account.id,
            "category_id": category.id,
            "type": "debit",
            "amount": "50.75",
            "date": "2024-01-15",
            "payee": "Whole Foods",
            "description": "Weekly groceries",
            "notes": "Organic produce"
        }

        response = client.post(
            "/api/v1/transactions",
            json=transaction_data,
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["account_id"] == account.id
        assert data["category_id"] == category.id
        assert data["type"] == "debit"
        assert Decimal(data["amount"]) == Decimal("50.75")
        assert data["date"] == "2024-01-15"
        assert data["payee"] == "Whole Foods"
        assert data["description"] == "Weekly groceries"
        assert data["notes"] == "Organic produce"
        assert "id" in data
        assert "user_id" in data
        assert "created_at" in data

    def test_create_transaction_without_optional_fields(self, client, auth_headers, test_user, db_session):
        """Test creating transaction with only required fields."""
        from app.models.account import Account

        account = Account(
            user_id=test_user.id,
            name="Checking",
            type=AccountType.CHECKING,
            currency="USD"
        )
        db_session.add(account)
        db_session.commit()
        db_session.refresh(account)

        transaction_data = {
            "account_id": account.id,
            "type": "debit",
            "amount": "25.00",
            "date": "2024-01-15"
        }

        response = client.post(
            "/api/v1/transactions",
            json=transaction_data,
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["category_id"] is None
        assert data["payee"] is None
        assert data["description"] is None

    def test_create_transfer_transaction(self, client, auth_headers, test_user, db_session):
        """Test creating a transfer transaction between accounts."""
        from app.models.account import Account

        # Create two accounts
        account1 = Account(
            user_id=test_user.id,
            name="Checking",
            type=AccountType.CHECKING,
            currency="USD"
        )
        account2 = Account(
            user_id=test_user.id,
            name="Savings",
            type=AccountType.SAVINGS,
            currency="USD"
        )
        db_session.add_all([account1, account2])
        db_session.commit()
        db_session.refresh(account1)
        db_session.refresh(account2)

        transaction_data = {
            "account_id": account1.id,
            "type": "transfer",
            "amount": "500.00",
            "date": "2024-01-15",
            "transfer_account_id": account2.id,
            "description": "Monthly savings"
        }

        response = client.post(
            "/api/v1/transactions",
            json=transaction_data,
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["type"] == "transfer"
        assert data["transfer_account_id"] == account2.id

    def test_create_transaction_without_auth(self, client, test_user, db_session):
        """Test that creating transaction without authentication fails."""
        from app.models.account import Account

        account = Account(
            user_id=test_user.id,
            name="Checking",
            type=AccountType.CHECKING,
            currency="USD"
        )
        db_session.add(account)
        db_session.commit()
        db_session.refresh(account)

        transaction_data = {
            "account_id": account.id,
            "type": "debit",
            "amount": "50.00",
            "date": "2024-01-15"
        }

        response = client.post("/api/v1/transactions", json=transaction_data)
        assert response.status_code == 401

    def test_create_transaction_negative_amount(self, client, auth_headers, test_user, db_session):
        """Test that creating transaction with negative amount fails."""
        from app.models.account import Account

        account = Account(
            user_id=test_user.id,
            name="Checking",
            type=AccountType.CHECKING,
            currency="USD"
        )
        db_session.add(account)
        db_session.commit()
        db_session.refresh(account)

        transaction_data = {
            "account_id": account.id,
            "type": "debit",
            "amount": "-50.00",
            "date": "2024-01-15"
        }

        response = client.post(
            "/api/v1/transactions",
            json=transaction_data,
            headers=auth_headers
        )

        assert response.status_code == 422

    def test_create_transaction_zero_amount(self, client, auth_headers, test_user, db_session):
        """Test that creating transaction with zero amount fails."""
        from app.models.account import Account

        account = Account(
            user_id=test_user.id,
            name="Checking",
            type=AccountType.CHECKING,
            currency="USD"
        )
        db_session.add(account)
        db_session.commit()
        db_session.refresh(account)

        transaction_data = {
            "account_id": account.id,
            "type": "debit",
            "amount": "0.00",
            "date": "2024-01-15"
        }

        response = client.post(
            "/api/v1/transactions",
            json=transaction_data,
            headers=auth_headers
        )

        assert response.status_code == 422

    def test_get_transactions(self, client, auth_headers, test_user, db_session):
        """Test retrieving all transactions for a user."""
        from app.models.account import Account
        from app.models.transaction import Transaction

        account = Account(
            user_id=test_user.id,
            name="Checking",
            type=AccountType.CHECKING,
            currency="USD"
        )
        db_session.add(account)
        db_session.commit()
        db_session.refresh(account)

        # Create test transactions
        transaction1 = Transaction(
            user_id=test_user.id,
            account_id=account.id,
            type=TransactionType.DEBIT,
            amount=Decimal("50.00"),
            date=date(2024, 1, 15),
            payee="Store A"
        )
        transaction2 = Transaction(
            user_id=test_user.id,
            account_id=account.id,
            type=TransactionType.CREDIT,
            amount=Decimal("100.00"),
            date=date(2024, 1, 16),
            payee="Employer"
        )
        db_session.add_all([transaction1, transaction2])
        db_session.commit()

        response = client.get("/api/v1/transactions", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_get_transactions_filtered_by_account(self, client, auth_headers, test_user, db_session):
        """Test retrieving transactions filtered by account."""
        from app.models.account import Account
        from app.models.transaction import Transaction

        # Create two accounts
        account1 = Account(
            user_id=test_user.id,
            name="Checking",
            type=AccountType.CHECKING,
            currency="USD"
        )
        account2 = Account(
            user_id=test_user.id,
            name="Savings",
            type=AccountType.SAVINGS,
            currency="USD"
        )
        db_session.add_all([account1, account2])
        db_session.commit()
        db_session.refresh(account1)
        db_session.refresh(account2)

        # Create transactions for both accounts
        transaction1 = Transaction(
            user_id=test_user.id,
            account_id=account1.id,
            type=TransactionType.DEBIT,
            amount=Decimal("50.00"),
            date=date(2024, 1, 15)
        )
        transaction2 = Transaction(
            user_id=test_user.id,
            account_id=account2.id,
            type=TransactionType.CREDIT,
            amount=Decimal("100.00"),
            date=date(2024, 1, 16)
        )
        db_session.add_all([transaction1, transaction2])
        db_session.commit()

        # Get transactions for account1 only
        response = client.get(
            f"/api/v1/transactions?account_id={account1.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["account_id"] == account1.id

    def test_get_transactions_filtered_by_date_range(self, client, auth_headers, test_user, db_session):
        """Test retrieving transactions filtered by date range."""
        from app.models.account import Account
        from app.models.transaction import Transaction

        account = Account(
            user_id=test_user.id,
            name="Checking",
            type=AccountType.CHECKING,
            currency="USD"
        )
        db_session.add(account)
        db_session.commit()
        db_session.refresh(account)

        # Create transactions with different dates
        transaction1 = Transaction(
            user_id=test_user.id,
            account_id=account.id,
            type=TransactionType.DEBIT,
            amount=Decimal("50.00"),
            date=date(2024, 1, 10)
        )
        transaction2 = Transaction(
            user_id=test_user.id,
            account_id=account.id,
            type=TransactionType.DEBIT,
            amount=Decimal("75.00"),
            date=date(2024, 1, 20)
        )
        transaction3 = Transaction(
            user_id=test_user.id,
            account_id=account.id,
            type=TransactionType.DEBIT,
            amount=Decimal("100.00"),
            date=date(2024, 1, 30)
        )
        db_session.add_all([transaction1, transaction2, transaction3])
        db_session.commit()

        # Get transactions between Jan 15 and Jan 25
        response = client.get(
            "/api/v1/transactions?start_date=2024-01-15&end_date=2024-01-25",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert Decimal(data[0]["amount"]) == Decimal("75.00")

    def test_get_transaction_by_id(self, client, auth_headers, test_user, db_session):
        """Test retrieving a specific transaction by ID."""
        from app.models.account import Account
        from app.models.transaction import Transaction

        account = Account(
            user_id=test_user.id,
            name="Checking",
            type=AccountType.CHECKING,
            currency="USD"
        )
        db_session.add(account)
        db_session.commit()
        db_session.refresh(account)

        transaction = Transaction(
            user_id=test_user.id,
            account_id=account.id,
            type=TransactionType.DEBIT,
            amount=Decimal("50.75"),
            date=date(2024, 1, 15),
            payee="Store A"
        )
        db_session.add(transaction)
        db_session.commit()
        db_session.refresh(transaction)

        response = client.get(f"/api/v1/transactions/{transaction.id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == transaction.id
        assert Decimal(data["amount"]) == Decimal("50.75")
        assert data["payee"] == "Store A"

    def test_get_nonexistent_transaction(self, client, auth_headers):
        """Test retrieving a non-existent transaction returns 404."""
        response = client.get("/api/v1/transactions/99999", headers=auth_headers)
        assert response.status_code == 404

    def test_update_transaction(self, client, auth_headers, test_user, db_session):
        """Test updating a transaction."""
        from app.models.account import Account
        from app.models.transaction import Transaction

        account = Account(
            user_id=test_user.id,
            name="Checking",
            type=AccountType.CHECKING,
            currency="USD"
        )
        db_session.add(account)
        db_session.commit()
        db_session.refresh(account)

        transaction = Transaction(
            user_id=test_user.id,
            account_id=account.id,
            type=TransactionType.DEBIT,
            amount=Decimal("50.00"),
            date=date(2024, 1, 15),
            payee="Old Payee"
        )
        db_session.add(transaction)
        db_session.commit()
        db_session.refresh(transaction)

        update_data = {
            "amount": "75.50",
            "payee": "New Payee",
            "description": "Updated description"
        }

        response = client.put(
            f"/api/v1/transactions/{transaction.id}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert Decimal(data["amount"]) == Decimal("75.50")
        assert data["payee"] == "New Payee"
        assert data["description"] == "Updated description"
        assert data["type"] == "debit"  # Unchanged

    def test_delete_transaction(self, client, auth_headers, test_user, db_session):
        """Test deleting a transaction."""
        from app.models.account import Account
        from app.models.transaction import Transaction

        account = Account(
            user_id=test_user.id,
            name="Checking",
            type=AccountType.CHECKING,
            currency="USD"
        )
        db_session.add(account)
        db_session.commit()
        db_session.refresh(account)

        transaction = Transaction(
            user_id=test_user.id,
            account_id=account.id,
            type=TransactionType.DEBIT,
            amount=Decimal("50.00"),
            date=date(2024, 1, 15)
        )
        db_session.add(transaction)
        db_session.commit()
        db_session.refresh(transaction)

        response = client.delete(f"/api/v1/transactions/{transaction.id}", headers=auth_headers)

        assert response.status_code == 204

        # Verify it's deleted
        response = client.get(f"/api/v1/transactions/{transaction.id}", headers=auth_headers)
        assert response.status_code == 404

    def test_user_can_only_access_own_transactions(self, client, db_session):
        """Test that users can only access their own transactions."""
        from app.models.user import User
        from app.models.account import Account
        from app.models.transaction import Transaction
        from app.core.security import get_password_hash

        # Create two users
        user1 = User(
            email="user1@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="User One"
        )
        user2 = User(
            email="user2@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="User Two"
        )
        db_session.add_all([user1, user2])
        db_session.commit()
        db_session.refresh(user1)
        db_session.refresh(user2)

        # Create account and transaction for user1
        account1 = Account(
            user_id=user1.id,
            name="User1 Account",
            type=AccountType.CHECKING,
            currency="USD"
        )
        db_session.add(account1)
        db_session.commit()
        db_session.refresh(account1)

        transaction1 = Transaction(
            user_id=user1.id,
            account_id=account1.id,
            type=TransactionType.DEBIT,
            amount=Decimal("50.00"),
            date=date(2024, 1, 15)
        )
        db_session.add(transaction1)
        db_session.commit()
        db_session.refresh(transaction1)

        # Login as user2
        login_response = client.post(
            "/api/v1/auth/login",
            data={"username": user2.email, "password": "password123"}
        )
        user2_token = login_response.json()["access_token"]
        user2_headers = {"Authorization": f"Bearer {user2_token}"}

        # Try to access user1's transaction as user2
        response = client.get(f"/api/v1/transactions/{transaction1.id}", headers=user2_headers)
        assert response.status_code == 404  # Should not be able to access

    def test_list_transactions_only_shows_user_transactions(self, client, db_session):
        """Test that listing transactions only shows the current user's transactions."""
        from app.models.user import User
        from app.models.account import Account
        from app.models.transaction import Transaction
        from app.core.security import get_password_hash

        # Create two users
        user1 = User(
            email="user1@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="User One"
        )
        user2 = User(
            email="user2@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="User Two"
        )
        db_session.add_all([user1, user2])
        db_session.commit()
        db_session.refresh(user1)
        db_session.refresh(user2)

        # Create accounts for both users
        account1 = Account(user_id=user1.id, name="User1 Account", type=AccountType.CHECKING, currency="USD")
        account2 = Account(user_id=user2.id, name="User2 Account", type=AccountType.CHECKING, currency="USD")
        db_session.add_all([account1, account2])
        db_session.commit()
        db_session.refresh(account1)
        db_session.refresh(account2)

        # Create transactions for both users
        transaction1 = Transaction(
            user_id=user1.id,
            account_id=account1.id,
            type=TransactionType.DEBIT,
            amount=Decimal("50.00"),
            date=date(2024, 1, 15)
        )
        transaction2 = Transaction(
            user_id=user2.id,
            account_id=account2.id,
            type=TransactionType.CREDIT,
            amount=Decimal("100.00"),
            date=date(2024, 1, 16)
        )
        db_session.add_all([transaction1, transaction2])
        db_session.commit()

        # Login as user1
        login_response = client.post(
            "/api/v1/auth/login",
            data={"username": user1.email, "password": "password123"}
        )
        user1_token = login_response.json()["access_token"]
        user1_headers = {"Authorization": f"Bearer {user1_token}"}

        # Get transactions for user1
        response = client.get("/api/v1/transactions", headers=user1_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["account_id"] == account1.id
