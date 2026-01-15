import pytest
from datetime import datetime
from app.services.payee_service import PayeeService
from app.models.payee import Payee
from app.models.user import User
from app.models.category import Category
from app.schemas.payee import PayeeCreate, PayeeUpdate


class TestPayeeService:
    """Test suite for PayeeService."""

    def test_get_or_create_new_payee(self, db_session, test_user):
        """Test creating a new payee."""
        service = PayeeService(db_session)

        payee = service.get_or_create(
            user_id=test_user.id,
            canonical_name="Amazon"
        )

        assert payee.id is not None
        assert payee.user_id == test_user.id
        assert payee.canonical_name == "Amazon"
        assert payee.transaction_count == 0
        assert payee.last_used_at is None

    def test_get_or_create_existing_payee(self, db_session, test_user):
        """Test retrieving existing payee."""
        service = PayeeService(db_session)

        # Create first payee
        payee1 = service.get_or_create(
            user_id=test_user.id,
            canonical_name="Starbucks"
        )

        # Try to create again - should return same payee
        payee2 = service.get_or_create(
            user_id=test_user.id,
            canonical_name="Starbucks"
        )

        assert payee1.id == payee2.id
        assert payee2.canonical_name == "Starbucks"

        # Verify only one payee exists
        all_payees = db_session.query(Payee).filter(
            Payee.user_id == test_user.id
        ).all()
        assert len(all_payees) == 1

    def test_get_or_create_with_normalization(self, db_session, test_user):
        """Test that normalization creates same payee for similar names."""
        service = PayeeService(db_session)

        # Create payees with variations that should normalize to same name
        payee1 = service.get_or_create(
            user_id=test_user.id,
            canonical_name="STARBUCKS #1234"
        )
        payee2 = service.get_or_create(
            user_id=test_user.id,
            canonical_name="Starbucks #5678"
        )

        # Should be the same payee (normalization removes store numbers)
        assert payee1.id == payee2.id

    def test_normalize_payee_name_removes_store_numbers(self, db_session):
        """Test normalization removes store numbers."""
        service = PayeeService(db_session)

        assert service._normalize_payee_name("STARBUCKS #1234") == "Starbucks"
        assert service._normalize_payee_name("TARGET STORE #0123") == "Target"
        assert service._normalize_payee_name("WAL-MART #1234") == "Wal-Mart"

    def test_normalize_payee_name_removes_prefixes(self, db_session):
        """Test normalization removes payment processor prefixes."""
        service = PayeeService(db_session)

        assert service._normalize_payee_name("SQ *COFFEE SHOP") == "Coffee Shop"
        assert service._normalize_payee_name("TST* RESTAURANT") == "Restaurant"
        assert service._normalize_payee_name("PAYPAL *ONLINE STORE") == "Online Store"
        assert service._normalize_payee_name("DEBIT CARD PURCHASE - AMAZON") == "Amazon"

    def test_normalize_payee_name_removes_dates(self, db_session):
        """Test normalization removes dates."""
        service = PayeeService(db_session)

        assert service._normalize_payee_name("AMAZON 8/18") == "Amazon"
        assert service._normalize_payee_name("WALMART 12/25") == "Walmart"

    def test_normalize_payee_name_removes_long_numbers(self, db_session):
        """Test normalization removes transaction IDs."""
        service = PayeeService(db_session)

        assert service._normalize_payee_name("XX7800 AMAZON INC") == "Amazon"
        assert service._normalize_payee_name("12345678 WALMART") == "Walmart"

    def test_normalize_payee_name_removes_company_suffixes(self, db_session):
        """Test normalization removes company suffixes."""
        service = PayeeService(db_session)

        assert service._normalize_payee_name("AMAZON INC") == "Amazon"
        assert service._normalize_payee_name("MICROSOFT CORP") == "Microsoft"
        assert service._normalize_payee_name("WALMART LLC") == "Walmart"

    def test_normalize_payee_name_title_case(self, db_session):
        """Test normalization applies title case."""
        service = PayeeService(db_session)

        assert service._normalize_payee_name("amazon") == "Amazon"
        assert service._normalize_payee_name("STARBUCKS") == "Starbucks"
        assert service._normalize_payee_name("whole foods") == "Whole Foods"

    def test_normalize_payee_name_handles_empty(self, db_session):
        """Test normalization handles empty strings."""
        service = PayeeService(db_session)

        assert service._normalize_payee_name("") == ""
        assert service._normalize_payee_name("   ") == ""

    def test_increment_usage(self, db_session, test_user):
        """Test incrementing payee usage statistics."""
        service = PayeeService(db_session)

        payee = service.get_or_create(
            user_id=test_user.id,
            canonical_name="Target"
        )

        assert payee.transaction_count == 0
        assert payee.last_used_at is None

        # Increment usage
        service.increment_usage(payee.id)

        # Refresh from DB
        db_session.refresh(payee)

        assert payee.transaction_count == 1
        assert payee.last_used_at is not None

        # Increment again
        service.increment_usage(payee.id)
        db_session.refresh(payee)

        assert payee.transaction_count == 2

    def test_search_payees_exact_match(self, db_session, test_user):
        """Test search prioritizes exact matches."""
        service = PayeeService(db_session)

        # Create multiple payees
        service.get_or_create(test_user.id, "Amazon")
        service.get_or_create(test_user.id, "Amazon Prime")
        service.get_or_create(test_user.id, "Other Amazon Store")

        results = service.search_payees(test_user.id, "Amazon", limit=10)

        # Exact match should be first
        assert len(results) == 3
        assert results[0].canonical_name == "Amazon"

    def test_search_payees_starts_with(self, db_session, test_user):
        """Test search prioritizes starts-with matches."""
        service = PayeeService(db_session)

        # Create payees
        payee1 = service.get_or_create(test_user.id, "Star Coffee")
        payee2 = service.get_or_create(test_user.id, "Starbucks")
        payee3 = service.get_or_create(test_user.id, "Five Star Restaurant")

        # Increment usage for the one that doesn't start with "Star"
        service.increment_usage(payee3.id)
        service.increment_usage(payee3.id)

        results = service.search_payees(test_user.id, "Star", limit=10)

        # Even though "Five Star Restaurant" has more usage,
        # "Star Coffee" and "Starbucks" should come first (starts with)
        assert len(results) == 3
        starts_with_results = [r.canonical_name for r in results[:2]]
        assert "Star Coffee" in starts_with_results
        assert "Starbucks" in starts_with_results

    def test_search_payees_by_usage_frequency(self, db_session, test_user):
        """Test search ranks by usage frequency."""
        service = PayeeService(db_session)

        payee1 = service.get_or_create(test_user.id, "Amazon")
        payee2 = service.get_or_create(test_user.id, "Amazon Prime")

        # Make payee2 more frequently used
        service.increment_usage(payee2.id)
        service.increment_usage(payee2.id)
        service.increment_usage(payee2.id)
        service.increment_usage(payee1.id)

        results = service.search_payees(test_user.id, "Amaz", limit=10)

        # Within same match type (starts with), higher usage should rank first
        assert len(results) == 2
        # Both start with "Amaz", so usage should determine order
        assert results[0].transaction_count > results[1].transaction_count

    def test_search_payees_case_insensitive(self, db_session, test_user):
        """Test search is case-insensitive."""
        service = PayeeService(db_session)

        service.get_or_create(test_user.id, "Amazon")

        results = service.search_payees(test_user.id, "amazon", limit=10)
        assert len(results) == 1
        assert results[0].canonical_name == "Amazon"

        results = service.search_payees(test_user.id, "AMAZON", limit=10)
        assert len(results) == 1

    def test_search_payees_limit(self, db_session, test_user):
        """Test search respects limit parameter."""
        service = PayeeService(db_session)

        # Create many payees
        for i in range(20):
            service.get_or_create(test_user.id, f"Store {i}")

        results = service.search_payees(test_user.id, "Store", limit=5)
        assert len(results) == 5

    def test_search_payees_user_isolation(self, db_session, test_user):
        """Test search only returns payees for the specified user."""
        service = PayeeService(db_session)

        # Create another user
        other_user = User(
            email="other@example.com",
            hashed_password="hashedpw",
            is_active=True
        )
        db_session.add(other_user)
        db_session.commit()

        # Create payees for both users
        service.get_or_create(test_user.id, "Amazon")
        service.get_or_create(other_user.id, "Amazon")

        results = service.search_payees(test_user.id, "Amazon")

        assert len(results) == 1
        assert results[0].user_id == test_user.id

    def test_update_default_category(self, db_session, test_user, test_category):
        """Test updating payee's default category."""
        service = PayeeService(db_session)

        payee = service.get_or_create(test_user.id, "Grocery Store")
        assert payee.default_category_id is None

        service.update_default_category(payee.id, test_category.id)
        db_session.refresh(payee)

        assert payee.default_category_id == test_category.id

    def test_get_by_id(self, db_session, test_user):
        """Test getting payee by ID."""
        service = PayeeService(db_session)

        payee = service.get_or_create(test_user.id, "Target")
        found = service.get_by_id(payee.id, test_user.id)

        assert found is not None
        assert found.id == payee.id
        assert found.canonical_name == "Target"

    def test_get_by_id_wrong_user(self, db_session, test_user):
        """Test get_by_id enforces user ownership."""
        service = PayeeService(db_session)

        # Create another user
        other_user = User(
            email="other@example.com",
            hashed_password="hashedpw",
            is_active=True
        )
        db_session.add(other_user)
        db_session.commit()

        payee = service.get_or_create(other_user.id, "Target")

        # Try to get with wrong user_id
        found = service.get_by_id(payee.id, test_user.id)
        assert found is None

    def test_get_all(self, db_session, test_user):
        """Test getting all payees for a user."""
        service = PayeeService(db_session)

        # Create multiple payees
        service.get_or_create(test_user.id, "Amazon")
        service.get_or_create(test_user.id, "Target")
        service.get_or_create(test_user.id, "Walmart")

        all_payees = service.get_all(test_user.id)

        assert len(all_payees) == 3
        payee_names = [p.canonical_name for p in all_payees]
        assert "Amazon" in payee_names
        assert "Target" in payee_names
        assert "Walmart" in payee_names

    def test_update(self, db_session, test_user):
        """Test updating payee metadata."""
        service = PayeeService(db_session)

        payee = service.get_or_create(test_user.id, "Coffee Shop")

        update_data = PayeeUpdate(
            payee_type="restaurant",
            notes="My favorite coffee shop"
        )

        updated = service.update(payee.id, test_user.id, update_data)

        assert updated is not None
        assert updated.payee_type == "restaurant"
        assert updated.notes == "My favorite coffee shop"
        # Canonical name should not change
        assert updated.canonical_name == "Coffee Shop"

    def test_delete(self, db_session, test_user):
        """Test deleting a payee."""
        service = PayeeService(db_session)

        payee = service.get_or_create(test_user.id, "Old Store")

        result = service.delete(payee.id, test_user.id)
        assert result is True

        # Verify deleted
        found = service.get_by_id(payee.id, test_user.id)
        assert found is None

    def test_create_with_default_category(self, db_session, test_user, test_category):
        """Test creating payee with default category."""
        service = PayeeService(db_session)

        payee = service.get_or_create(
            user_id=test_user.id,
            canonical_name="Grocery Store",
            default_category_id=test_category.id
        )

        assert payee.default_category_id == test_category.id


@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    user = User(
        email="test@example.com",
        hashed_password="hashedpassword",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


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
