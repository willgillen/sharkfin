import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.payee import Payee
from app.models.category import Category
from app.models.user import User


@pytest.fixture
def test_category(db_session, test_user):
    """Create a test category."""
    category = Category(
        user_id=test_user.id,
        name="Groceries",
        type="expense"
    )
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)
    return category


class TestPayeeAPI:
    """Test suite for Payee API endpoints."""

    def test_create_payee(self, client: TestClient, auth_headers, db_session):
        """Test creating a new payee."""
        response = client.post(
            "/api/v1/payees",
            json={
                "canonical_name": "Amazon",
                "payee_type": "online_retail"
            },
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["canonical_name"] == "Amazon"
        assert data["payee_type"] == "online_retail"
        assert data["transaction_count"] == 0
        assert data["id"] is not None

    def test_create_duplicate_payee_returns_existing(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test creating duplicate payee returns existing one."""
        # Create first payee
        response1 = client.post(
            "/api/v1/payees",
            json={"canonical_name": "Starbucks"},
            headers=auth_headers
        )
        assert response1.status_code == 200
        payee1_id = response1.json()["id"]

        # Try to create same payee again
        response2 = client.post(
            "/api/v1/payees",
            json={"canonical_name": "Starbucks"},
            headers=auth_headers
        )
        assert response2.status_code == 200
        payee2_id = response2.json()["id"]

        # Should return the same payee
        assert payee1_id == payee2_id

    def test_get_payees(self, client: TestClient, auth_headers, db_session):
        """Test getting all payees."""
        # Create multiple payees
        client.post(
            "/api/v1/payees",
            json={"canonical_name": "Amazon"},
            headers=auth_headers
        )
        client.post(
            "/api/v1/payees",
            json={"canonical_name": "Target"},
            headers=auth_headers
        )
        client.post(
            "/api/v1/payees",
            json={"canonical_name": "Walmart"},
            headers=auth_headers
        )

        response = client.get("/api/v1/payees", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()

        assert len(data) == 3
        payee_names = [p["canonical_name"] for p in data]
        assert "Amazon" in payee_names
        assert "Target" in payee_names
        assert "Walmart" in payee_names

    def test_get_payees_with_search(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test searching payees."""
        # Create payees
        client.post(
            "/api/v1/payees",
            json={"canonical_name": "Amazon"},
            headers=auth_headers
        )
        client.post(
            "/api/v1/payees",
            json={"canonical_name": "Amazon Prime"},
            headers=auth_headers
        )
        client.post(
            "/api/v1/payees",
            json={"canonical_name": "Target"},
            headers=auth_headers
        )

        response = client.get(
            "/api/v1/payees?q=Amazon",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()

        assert len(data) == 2
        payee_names = [p["canonical_name"] for p in data]
        assert "Amazon" in payee_names
        assert "Amazon Prime" in payee_names
        assert "Target" not in payee_names

    def test_get_payees_pagination(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test pagination works correctly."""
        # Create 15 payees
        for i in range(15):
            client.post(
                "/api/v1/payees",
                json={"canonical_name": f"Store {i}"},
                headers=auth_headers
            )

        # Get first 10
        response = client.get(
            "/api/v1/payees?skip=0&limit=10",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert len(response.json()) == 10

        # Get next 5
        response = client.get(
            "/api/v1/payees?skip=10&limit=10",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert len(response.json()) == 5

    def test_autocomplete_payees(
        self, client: TestClient, auth_headers, test_category, db_session
    ):
        """Test payee autocomplete endpoint."""
        # Create payees with different usage
        amazon_response = client.post(
            "/api/v1/payees",
            json={
                "canonical_name": "Amazon",
                "default_category_id": test_category.id
            },
            headers=auth_headers
        )
        amazon_id = amazon_response.json()["id"]

        client.post(
            "/api/v1/payees",
            json={"canonical_name": "Amazon Prime"},
            headers=auth_headers
        )
        client.post(
            "/api/v1/payees",
            json={"canonical_name": "Target"},
            headers=auth_headers
        )

        # Simulate usage by incrementing transaction count
        from app.services.payee_service import PayeeService
        service = PayeeService(db_session)
        service.increment_usage(amazon_id)
        service.increment_usage(amazon_id)

        # Test autocomplete
        response = client.get(
            "/api/v1/payees/autocomplete?q=Amaz",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()

        assert len(data) == 2
        # Amazon should be first (higher usage)
        assert data[0]["canonical_name"] == "Amazon"
        assert data[0]["default_category_name"] == test_category.name
        assert data[0]["transaction_count"] == 2

    def test_autocomplete_requires_query(
        self, client: TestClient, auth_headers
    ):
        """Test autocomplete requires query parameter."""
        response = client.get(
            "/api/v1/payees/autocomplete",
            headers=auth_headers
        )
        assert response.status_code == 422  # Validation error

    def test_get_payee_by_id(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test getting a specific payee."""
        # Create payee
        create_response = client.post(
            "/api/v1/payees",
            json={"canonical_name": "Starbucks", "payee_type": "restaurant"},
            headers=auth_headers
        )
        payee_id = create_response.json()["id"]

        # Get payee
        response = client.get(
            f"/api/v1/payees/{payee_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == payee_id
        assert data["canonical_name"] == "Starbucks"
        assert data["payee_type"] == "restaurant"

    def test_get_payee_not_found(
        self, client: TestClient, auth_headers
    ):
        """Test getting non-existent payee."""
        response = client.get(
            "/api/v1/payees/99999",
            headers=auth_headers
        )
        assert response.status_code == 404

    def test_update_payee(
        self, client: TestClient, auth_headers, test_category, db_session
    ):
        """Test updating payee metadata."""
        # Create payee
        create_response = client.post(
            "/api/v1/payees",
            json={"canonical_name": "Coffee Shop"},
            headers=auth_headers
        )
        payee_id = create_response.json()["id"]

        # Update payee
        response = client.put(
            f"/api/v1/payees/{payee_id}",
            json={
                "payee_type": "restaurant",
                "default_category_id": test_category.id,
                "notes": "My favorite coffee shop"
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == payee_id
        assert data["canonical_name"] == "Coffee Shop"  # Unchanged
        assert data["payee_type"] == "restaurant"
        assert data["default_category_id"] == test_category.id
        assert data["notes"] == "My favorite coffee shop"

    def test_update_payee_not_found(
        self, client: TestClient, auth_headers
    ):
        """Test updating non-existent payee."""
        response = client.put(
            "/api/v1/payees/99999",
            json={"payee_type": "restaurant"},
            headers=auth_headers
        )
        assert response.status_code == 404

    def test_delete_payee(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test deleting a payee."""
        # Create payee
        create_response = client.post(
            "/api/v1/payees",
            json={"canonical_name": "Old Store"},
            headers=auth_headers
        )
        payee_id = create_response.json()["id"]

        # Delete payee
        response = client.delete(
            f"/api/v1/payees/{payee_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Payee deleted successfully"

        # Verify deletion
        get_response = client.get(
            f"/api/v1/payees/{payee_id}",
            headers=auth_headers
        )
        assert get_response.status_code == 404

    def test_delete_payee_not_found(
        self, client: TestClient, auth_headers
    ):
        """Test deleting non-existent payee."""
        response = client.delete(
            "/api/v1/payees/99999",
            headers=auth_headers
        )
        assert response.status_code == 404

    def test_payee_requires_auth(self, client: TestClient):
        """Test that payee endpoints require authentication."""
        # Try to access without auth
        response = client.get("/api/v1/payees")
        assert response.status_code == 401

        response = client.post(
            "/api/v1/payees",
            json={"canonical_name": "Test"}
        )
        assert response.status_code == 401

    def test_get_payee_transactions(
        self, client: TestClient, auth_headers, test_category, db_session
    ):
        """Test getting transactions for a payee."""
        from app.models.transaction import Transaction, TransactionType
        from app.models.account import Account
        from app.models.user import User
        from datetime import date

        # Get the test user
        user = db_session.query(User).first()

        # Create an account
        account = Account(
            user_id=user.id,
            name="Test Checking",
            type="checking",
            current_balance=1000.00,
            currency="USD"
        )
        db_session.add(account)
        db_session.commit()
        db_session.refresh(account)

        # Create a payee
        create_response = client.post(
            "/api/v1/payees",
            json={
                "canonical_name": "Test Store",
                "default_category_id": test_category.id
            },
            headers=auth_headers
        )
        payee_id = create_response.json()["id"]

        # Create transactions for this payee
        for i in range(5):
            txn = Transaction(
                user_id=user.id,
                account_id=account.id,
                payee_id=payee_id,
                category_id=test_category.id,
                type=TransactionType.DEBIT,
                amount=25.00 + i,
                date=date(2026, 1, 15 - i),
                description=f"Purchase {i + 1}"
            )
            db_session.add(txn)
        db_session.commit()

        # Get transactions
        response = client.get(
            f"/api/v1/payees/{payee_id}/transactions?limit=10",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()

        assert len(data) == 5
        # Should be sorted by date descending
        assert data[0]["date"] == "2026-01-15"
        assert data[0]["account_name"] == "Test Checking"
        assert data[0]["category_name"] == test_category.name
        assert data[0]["type"] == "debit"

    def test_get_payee_transactions_empty(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test getting transactions for payee with no transactions."""
        # Create a payee
        create_response = client.post(
            "/api/v1/payees",
            json={"canonical_name": "Empty Payee"},
            headers=auth_headers
        )
        payee_id = create_response.json()["id"]

        # Get transactions
        response = client.get(
            f"/api/v1/payees/{payee_id}/transactions",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()

        assert len(data) == 0

    def test_get_payee_transactions_not_found(
        self, client: TestClient, auth_headers
    ):
        """Test getting transactions for non-existent payee."""
        response = client.get(
            "/api/v1/payees/99999/transactions",
            headers=auth_headers
        )
        assert response.status_code == 404

    def test_get_payee_stats(
        self, client: TestClient, auth_headers, test_category, db_session
    ):
        """Test getting spending stats for a payee."""
        from app.models.transaction import Transaction, TransactionType
        from app.models.account import Account
        from app.models.user import User
        from datetime import date
        from decimal import Decimal

        # Get the test user
        user = db_session.query(User).first()

        # Create an account
        account = Account(
            user_id=user.id,
            name="Test Checking",
            type="checking",
            current_balance=1000.00,
            currency="USD"
        )
        db_session.add(account)
        db_session.commit()
        db_session.refresh(account)

        # Create a payee
        create_response = client.post(
            "/api/v1/payees",
            json={"canonical_name": "Stats Store"},
            headers=auth_headers
        )
        payee_id = create_response.json()["id"]

        # Create transactions - some this month, some older
        today = date.today()
        this_month_start = date(today.year, today.month, 1)
        this_year_start = date(today.year, 1, 1)

        # Transaction this month
        txn1 = Transaction(
            user_id=user.id,
            account_id=account.id,
            payee_id=payee_id,
            type=TransactionType.DEBIT,
            amount=Decimal("50.00"),
            date=this_month_start,
            description="This month purchase"
        )
        db_session.add(txn1)

        # Transaction this year but last month
        if today.month > 1:
            old_date = date(today.year, today.month - 1, 15)
        else:
            old_date = date(today.year - 1, 12, 15)

        txn2 = Transaction(
            user_id=user.id,
            account_id=account.id,
            payee_id=payee_id,
            type=TransactionType.DEBIT,
            amount=Decimal("100.00"),
            date=old_date,
            description="Last month purchase"
        )
        db_session.add(txn2)

        # A credit transaction
        txn3 = Transaction(
            user_id=user.id,
            account_id=account.id,
            payee_id=payee_id,
            type=TransactionType.CREDIT,
            amount=Decimal("25.00"),
            date=this_month_start,
            description="Refund"
        )
        db_session.add(txn3)
        db_session.commit()

        # Get stats
        response = client.get(
            f"/api/v1/payees/{payee_id}/stats",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()

        assert data["transaction_count"] == 3
        assert float(data["total_spent_all_time"]) == 150.00  # 50 + 100
        assert float(data["total_spent_this_month"]) == 50.00  # Only txn1
        assert float(data["total_income_all_time"]) == 25.00  # txn3
        assert data["first_transaction_date"] is not None
        assert data["last_transaction_date"] is not None
        assert data["average_transaction_amount"] is not None

    def test_get_payee_stats_empty(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test getting stats for payee with no transactions."""
        # Create a payee
        create_response = client.post(
            "/api/v1/payees",
            json={"canonical_name": "Empty Stats Payee"},
            headers=auth_headers
        )
        payee_id = create_response.json()["id"]

        # Get stats
        response = client.get(
            f"/api/v1/payees/{payee_id}/stats",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()

        assert data["transaction_count"] == 0
        assert float(data["total_spent_all_time"]) == 0.0
        assert float(data["total_spent_this_month"]) == 0.0
        assert float(data["total_spent_this_year"]) == 0.0
        assert data["first_transaction_date"] is None
        assert data["last_transaction_date"] is None

    def test_get_payee_stats_not_found(
        self, client: TestClient, auth_headers
    ):
        """Test getting stats for non-existent payee."""
        response = client.get(
            "/api/v1/payees/99999/stats",
            headers=auth_headers
        )
        assert response.status_code == 404

    def test_payee_list_includes_category_name(
        self, client: TestClient, auth_headers, test_category, db_session
    ):
        """Test that payee list includes default_category_name (13.1 fix)."""
        # Create a payee with a default category
        create_response = client.post(
            "/api/v1/payees",
            json={
                "canonical_name": "Category Test Payee",
                "default_category_id": test_category.id
            },
            headers=auth_headers
        )
        assert create_response.status_code == 200

        # Get payee list
        response = client.get("/api/v1/payees", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()

        # Find our payee
        payee = next(
            (p for p in data if p["canonical_name"] == "Category Test Payee"),
            None
        )
        assert payee is not None
        assert payee["default_category_id"] == test_category.id
        assert payee["default_category_name"] == test_category.name  # This is the fix!


class TestPayeePatternAPI:
    """Test suite for Payee Pattern Management API endpoints."""

    def test_get_patterns_empty(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test getting patterns for payee with no patterns."""
        # Create a payee
        create_response = client.post(
            "/api/v1/payees",
            json={"canonical_name": "Pattern Test Payee"},
            headers=auth_headers
        )
        payee_id = create_response.json()["id"]

        # Get patterns
        response = client.get(
            f"/api/v1/payees/{payee_id}/patterns",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

    def test_create_pattern(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test creating a new pattern for a payee."""
        # Create a payee
        create_response = client.post(
            "/api/v1/payees",
            json={"canonical_name": "Uber"},
            headers=auth_headers
        )
        payee_id = create_response.json()["id"]

        # Create a pattern
        response = client.post(
            f"/api/v1/payees/{payee_id}/patterns",
            json={
                "pattern_type": "description_contains",
                "pattern_value": "UBER",
                "confidence_score": "0.90"
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()

        assert data["payee_id"] == payee_id
        assert data["pattern_type"] == "description_contains"
        assert data["pattern_value"] == "UBER"
        assert float(data["confidence_score"]) == 0.90
        assert data["source"] == "user_created"
        assert data["match_count"] == 0

    def test_create_pattern_short_value_fails(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test that patterns with short values are rejected for description_contains."""
        # Create a payee
        create_response = client.post(
            "/api/v1/payees",
            json={"canonical_name": "AT&T"},
            headers=auth_headers
        )
        payee_id = create_response.json()["id"]

        # Try to create a pattern with value < 4 chars
        response = client.post(
            f"/api/v1/payees/{payee_id}/patterns",
            json={
                "pattern_type": "description_contains",
                "pattern_value": "AT",
                "confidence_score": "0.80"
            },
            headers=auth_headers
        )
        assert response.status_code == 400
        assert "at least 4 characters" in response.json()["detail"]

    def test_create_pattern_invalid_type_fails(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test that invalid pattern types are rejected."""
        # Create a payee
        create_response = client.post(
            "/api/v1/payees",
            json={"canonical_name": "Test Payee"},
            headers=auth_headers
        )
        payee_id = create_response.json()["id"]

        # Try to create a pattern with invalid type
        response = client.post(
            f"/api/v1/payees/{payee_id}/patterns",
            json={
                "pattern_type": "invalid_type",
                "pattern_value": "TEST",
                "confidence_score": "0.80"
            },
            headers=auth_headers
        )
        assert response.status_code == 400
        assert "Invalid pattern type" in response.json()["detail"]

    def test_create_pattern_payee_not_found(
        self, client: TestClient, auth_headers
    ):
        """Test creating pattern for non-existent payee."""
        response = client.post(
            "/api/v1/payees/99999/patterns",
            json={
                "pattern_type": "description_contains",
                "pattern_value": "TEST",
                "confidence_score": "0.80"
            },
            headers=auth_headers
        )
        assert response.status_code == 404

    def test_get_patterns_after_create(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test listing patterns after creating some."""
        # Create a payee
        create_response = client.post(
            "/api/v1/payees",
            json={"canonical_name": "Starbucks"},
            headers=auth_headers
        )
        payee_id = create_response.json()["id"]

        # Create multiple patterns
        client.post(
            f"/api/v1/payees/{payee_id}/patterns",
            json={
                "pattern_type": "description_contains",
                "pattern_value": "STARBUCKS",
                "confidence_score": "0.95"
            },
            headers=auth_headers
        )
        client.post(
            f"/api/v1/payees/{payee_id}/patterns",
            json={
                "pattern_type": "exact_match",
                "pattern_value": "Starbucks",
                "confidence_score": "0.85"
            },
            headers=auth_headers
        )

        # Get patterns
        response = client.get(
            f"/api/v1/payees/{payee_id}/patterns",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()

        assert len(data) == 2
        # Should be sorted by confidence descending
        assert float(data[0]["confidence_score"]) >= float(data[1]["confidence_score"])

    def test_update_pattern(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test updating a pattern."""
        # Create a payee
        create_response = client.post(
            "/api/v1/payees",
            json={"canonical_name": "Amazon"},
            headers=auth_headers
        )
        payee_id = create_response.json()["id"]

        # Create a pattern
        pattern_response = client.post(
            f"/api/v1/payees/{payee_id}/patterns",
            json={
                "pattern_type": "description_contains",
                "pattern_value": "AMAZON",
                "confidence_score": "0.80"
            },
            headers=auth_headers
        )
        pattern_id = pattern_response.json()["id"]

        # Update the pattern
        response = client.put(
            f"/api/v1/payees/patterns/{pattern_id}",
            json={
                "confidence_score": "0.95"
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == pattern_id
        assert float(data["confidence_score"]) == 0.95
        assert data["pattern_value"] == "AMAZON"  # Unchanged

    def test_update_pattern_not_found(
        self, client: TestClient, auth_headers
    ):
        """Test updating non-existent pattern."""
        response = client.put(
            "/api/v1/payees/patterns/99999",
            json={"confidence_score": "0.90"},
            headers=auth_headers
        )
        assert response.status_code == 404

    def test_delete_pattern(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test deleting a pattern."""
        # Create a payee
        create_response = client.post(
            "/api/v1/payees",
            json={"canonical_name": "Delete Test"},
            headers=auth_headers
        )
        payee_id = create_response.json()["id"]

        # Create a pattern
        pattern_response = client.post(
            f"/api/v1/payees/{payee_id}/patterns",
            json={
                "pattern_type": "description_contains",
                "pattern_value": "DELTEST",
                "confidence_score": "0.80"
            },
            headers=auth_headers
        )
        pattern_id = pattern_response.json()["id"]

        # Delete the pattern
        response = client.delete(
            f"/api/v1/payees/patterns/{pattern_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Pattern deleted successfully"

        # Verify it's gone
        patterns_response = client.get(
            f"/api/v1/payees/{payee_id}/patterns",
            headers=auth_headers
        )
        assert len(patterns_response.json()) == 0

    def test_delete_pattern_not_found(
        self, client: TestClient, auth_headers
    ):
        """Test deleting non-existent pattern."""
        response = client.delete(
            "/api/v1/payees/patterns/99999",
            headers=auth_headers
        )
        assert response.status_code == 404

    def test_test_pattern_contains(
        self, client: TestClient, auth_headers
    ):
        """Test the pattern testing endpoint for description_contains."""
        response = client.post(
            "/api/v1/payees/patterns/test",
            params={
                "pattern_type": "description_contains",
                "pattern_value": "UBER"
            },
            json={"description": "UBER TRIP 12345 SF CA"},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()

        assert data["matches"] is True
        assert data["pattern_type"] == "description_contains"
        assert "Found 'UBER'" in data["match_details"]

    def test_test_pattern_no_match(
        self, client: TestClient, auth_headers
    ):
        """Test the pattern testing endpoint when no match."""
        response = client.post(
            "/api/v1/payees/patterns/test",
            params={
                "pattern_type": "description_contains",
                "pattern_value": "LYFT"
            },
            json={"description": "UBER TRIP 12345 SF CA"},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()

        assert data["matches"] is False

    def test_test_pattern_invalid_type(
        self, client: TestClient, auth_headers
    ):
        """Test pattern testing with invalid pattern type."""
        response = client.post(
            "/api/v1/payees/patterns/test",
            params={
                "pattern_type": "invalid_type",
                "pattern_value": "TEST"
            },
            json={"description": "TEST DESCRIPTION"},
            headers=auth_headers
        )
        assert response.status_code == 400
