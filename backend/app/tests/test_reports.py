import pytest
from decimal import Decimal
from datetime import date
from dateutil.relativedelta import relativedelta


class TestReportsAPI:
    """Test reports and dashboard API endpoints."""

    def test_dashboard_summary(self, client, auth_headers, test_user, db_session):
        """Test getting complete dashboard summary."""
        from app.models.account import Account, AccountType
        from app.models.category import Category, CategoryType
        from app.models.transaction import Transaction, TransactionType
        from app.models.budget import Budget, BudgetPeriod

        # Create accounts
        checking = Account(
            user_id=test_user.id,
            name="Checking",
            type=AccountType.CHECKING,
            currency="USD",
            current_balance=Decimal("2000.00")
        )
        savings = Account(
            user_id=test_user.id,
            name="Savings",
            type=AccountType.SAVINGS,
            currency="USD",
            current_balance=Decimal("5000.00")
        )
        credit_card = Account(
            user_id=test_user.id,
            name="Credit Card",
            type=AccountType.CREDIT_CARD,
            currency="USD",
            current_balance=Decimal("-500.00")
        )
        db_session.add_all([checking, savings, credit_card])
        db_session.commit()
        db_session.refresh(checking)

        # Create categories
        income_cat = Category(
            user_id=test_user.id,
            name="Salary",
            type=CategoryType.INCOME
        )
        expense_cat = Category(
            user_id=test_user.id,
            name="Groceries",
            type=CategoryType.EXPENSE
        )
        db_session.add_all([income_cat, expense_cat])
        db_session.commit()
        db_session.refresh(income_cat)
        db_session.refresh(expense_cat)

        # Create transactions for current month
        today = date.today()
        month_start = date(today.year, today.month, 1)

        income_tx = Transaction(
            user_id=test_user.id,
            account_id=checking.id,
            category_id=income_cat.id,
            type=TransactionType.CREDIT,
            amount=Decimal("3000.00"),
            date=month_start
        )
        expense_tx = Transaction(
            user_id=test_user.id,
            account_id=checking.id,
            category_id=expense_cat.id,
            type=TransactionType.DEBIT,
            amount=Decimal("500.00"),
            date=month_start
        )
        db_session.add_all([income_tx, expense_tx])
        db_session.commit()

        # Create a budget
        budget = Budget(
            user_id=test_user.id,
            category_id=expense_cat.id,
            name="Grocery Budget",
            amount=Decimal("600.00"),
            period=BudgetPeriod.MONTHLY,
            start_date=month_start
        )
        db_session.add(budget)
        db_session.commit()

        response = client.get("/api/v1/reports/dashboard", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Check account summary
        assert "account_summary" in data
        assert Decimal(data["account_summary"]["total_assets"]) == Decimal("7000.00")
        assert Decimal(data["account_summary"]["total_liabilities"]) == Decimal("500.00")
        assert Decimal(data["account_summary"]["net_worth"]) == Decimal("6500.00")

        # Check income vs expenses
        assert "income_vs_expenses" in data
        assert Decimal(data["income_vs_expenses"]["total_income"]) == Decimal("3000.00")
        assert Decimal(data["income_vs_expenses"]["total_expenses"]) == Decimal("500.00")
        assert Decimal(data["income_vs_expenses"]["net"]) == Decimal("2500.00")

        # Check budget status
        assert "budget_status" in data
        assert len(data["budget_status"]) == 1
        assert data["budget_status"][0]["budget_name"] == "Grocery Budget"
        assert Decimal(data["budget_status"][0]["spent"]) == Decimal("500.00")
        assert Decimal(data["budget_status"][0]["remaining"]) == Decimal("100.00")

        # Check top spending categories
        assert "top_spending_categories" in data
        assert len(data["top_spending_categories"]) == 1
        assert data["top_spending_categories"][0]["category_name"] == "Groceries"

    def test_dashboard_summary_with_date_range(self, client, auth_headers, test_user, db_session):
        """Test dashboard summary with custom date range."""
        from app.models.account import Account, AccountType
        from app.models.category import Category, CategoryType
        from app.models.transaction import Transaction, TransactionType

        # Create account and category
        checking = Account(
            user_id=test_user.id,
            name="Checking",
            type=AccountType.CHECKING,
            currency="USD",
            current_balance=Decimal("1000.00")
        )
        db_session.add(checking)
        db_session.commit()
        db_session.refresh(checking)

        expense_cat = Category(
            user_id=test_user.id,
            name="Food",
            type=CategoryType.EXPENSE
        )
        db_session.add(expense_cat)
        db_session.commit()
        db_session.refresh(expense_cat)

        # Create transactions in different months
        jan_tx = Transaction(
            user_id=test_user.id,
            account_id=checking.id,
            category_id=expense_cat.id,
            type=TransactionType.DEBIT,
            amount=Decimal("100.00"),
            date=date(2024, 1, 15)
        )
        feb_tx = Transaction(
            user_id=test_user.id,
            account_id=checking.id,
            category_id=expense_cat.id,
            type=TransactionType.DEBIT,
            amount=Decimal("200.00"),
            date=date(2024, 2, 15)
        )
        db_session.add_all([jan_tx, feb_tx])
        db_session.commit()

        # Query for January only
        response = client.get(
            "/api/v1/reports/dashboard?start_date=2024-01-01&end_date=2024-01-31",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert Decimal(data["income_vs_expenses"]["total_expenses"]) == Decimal("100.00")

    def test_spending_by_category(self, client, auth_headers, test_user, db_session):
        """Test spending by category report."""
        from app.models.account import Account, AccountType
        from app.models.category import Category, CategoryType
        from app.models.transaction import Transaction, TransactionType

        # Create account
        checking = Account(
            user_id=test_user.id,
            name="Checking",
            type=AccountType.CHECKING,
            currency="USD"
        )
        db_session.add(checking)
        db_session.commit()
        db_session.refresh(checking)

        # Create categories
        groceries = Category(
            user_id=test_user.id,
            name="Groceries",
            type=CategoryType.EXPENSE
        )
        dining = Category(
            user_id=test_user.id,
            name="Dining",
            type=CategoryType.EXPENSE
        )
        db_session.add_all([groceries, dining])
        db_session.commit()
        db_session.refresh(groceries)
        db_session.refresh(dining)

        # Create transactions
        today = date.today()
        month_start = date(today.year, today.month, 1)

        tx1 = Transaction(
            user_id=test_user.id,
            account_id=checking.id,
            category_id=groceries.id,
            type=TransactionType.DEBIT,
            amount=Decimal("300.00"),
            date=month_start
        )
        tx2 = Transaction(
            user_id=test_user.id,
            account_id=checking.id,
            category_id=groceries.id,
            type=TransactionType.DEBIT,
            amount=Decimal("200.00"),
            date=month_start
        )
        tx3 = Transaction(
            user_id=test_user.id,
            account_id=checking.id,
            category_id=dining.id,
            type=TransactionType.DEBIT,
            amount=Decimal("150.00"),
            date=month_start
        )
        db_session.add_all([tx1, tx2, tx3])
        db_session.commit()

        response = client.get("/api/v1/reports/spending-by-category", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert Decimal(data["total_spending"]) == Decimal("650.00")
        assert len(data["categories"]) == 2

        # Check categories are sorted by amount (descending)
        assert data["categories"][0]["category_name"] == "Groceries"
        assert Decimal(data["categories"][0]["amount"]) == Decimal("500.00")
        assert Decimal(data["categories"][0]["percentage"]).quantize(Decimal("0.01")) == Decimal("76.92")
        assert data["categories"][0]["transaction_count"] == 2

        assert data["categories"][1]["category_name"] == "Dining"
        assert Decimal(data["categories"][1]["amount"]) == Decimal("150.00")

    def test_spending_by_category_no_transactions(self, client, auth_headers, test_user, db_session):
        """Test spending by category with no transactions."""
        response = client.get("/api/v1/reports/spending-by-category", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert Decimal(data["total_spending"]) == Decimal("0.00")
        assert len(data["categories"]) == 0

    def test_income_vs_expenses(self, client, auth_headers, test_user, db_session):
        """Test income vs expenses report with trends."""
        from app.models.account import Account, AccountType
        from app.models.category import Category, CategoryType
        from app.models.transaction import Transaction, TransactionType

        # Create account
        checking = Account(
            user_id=test_user.id,
            name="Checking",
            type=AccountType.CHECKING,
            currency="USD"
        )
        db_session.add(checking)
        db_session.commit()
        db_session.refresh(checking)

        # Create categories
        income_cat = Category(
            user_id=test_user.id,
            name="Salary",
            type=CategoryType.INCOME
        )
        expense_cat = Category(
            user_id=test_user.id,
            name="Expenses",
            type=CategoryType.EXPENSE
        )
        db_session.add_all([income_cat, expense_cat])
        db_session.commit()
        db_session.refresh(income_cat)
        db_session.refresh(expense_cat)

        # Create transactions over 3 months
        today = date.today()
        for i in range(3):
            month_date = today - relativedelta(months=i)
            month_start = date(month_date.year, month_date.month, 1)

            income_tx = Transaction(
                user_id=test_user.id,
                account_id=checking.id,
                category_id=income_cat.id,
                type=TransactionType.CREDIT,
                amount=Decimal("3000.00"),
                date=month_start
            )
            expense_tx = Transaction(
                user_id=test_user.id,
                account_id=checking.id,
                category_id=expense_cat.id,
                type=TransactionType.DEBIT,
                amount=Decimal("2000.00"),
                date=month_start
            )
            db_session.add_all([income_tx, expense_tx])

        db_session.commit()

        response = client.get("/api/v1/reports/income-vs-expenses?months=3", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Check current period totals
        assert Decimal(data["current_period"]["total_income"]) == Decimal("9000.00")
        assert Decimal(data["current_period"]["total_expenses"]) == Decimal("6000.00")
        assert Decimal(data["current_period"]["net"]) == Decimal("3000.00")
        assert Decimal(data["current_period"]["savings_rate"]).quantize(Decimal("0.01")) == Decimal("33.33")

        # Check monthly trends
        assert len(data["monthly_trends"]) == 3
        for trend in data["monthly_trends"]:
            assert Decimal(trend["income"]) == Decimal("3000.00")
            assert Decimal(trend["expenses"]) == Decimal("2000.00")
            assert Decimal(trend["net"]) == Decimal("1000.00")

    def test_income_vs_expenses_no_income(self, client, auth_headers, test_user, db_session):
        """Test income vs expenses with no income (should handle division by zero)."""
        from app.models.account import Account, AccountType
        from app.models.category import Category, CategoryType
        from app.models.transaction import Transaction, TransactionType

        # Create account and category
        checking = Account(
            user_id=test_user.id,
            name="Checking",
            type=AccountType.CHECKING,
            currency="USD"
        )
        db_session.add(checking)
        db_session.commit()
        db_session.refresh(checking)

        expense_cat = Category(
            user_id=test_user.id,
            name="Expenses",
            type=CategoryType.EXPENSE
        )
        db_session.add(expense_cat)
        db_session.commit()
        db_session.refresh(expense_cat)

        # Create only expense transaction
        tx = Transaction(
            user_id=test_user.id,
            account_id=checking.id,
            category_id=expense_cat.id,
            type=TransactionType.DEBIT,
            amount=Decimal("100.00"),
            date=date.today()
        )
        db_session.add(tx)
        db_session.commit()

        response = client.get("/api/v1/reports/income-vs-expenses?months=1", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert Decimal(data["current_period"]["total_income"]) == Decimal("0.00")
        assert Decimal(data["current_period"]["total_expenses"]) == Decimal("100.00")
        assert Decimal(data["current_period"]["net"]) == Decimal("-100.00")
        assert Decimal(data["current_period"]["savings_rate"]) == Decimal("0.00")

    def test_reports_require_authentication(self, client):
        """Test that all report endpoints require authentication."""
        endpoints = [
            "/api/v1/reports/dashboard",
            "/api/v1/reports/spending-by-category",
            "/api/v1/reports/income-vs-expenses"
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401

    def test_user_can_only_see_own_data(self, client, db_session):
        """Test that users can only see their own data in reports."""
        from app.models.user import User
        from app.models.account import Account, AccountType
        from app.models.category import Category, CategoryType
        from app.models.transaction import Transaction, TransactionType
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

        # Create account and transactions for user1
        account1 = Account(
            user_id=user1.id,
            name="User1 Account",
            type=AccountType.CHECKING,
            currency="USD",
            current_balance=Decimal("1000.00")
        )
        db_session.add(account1)
        db_session.commit()
        db_session.refresh(account1)

        category1 = Category(
            user_id=user1.id,
            name="User1 Category",
            type=CategoryType.EXPENSE
        )
        db_session.add(category1)
        db_session.commit()
        db_session.refresh(category1)

        tx1 = Transaction(
            user_id=user1.id,
            account_id=account1.id,
            category_id=category1.id,
            type=TransactionType.DEBIT,
            amount=Decimal("500.00"),
            date=date.today()
        )
        db_session.add(tx1)
        db_session.commit()

        # Login as user2
        login_response = client.post(
            "/api/v1/auth/login",
            data={"username": user2.email, "password": "password123"}
        )
        user2_token = login_response.json()["access_token"]
        user2_headers = {"Authorization": f"Bearer {user2_token}"}

        # User2 should see no data
        response = client.get("/api/v1/reports/dashboard", headers=user2_headers)
        assert response.status_code == 200
        data = response.json()

        assert Decimal(data["account_summary"]["total_assets"]) == Decimal("0.00")
        assert Decimal(data["income_vs_expenses"]["total_expenses"]) == Decimal("0.00")
        assert len(data["top_spending_categories"]) == 0
