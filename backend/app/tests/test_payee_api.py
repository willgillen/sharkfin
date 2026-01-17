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
