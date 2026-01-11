import pytest
from app.models.category import CategoryType


class TestCategoryCRUD:
    """Test CRUD operations for categories."""

    def test_create_category(self, client, auth_headers):
        """Test creating a new category."""
        category_data = {
            "name": "Groceries",
            "type": "expense",
            "color": "#FF5733",
            "icon": "shopping-cart"
        }

        response = client.post(
            "/api/v1/categories",
            json=category_data,
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == category_data["name"]
        assert data["type"] == category_data["type"]
        assert data["color"] == category_data["color"]
        assert data["icon"] == category_data["icon"]
        assert data["parent_id"] is None
        assert "id" in data
        assert "user_id" in data
        assert "created_at" in data

    def test_create_subcategory(self, client, auth_headers, test_user, db_session):
        """Test creating a subcategory with parent_id."""
        from app.models.category import Category

        # Create parent category
        parent = Category(
            user_id=test_user.id,
            name="Food",
            type=CategoryType.EXPENSE,
            color="#FF0000"
        )
        db_session.add(parent)
        db_session.commit()
        db_session.refresh(parent)

        # Create subcategory
        subcategory_data = {
            "name": "Restaurants",
            "type": "expense",
            "parent_id": parent.id,
            "color": "#FF5733"
        }

        response = client.post(
            "/api/v1/categories",
            json=subcategory_data,
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == subcategory_data["name"]
        assert data["parent_id"] == parent.id

    def test_create_category_without_auth(self, client):
        """Test that creating category without authentication fails."""
        category_data = {
            "name": "Groceries",
            "type": "expense"
        }

        response = client.post("/api/v1/categories", json=category_data)
        assert response.status_code == 401

    def test_create_category_invalid_color(self, client, auth_headers):
        """Test creating category with invalid color format."""
        category_data = {
            "name": "Groceries",
            "type": "expense",
            "color": "FF5733"  # Missing # prefix
        }

        response = client.post(
            "/api/v1/categories",
            json=category_data,
            headers=auth_headers
        )

        assert response.status_code == 422

    def test_create_category_invalid_color_length(self, client, auth_headers):
        """Test creating category with invalid color length."""
        category_data = {
            "name": "Groceries",
            "type": "expense",
            "color": "#FF57"  # Too short
        }

        response = client.post(
            "/api/v1/categories",
            json=category_data,
            headers=auth_headers
        )

        assert response.status_code == 422

    def test_get_categories(self, client, auth_headers, test_user, db_session):
        """Test retrieving all categories for a user."""
        from app.models.category import Category

        # Create test categories
        category1 = Category(
            user_id=test_user.id,
            name="Salary",
            type=CategoryType.INCOME,
            color="#00FF00"
        )
        category2 = Category(
            user_id=test_user.id,
            name="Groceries",
            type=CategoryType.EXPENSE,
            color="#FF0000"
        )
        db_session.add_all([category1, category2])
        db_session.commit()

        response = client.get("/api/v1/categories", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "Salary"
        assert data[1]["name"] == "Groceries"

    def test_get_categories_filtered_by_type(self, client, auth_headers, test_user, db_session):
        """Test retrieving categories filtered by type."""
        from app.models.category import Category

        # Create categories of different types
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

        # Get only expense categories
        response = client.get("/api/v1/categories?type=expense", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Groceries"
        assert data[0]["type"] == "expense"

    def test_get_category_by_id(self, client, auth_headers, test_user, db_session):
        """Test retrieving a specific category by ID."""
        from app.models.category import Category

        category = Category(
            user_id=test_user.id,
            name="Groceries",
            type=CategoryType.EXPENSE,
            color="#FF5733"
        )
        db_session.add(category)
        db_session.commit()
        db_session.refresh(category)

        response = client.get(f"/api/v1/categories/{category.id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == category.id
        assert data["name"] == "Groceries"
        assert data["color"] == "#FF5733"

    def test_get_nonexistent_category(self, client, auth_headers):
        """Test retrieving a non-existent category returns 404."""
        response = client.get("/api/v1/categories/99999", headers=auth_headers)
        assert response.status_code == 404

    def test_update_category(self, client, auth_headers, test_user, db_session):
        """Test updating a category."""
        from app.models.category import Category

        category = Category(
            user_id=test_user.id,
            name="Old Name",
            type=CategoryType.EXPENSE,
            color="#FF0000"
        )
        db_session.add(category)
        db_session.commit()
        db_session.refresh(category)

        update_data = {
            "name": "Updated Name",
            "color": "#00FF00"
        }

        response = client.put(
            f"/api/v1/categories/{category.id}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["color"] == "#00FF00"
        assert data["type"] == "expense"  # Unchanged

    def test_delete_category(self, client, auth_headers, test_user, db_session):
        """Test deleting a category."""
        from app.models.category import Category

        category = Category(
            user_id=test_user.id,
            name="To Delete",
            type=CategoryType.EXPENSE
        )
        db_session.add(category)
        db_session.commit()
        db_session.refresh(category)

        response = client.delete(f"/api/v1/categories/{category.id}", headers=auth_headers)

        assert response.status_code == 204

        # Verify it's deleted
        response = client.get(f"/api/v1/categories/{category.id}", headers=auth_headers)
        assert response.status_code == 404

    def test_user_can_only_access_own_categories(self, client, db_session):
        """Test that users can only access their own categories."""
        from app.models.user import User
        from app.models.category import Category
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

        # Create category for user1
        category1 = Category(
            user_id=user1.id,
            name="User1 Category",
            type=CategoryType.EXPENSE
        )
        db_session.add(category1)
        db_session.commit()
        db_session.refresh(category1)

        # Login as user2
        login_response = client.post(
            "/api/v1/auth/login",
            data={"username": user2.email, "password": "password123"}
        )
        user2_token = login_response.json()["access_token"]
        user2_headers = {"Authorization": f"Bearer {user2_token}"}

        # Try to access user1's category as user2
        response = client.get(f"/api/v1/categories/{category1.id}", headers=user2_headers)
        assert response.status_code == 404  # Should not be able to access

    def test_list_categories_only_shows_user_categories(self, client, db_session):
        """Test that listing categories only shows the current user's categories."""
        from app.models.user import User
        from app.models.category import Category
        from app.core.security import get_password_hash

        # Create two users with categories
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

        # Create categories for both users
        category1 = Category(user_id=user1.id, name="User1 Category", type=CategoryType.EXPENSE)
        category2 = Category(user_id=user2.id, name="User2 Category", type=CategoryType.INCOME)
        db_session.add_all([category1, category2])
        db_session.commit()

        # Login as user1
        login_response = client.post(
            "/api/v1/auth/login",
            data={"username": user1.email, "password": "password123"}
        )
        user1_token = login_response.json()["access_token"]
        user1_headers = {"Authorization": f"Bearer {user1_token}"}

        # Get categories for user1
        response = client.get("/api/v1/categories", headers=user1_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "User1 Category"

    def test_delete_parent_category_cascades_to_subcategories(self, client, auth_headers, test_user, db_session):
        """Test that deleting a parent category cascades to subcategories."""
        from app.models.category import Category

        # Create parent and subcategory
        parent = Category(
            user_id=test_user.id,
            name="Parent",
            type=CategoryType.EXPENSE
        )
        db_session.add(parent)
        db_session.commit()
        db_session.refresh(parent)

        subcategory = Category(
            user_id=test_user.id,
            name="Subcategory",
            type=CategoryType.EXPENSE,
            parent_id=parent.id
        )
        db_session.add(subcategory)
        db_session.commit()
        db_session.refresh(subcategory)

        # Store the ID before deletion
        subcategory_id = subcategory.id

        # Delete parent
        response = client.delete(f"/api/v1/categories/{parent.id}", headers=auth_headers)
        assert response.status_code == 204

        # Verify subcategory is also deleted
        response = client.get(f"/api/v1/categories/{subcategory_id}", headers=auth_headers)
        assert response.status_code == 404
