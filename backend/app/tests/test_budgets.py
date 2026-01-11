import pytest
from decimal import Decimal
from datetime import date
from dateutil.relativedelta import relativedelta
from app.models.budget import BudgetPeriod
from app.models.category import CategoryType


class TestBudgetCRUD:
    """Test CRUD operations for budgets."""

    def test_create_budget(self, client, auth_headers, test_user, db_session):
        """Test creating a new budget."""
        from app.models.category import Category

        # Create a category first
        category = Category(
            user_id=test_user.id,
            name="Groceries",
            type=CategoryType.EXPENSE
        )
        db_session.add(category)
        db_session.commit()
        db_session.refresh(category)

        budget_data = {
            "category_id": category.id,
            "name": "Monthly Grocery Budget",
            "amount": "500.00",
            "period": "monthly",
            "start_date": "2024-01-01",
            "rollover": True,
            "alert_enabled": True,
            "alert_threshold": "85.0",
            "notes": "Budget for groceries"
        }

        response = client.post(
            "/api/v1/budgets",
            json=budget_data,
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["category_id"] == category.id
        assert data["name"] == budget_data["name"]
        assert Decimal(data["amount"]) == Decimal(budget_data["amount"])
        assert data["period"] == budget_data["period"]
        assert data["start_date"] == budget_data["start_date"]
        assert data["rollover"] is True
        assert data["alert_enabled"] is True
        assert Decimal(data["alert_threshold"]) == Decimal(budget_data["alert_threshold"])
        assert "id" in data
        assert "user_id" in data

    def test_create_budget_with_end_date(self, client, auth_headers, test_user, db_session):
        """Test creating budget with an end date."""
        from app.models.category import Category

        category = Category(
            user_id=test_user.id,
            name="Vacation",
            type=CategoryType.EXPENSE
        )
        db_session.add(category)
        db_session.commit()
        db_session.refresh(category)

        budget_data = {
            "category_id": category.id,
            "name": "Vacation Fund",
            "amount": "2000.00",
            "period": "monthly",
            "start_date": "2024-01-01",
            "end_date": "2024-12-31"
        }

        response = client.post(
            "/api/v1/budgets",
            json=budget_data,
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["end_date"] == budget_data["end_date"]

    def test_create_budget_without_auth(self, client, test_user, db_session):
        """Test that creating budget without authentication fails."""
        from app.models.category import Category

        category = Category(
            user_id=test_user.id,
            name="Test",
            type=CategoryType.EXPENSE
        )
        db_session.add(category)
        db_session.commit()
        db_session.refresh(category)

        budget_data = {
            "category_id": category.id,
            "name": "Test Budget",
            "amount": "100.00",
            "period": "monthly",
            "start_date": "2024-01-01"
        }

        response = client.post("/api/v1/budgets", json=budget_data)
        assert response.status_code == 401

    def test_create_budget_negative_amount(self, client, auth_headers, test_user, db_session):
        """Test that creating budget with negative amount fails."""
        from app.models.category import Category

        category = Category(
            user_id=test_user.id,
            name="Test",
            type=CategoryType.EXPENSE
        )
        db_session.add(category)
        db_session.commit()
        db_session.refresh(category)

        budget_data = {
            "category_id": category.id,
            "name": "Test Budget",
            "amount": "-100.00",
            "period": "monthly",
            "start_date": "2024-01-01"
        }

        response = client.post(
            "/api/v1/budgets",
            json=budget_data,
            headers=auth_headers
        )

        assert response.status_code == 422

    def test_create_budget_invalid_alert_threshold(self, client, auth_headers, test_user, db_session):
        """Test creating budget with invalid alert threshold."""
        from app.models.category import Category

        category = Category(
            user_id=test_user.id,
            name="Test",
            type=CategoryType.EXPENSE
        )
        db_session.add(category)
        db_session.commit()
        db_session.refresh(category)

        budget_data = {
            "category_id": category.id,
            "name": "Test Budget",
            "amount": "100.00",
            "period": "monthly",
            "start_date": "2024-01-01",
            "alert_threshold": "150.0"  # Invalid: > 100
        }

        response = client.post(
            "/api/v1/budgets",
            json=budget_data,
            headers=auth_headers
        )

        assert response.status_code == 422

    def test_create_budget_end_date_before_start_date(self, client, auth_headers, test_user, db_session):
        """Test creating budget with end_date before start_date fails."""
        from app.models.category import Category

        category = Category(
            user_id=test_user.id,
            name="Test",
            type=CategoryType.EXPENSE
        )
        db_session.add(category)
        db_session.commit()
        db_session.refresh(category)

        budget_data = {
            "category_id": category.id,
            "name": "Test Budget",
            "amount": "100.00",
            "period": "monthly",
            "start_date": "2024-12-31",
            "end_date": "2024-01-01"  # Before start_date
        }

        response = client.post(
            "/api/v1/budgets",
            json=budget_data,
            headers=auth_headers
        )

        assert response.status_code == 422

    def test_get_budgets(self, client, auth_headers, test_user, db_session):
        """Test retrieving all budgets for a user."""
        from app.models.category import Category
        from app.models.budget import Budget

        # Create categories
        category1 = Category(
            user_id=test_user.id,
            name="Groceries",
            type=CategoryType.EXPENSE
        )
        category2 = Category(
            user_id=test_user.id,
            name="Entertainment",
            type=CategoryType.EXPENSE
        )
        db_session.add_all([category1, category2])
        db_session.commit()
        db_session.refresh(category1)
        db_session.refresh(category2)

        # Create budgets
        budget1 = Budget(
            user_id=test_user.id,
            category_id=category1.id,
            name="Grocery Budget",
            amount=Decimal("500.00"),
            period=BudgetPeriod.MONTHLY,
            start_date=date(2024, 1, 1)
        )
        budget2 = Budget(
            user_id=test_user.id,
            category_id=category2.id,
            name="Entertainment Budget",
            amount=Decimal("200.00"),
            period=BudgetPeriod.MONTHLY,
            start_date=date(2024, 1, 1)
        )
        db_session.add_all([budget1, budget2])
        db_session.commit()

        response = client.get("/api/v1/budgets", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "Grocery Budget"
        assert data[1]["name"] == "Entertainment Budget"

    def test_get_budget_by_id(self, client, auth_headers, test_user, db_session):
        """Test retrieving a specific budget by ID."""
        from app.models.category import Category
        from app.models.budget import Budget

        category = Category(
            user_id=test_user.id,
            name="Groceries",
            type=CategoryType.EXPENSE
        )
        db_session.add(category)
        db_session.commit()
        db_session.refresh(category)

        budget = Budget(
            user_id=test_user.id,
            category_id=category.id,
            name="Grocery Budget",
            amount=Decimal("500.00"),
            period=BudgetPeriod.MONTHLY,
            start_date=date(2024, 1, 1)
        )
        db_session.add(budget)
        db_session.commit()
        db_session.refresh(budget)

        response = client.get(f"/api/v1/budgets/{budget.id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == budget.id
        assert data["name"] == "Grocery Budget"
        assert Decimal(data["amount"]) == Decimal("500.00")

    def test_get_nonexistent_budget(self, client, auth_headers):
        """Test retrieving a non-existent budget returns 404."""
        response = client.get("/api/v1/budgets/99999", headers=auth_headers)
        assert response.status_code == 404

    def test_update_budget(self, client, auth_headers, test_user, db_session):
        """Test updating a budget."""
        from app.models.category import Category
        from app.models.budget import Budget

        category = Category(
            user_id=test_user.id,
            name="Groceries",
            type=CategoryType.EXPENSE
        )
        db_session.add(category)
        db_session.commit()
        db_session.refresh(category)

        budget = Budget(
            user_id=test_user.id,
            category_id=category.id,
            name="Old Name",
            amount=Decimal("500.00"),
            period=BudgetPeriod.MONTHLY,
            start_date=date(2024, 1, 1)
        )
        db_session.add(budget)
        db_session.commit()
        db_session.refresh(budget)

        update_data = {
            "name": "Updated Budget Name",
            "amount": "750.00"
        }

        response = client.put(
            f"/api/v1/budgets/{budget.id}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Budget Name"
        assert Decimal(data["amount"]) == Decimal("750.00")
        assert data["period"] == "monthly"  # Unchanged

    def test_delete_budget(self, client, auth_headers, test_user, db_session):
        """Test deleting a budget."""
        from app.models.category import Category
        from app.models.budget import Budget

        category = Category(
            user_id=test_user.id,
            name="Groceries",
            type=CategoryType.EXPENSE
        )
        db_session.add(category)
        db_session.commit()
        db_session.refresh(category)

        budget = Budget(
            user_id=test_user.id,
            category_id=category.id,
            name="To Delete",
            amount=Decimal("500.00"),
            period=BudgetPeriod.MONTHLY,
            start_date=date(2024, 1, 1)
        )
        db_session.add(budget)
        db_session.commit()
        db_session.refresh(budget)

        response = client.delete(f"/api/v1/budgets/{budget.id}", headers=auth_headers)

        assert response.status_code == 204

        # Verify it's deleted
        response = client.get(f"/api/v1/budgets/{budget.id}", headers=auth_headers)
        assert response.status_code == 404

    def test_user_can_only_access_own_budgets(self, client, db_session):
        """Test that users can only access their own budgets."""
        from app.models.user import User
        from app.models.category import Category
        from app.models.budget import Budget
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

        # Create category and budget for user1
        category1 = Category(
            user_id=user1.id,
            name="User1 Category",
            type=CategoryType.EXPENSE
        )
        db_session.add(category1)
        db_session.commit()
        db_session.refresh(category1)

        budget1 = Budget(
            user_id=user1.id,
            category_id=category1.id,
            name="User1 Budget",
            amount=Decimal("500.00"),
            period=BudgetPeriod.MONTHLY,
            start_date=date(2024, 1, 1)
        )
        db_session.add(budget1)
        db_session.commit()
        db_session.refresh(budget1)

        # Login as user2
        login_response = client.post(
            "/api/v1/auth/login",
            data={"username": user2.email, "password": "password123"}
        )
        user2_token = login_response.json()["access_token"]
        user2_headers = {"Authorization": f"Bearer {user2_token}"}

        # Try to access user1's budget as user2
        response = client.get(f"/api/v1/budgets/{budget1.id}", headers=user2_headers)
        assert response.status_code == 404  # Should not be able to access

    def test_list_budgets_only_shows_user_budgets(self, client, db_session):
        """Test that listing budgets only shows the current user's budgets."""
        from app.models.user import User
        from app.models.category import Category
        from app.models.budget import Budget
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

        # Create categories and budgets for both users
        category1 = Category(user_id=user1.id, name="User1 Category", type=CategoryType.EXPENSE)
        category2 = Category(user_id=user2.id, name="User2 Category", type=CategoryType.EXPENSE)
        db_session.add_all([category1, category2])
        db_session.commit()
        db_session.refresh(category1)
        db_session.refresh(category2)

        budget1 = Budget(
            user_id=user1.id,
            category_id=category1.id,
            name="User1 Budget",
            amount=Decimal("500.00"),
            period=BudgetPeriod.MONTHLY,
            start_date=date(2024, 1, 1)
        )
        budget2 = Budget(
            user_id=user2.id,
            category_id=category2.id,
            name="User2 Budget",
            amount=Decimal("300.00"),
            period=BudgetPeriod.MONTHLY,
            start_date=date(2024, 1, 1)
        )
        db_session.add_all([budget1, budget2])
        db_session.commit()

        # Login as user1
        login_response = client.post(
            "/api/v1/auth/login",
            data={"username": user1.email, "password": "password123"}
        )
        user1_token = login_response.json()["access_token"]
        user1_headers = {"Authorization": f"Bearer {user1_token}"}

        # Get budgets for user1
        response = client.get("/api/v1/budgets", headers=user1_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "User1 Budget"

    def test_get_budget_with_progress(self, client, auth_headers, test_user, db_session):
        """Test retrieving budget with spending progress."""
        from app.models.category import Category
        from app.models.budget import Budget
        from app.models.account import Account, AccountType
        from app.models.transaction import Transaction, TransactionType
        from datetime import date

        # Create account
        account = Account(
            user_id=test_user.id,
            name="Checking",
            type=AccountType.CHECKING,
            currency="USD"
        )
        db_session.add(account)
        db_session.commit()
        db_session.refresh(account)

        # Create category
        category = Category(
            user_id=test_user.id,
            name="Groceries",
            type=CategoryType.EXPENSE
        )
        db_session.add(category)
        db_session.commit()
        db_session.refresh(category)

        # Create budget for January
        budget = Budget(
            user_id=test_user.id,
            category_id=category.id,
            name="Grocery Budget",
            amount=Decimal("500.00"),
            period=BudgetPeriod.MONTHLY,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
        db_session.add(budget)
        db_session.commit()
        db_session.refresh(budget)

        # Create transactions within budget period
        transaction1 = Transaction(
            user_id=test_user.id,
            account_id=account.id,
            category_id=category.id,
            type=TransactionType.DEBIT,
            amount=Decimal("150.00"),
            date=date(2024, 1, 10)
        )
        transaction2 = Transaction(
            user_id=test_user.id,
            account_id=account.id,
            category_id=category.id,
            type=TransactionType.DEBIT,
            amount=Decimal("100.00"),
            date=date(2024, 1, 20)
        )
        db_session.add_all([transaction1, transaction2])
        db_session.commit()

        response = client.get(f"/api/v1/budgets/{budget.id}/progress", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert Decimal(data["spent"]) == Decimal("250.00")
        assert Decimal(data["remaining"]) == Decimal("250.00")
        assert Decimal(data["percentage"]) == Decimal("50.0")
        assert data["is_over_budget"] is False
