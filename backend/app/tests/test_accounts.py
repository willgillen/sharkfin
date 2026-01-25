import pytest
from decimal import Decimal
from app.models.account import AccountType


class TestAccountCRUD:
    """Test CRUD operations for accounts."""

    def test_create_account(self, client, auth_headers):
        """Test creating a new account."""
        account_data = {
            "name": "My Checking Account",
            "type": "checking",
            "currency": "USD",
            "opening_balance": "1000.50",
            "notes": "Primary checking account"
        }

        response = client.post(
            "/api/v1/accounts",
            json=account_data,
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == account_data["name"]
        assert data["type"] == account_data["type"]
        assert data["currency"] == account_data["currency"]
        assert Decimal(data["opening_balance"]) == Decimal(account_data["opening_balance"])
        assert Decimal(data["current_balance"]) == Decimal(account_data["opening_balance"])  # Calculated from opening
        assert data["notes"] == account_data["notes"]
        assert data["is_active"] is True
        assert "id" in data
        assert "user_id" in data
        assert "created_at" in data

    def test_create_account_without_auth(self, client):
        """Test that creating account without authentication fails."""
        account_data = {
            "name": "My Checking Account",
            "type": "checking"
        }

        response = client.post("/api/v1/accounts", json=account_data)
        assert response.status_code == 401

    def test_create_account_invalid_currency(self, client, auth_headers):
        """Test creating account with invalid currency code."""
        account_data = {
            "name": "My Account",
            "type": "checking",
            "currency": "US"  # Invalid: should be 3 characters
        }

        response = client.post(
            "/api/v1/accounts",
            json=account_data,
            headers=auth_headers
        )

        assert response.status_code == 422

    def test_get_accounts(self, client, auth_headers, test_user, db_session):
        """Test retrieving all accounts for a user."""
        from app.models.account import Account

        # Create test accounts
        account1 = Account(
            user_id=test_user.id,
            name="Checking",
            type=AccountType.CHECKING,
            currency="USD",
            opening_balance=Decimal("1000.00")
        )
        account2 = Account(
            user_id=test_user.id,
            name="Savings",
            type=AccountType.SAVINGS,
            currency="USD",
            opening_balance=Decimal("5000.00")
        )
        db_session.add_all([account1, account2])
        db_session.commit()

        response = client.get("/api/v1/accounts", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "Checking"
        assert data[1]["name"] == "Savings"

    def test_get_account_by_id(self, client, auth_headers, test_user, db_session):
        """Test retrieving a specific account by ID."""
        from app.models.account import Account

        account = Account(
            user_id=test_user.id,
            name="My Checking",
            type=AccountType.CHECKING,
            currency="USD",
            opening_balance=Decimal("1500.00")
        )
        db_session.add(account)
        db_session.commit()
        db_session.refresh(account)

        response = client.get(f"/api/v1/accounts/{account.id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == account.id
        assert data["name"] == "My Checking"
        assert Decimal(data["current_balance"]) == Decimal("1500.00")

    def test_get_nonexistent_account(self, client, auth_headers):
        """Test retrieving a non-existent account returns 404."""
        response = client.get("/api/v1/accounts/99999", headers=auth_headers)
        assert response.status_code == 404

    def test_update_account(self, client, auth_headers, test_user, db_session):
        """Test updating an account."""
        from app.models.account import Account

        account = Account(
            user_id=test_user.id,
            name="Old Name",
            type=AccountType.CHECKING,
            currency="USD",
            opening_balance=Decimal("1000.00")
        )
        db_session.add(account)
        db_session.commit()
        db_session.refresh(account)

        update_data = {
            "name": "Updated Name",
            "opening_balance": "2000.00"
        }

        response = client.put(
            f"/api/v1/accounts/{account.id}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert Decimal(data["current_balance"]) == Decimal("2000.00")
        assert data["type"] == "checking"  # Unchanged

    def test_delete_account(self, client, auth_headers, test_user, db_session):
        """Test deleting an account."""
        from app.models.account import Account

        account = Account(
            user_id=test_user.id,
            name="To Delete",
            type=AccountType.CHECKING,
            currency="USD"
        )
        db_session.add(account)
        db_session.commit()
        db_session.refresh(account)

        response = client.delete(f"/api/v1/accounts/{account.id}", headers=auth_headers)

        assert response.status_code == 204

        # Verify it's deleted
        response = client.get(f"/api/v1/accounts/{account.id}", headers=auth_headers)
        assert response.status_code == 404

    def test_user_can_only_access_own_accounts(self, client, db_session):
        """Test that users can only access their own accounts."""
        from app.models.user import User
        from app.models.account import Account
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

        # Create account for user1
        account1 = Account(
            user_id=user1.id,
            name="User1 Account",
            type=AccountType.CHECKING,
            currency="USD"
        )
        db_session.add(account1)
        db_session.commit()
        db_session.refresh(account1)

        # Login as user2
        login_response = client.post(
            "/api/v1/auth/login",
            data={"username": user2.email, "password": "password123"}
        )
        user2_token = login_response.json()["access_token"]
        user2_headers = {"Authorization": f"Bearer {user2_token}"}

        # Try to access user1's account as user2
        response = client.get(f"/api/v1/accounts/{account1.id}", headers=user2_headers)
        assert response.status_code == 404  # Should not be able to access

    def test_list_accounts_only_shows_user_accounts(self, client, db_session):
        """Test that listing accounts only shows the current user's accounts."""
        from app.models.user import User
        from app.models.account import Account
        from app.core.security import get_password_hash

        # Create two users with accounts
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
        account2 = Account(user_id=user2.id, name="User2 Account", type=AccountType.SAVINGS, currency="USD")
        db_session.add_all([account1, account2])
        db_session.commit()

        # Login as user1
        login_response = client.post(
            "/api/v1/auth/login",
            data={"username": user1.email, "password": "password123"}
        )
        user1_token = login_response.json()["access_token"]
        user1_headers = {"Authorization": f"Bearer {user1_token}"}

        # Get accounts for user1
        response = client.get("/api/v1/accounts", headers=user1_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "User1 Account"

    def test_create_account_with_institution(self, client, auth_headers):
        """Test creating account with institution field."""
        account_data = {
            "name": "Chase Checking",
            "type": "checking",
            "institution": "Chase Bank",
            "account_number": "1234",
            "currency": "USD",
            "opening_balance": "2500.00",
            "notes": "Primary checking at Chase"
        }

        response = client.post(
            "/api/v1/accounts",
            json=account_data,
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == account_data["name"]
        assert data["institution"] == account_data["institution"]
        assert data["account_number"] == account_data["account_number"]
        assert data["type"] == account_data["type"]
        assert Decimal(data["current_balance"]) == Decimal(account_data["opening_balance"])

    def test_institution_persists_after_save(self, client, auth_headers, test_user, db_session):
        """Test that institution field persists correctly in database."""
        from app.models.account import Account

        # Create account with institution
        account = Account(
            user_id=test_user.id,
            name="Wells Fargo Savings",
            type=AccountType.SAVINGS,
            institution="Wells Fargo",
            account_number="5678",
            currency="USD",
            opening_balance=Decimal("10000.00")
        )
        db_session.add(account)
        db_session.commit()
        db_session.refresh(account)

        # Verify institution persisted
        assert account.institution == "Wells Fargo"
        assert account.account_number == "5678"

        # Retrieve via API and verify
        response = client.get(f"/api/v1/accounts/{account.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["institution"] == "Wells Fargo"
        assert data["account_number"] == "5678"

    def test_update_account_institution(self, client, auth_headers, test_user, db_session):
        """Test updating account institution field."""
        from app.models.account import Account

        # Create account without institution
        account = Account(
            user_id=test_user.id,
            name="Generic Account",
            type=AccountType.CHECKING,
            currency="USD",
            opening_balance=Decimal("1000.00")
        )
        db_session.add(account)
        db_session.commit()
        db_session.refresh(account)

        # Update to add institution
        update_data = {
            "institution": "Bank of America",
            "account_number": "9999"
        }

        response = client.put(
            f"/api/v1/accounts/{account.id}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["institution"] == "Bank of America"
        assert data["account_number"] == "9999"

    def test_account_number_validation(self, client, auth_headers):
        """Test that account_number field validates length (max 4 digits)."""
        account_data = {
            "name": "Invalid Account",
            "type": "checking",
            "institution": "Some Bank",
            "account_number": "12345",  # Too long - should be max 4
            "currency": "USD",
            "opening_balance": "1000.00"
        }

        response = client.post(
            "/api/v1/accounts",
            json=account_data,
            headers=auth_headers
        )

        # Should fail validation
        assert response.status_code == 422
