"""
Tests for PayeeExtractionService

Tests intelligent extraction of clean payee names from transaction descriptions
by removing store numbers, payment processor prefixes, transaction IDs, etc.
"""
import pytest
from app.services.payee_extraction_service import PayeeExtractionService
from app.models.payee import Payee
from app.models.user import User
from sqlalchemy.orm import Session


@pytest.fixture
def extraction_service(db_session: Session):
    """Create PayeeExtractionService instance"""
    return PayeeExtractionService(db_session)


@pytest.fixture
def test_user(db_session: Session):
    """Create test user"""
    from app.core.security import get_password_hash
    user = User(
        email="extraction@test.com",
        hashed_password=get_password_hash("testpass123"),
        full_name="Extraction Test User"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


class TestPayeeExtraction:
    """Test payee name extraction from descriptions"""

    def test_extract_square_prefix(self, extraction_service: PayeeExtractionService):
        """Test removing Square payment processor prefix"""
        description = "SQ *COFFEE SHOP"
        extracted, confidence = extraction_service.extract_payee_name(description)

        assert extracted == "Coffee Shop"
        assert confidence > 0.6  # Should have good confidence

    def test_extract_toast_prefix(self, extraction_service: PayeeExtractionService):
        """Test removing Toast payment processor prefix"""
        description = "TST* RESTAURANT ABC"
        extracted, confidence = extraction_service.extract_payee_name(description)

        assert extracted == "Restaurant Abc"
        assert confidence > 0.6

    def test_extract_paypal_prefix(self, extraction_service: PayeeExtractionService):
        """Test removing PayPal prefix"""
        description = "PAYPAL *EBAY"
        extracted, confidence = extraction_service.extract_payee_name(description)

        assert extracted == "Ebay"
        assert confidence > 0.6

    def test_remove_store_number(self, extraction_service: PayeeExtractionService):
        """Test removing store numbers like #1234"""
        description = "WHOLE FOODS MARKET #456"
        extracted, confidence = extraction_service.extract_payee_name(description)

        assert extracted == "Whole Foods Market"
        assert "#456" not in extracted

    def test_remove_store_location(self, extraction_service: PayeeExtractionService):
        """Test removing STORE/LOCATION indicators"""
        description = "WALMART STORE 1234"
        extracted, confidence = extraction_service.extract_payee_name(description)

        assert extracted == "Walmart"
        assert "STORE" not in extracted.upper()
        assert "1234" not in extracted

    def test_remove_transaction_id(self, extraction_service: PayeeExtractionService):
        """Test removing transaction IDs"""
        description = "AMAZON.COM*ABCDEF123456"
        extracted, confidence = extraction_service.extract_payee_name(description)

        assert "Amazon" in extracted
        assert "ABCDEF123456" not in extracted

    def test_remove_url_suffix(self, extraction_service: PayeeExtractionService):
        """Test removing .com, .net suffixes"""
        description = "NETFLIX.COM"
        extracted, confidence = extraction_service.extract_payee_name(description)

        assert extracted == "Netflix"
        assert ".COM" not in extracted.upper()

    def test_remove_www_prefix(self, extraction_service: PayeeExtractionService):
        """Test removing WWW. prefix and .COM suffix"""
        description = "WWW.SPOTIFY.COM"
        extracted, confidence = extraction_service.extract_payee_name(description)

        assert extracted == "Spotify"
        assert "WWW" not in extracted.upper()
        assert ".COM" not in extracted.upper()

    def test_complex_extraction(self, extraction_service: PayeeExtractionService):
        """Test complex case with multiple patterns"""
        description = "SQ *COFFEE SHOP #789"
        extracted, confidence = extraction_service.extract_payee_name(description)

        assert extracted == "Coffee Shop"
        assert "SQ" not in extracted
        assert "#789" not in extracted
        assert confidence > 0.7  # High confidence for multiple matches

    def test_real_world_amazon(self, extraction_service: PayeeExtractionService):
        """Test real-world Amazon transaction"""
        description = "AMAZON.COM*AB3CD4EF5"
        extracted, confidence = extraction_service.extract_payee_name(description)

        assert "Amazon" in extracted
        assert len(extracted) < 15  # Should be cleaned up

    def test_real_world_starbucks(self, extraction_service: PayeeExtractionService):
        """Test real-world Starbucks transaction"""
        description = "STARBUCKS STORE 9876"
        extracted, confidence = extraction_service.extract_payee_name(description)

        assert extracted == "Starbucks"
        assert "9876" not in extracted

    def test_real_world_gas_station(self, extraction_service: PayeeExtractionService):
        """Test real-world gas station transaction"""
        description = "SHELL OIL 78912345"
        extracted, confidence = extraction_service.extract_payee_name(description)

        assert "Shell Oil" in extracted
        assert "78912345" not in extracted

    def test_empty_description(self, extraction_service: PayeeExtractionService):
        """Test handling empty description"""
        extracted, confidence = extraction_service.extract_payee_name("")

        assert extracted == ""
        assert confidence == 0.0

    def test_whitespace_normalization(self, extraction_service: PayeeExtractionService):
        """Test whitespace normalization"""
        description = "  COFFEE   SHOP   "
        extracted, confidence = extraction_service.extract_payee_name(description)

        assert extracted == "Coffee Shop"
        assert "  " not in extracted  # No multiple spaces

    def test_title_case_conversion(self, extraction_service: PayeeExtractionService):
        """Test title case conversion"""
        description = "TARGET STORE 1234"
        extracted, confidence = extraction_service.extract_payee_name(description)

        assert extracted == "Target"  # Title cased

    def test_trailing_punctuation_removal(self, extraction_service: PayeeExtractionService):
        """Test removal of trailing punctuation"""
        description = "COFFEE SHOP..."
        extracted, confidence = extraction_service.extract_payee_name(description)

        assert extracted == "Coffee Shop"
        assert not extracted.endswith(".")


class TestPayeeMatching:
    """Test fuzzy matching to existing Payee entities"""

    def test_exact_match(self, extraction_service: PayeeExtractionService, test_user: User, db_session: Session):
        """Test exact match to existing payee"""
        # Create existing payee
        payee = Payee(
            user_id=test_user.id,
            canonical_name="Starbucks"
        )
        db_session.add(payee)
        db_session.commit()

        # Try to match
        matched = extraction_service.match_to_existing_payee(
            test_user.id,
            "Starbucks"
        )

        assert matched is not None
        assert matched.canonical_name == "Starbucks"

    def test_fuzzy_match_high_similarity(self, extraction_service: PayeeExtractionService, test_user: User, db_session: Session):
        """Test fuzzy match with high similarity"""
        # Create existing payee
        payee = Payee(
            user_id=test_user.id,
            canonical_name="Whole Foods Market"
        )
        db_session.add(payee)
        db_session.commit()

        # Try to match with slight variation - use lower threshold
        matched = extraction_service.match_to_existing_payee(
            test_user.id,
            "Whole Foods",  # Missing "Market"
            threshold=0.75  # Lower threshold for this test
        )

        assert matched is not None
        assert matched.canonical_name == "Whole Foods Market"

    def test_no_match_low_similarity(self, extraction_service: PayeeExtractionService, test_user: User, db_session: Session):
        """Test no match when similarity is too low"""
        # Create existing payee
        payee = Payee(
            user_id=test_user.id,
            canonical_name="Starbucks"
        )
        db_session.add(payee)
        db_session.commit()

        # Try to match with completely different name
        matched = extraction_service.match_to_existing_payee(
            test_user.id,
            "Walmart"
        )

        assert matched is None

    def test_match_case_insensitive(self, extraction_service: PayeeExtractionService, test_user: User, db_session: Session):
        """Test matching is case-insensitive"""
        payee = Payee(
            user_id=test_user.id,
            canonical_name="Amazon"
        )
        db_session.add(payee)
        db_session.commit()

        # Try different cases
        matched_upper = extraction_service.match_to_existing_payee(test_user.id, "AMAZON")
        matched_lower = extraction_service.match_to_existing_payee(test_user.id, "amazon")
        matched_title = extraction_service.match_to_existing_payee(test_user.id, "Amazon")

        assert matched_upper is not None
        assert matched_lower is not None
        assert matched_title is not None

    def test_match_best_among_multiple(self, extraction_service: PayeeExtractionService, test_user: User, db_session: Session):
        """Test matching selects best match when multiple payees exist"""
        # Create multiple similar payees
        payee1 = Payee(user_id=test_user.id, canonical_name="Starbucks")
        payee2 = Payee(user_id=test_user.id, canonical_name="Starbucks Coffee")
        payee3 = Payee(user_id=test_user.id, canonical_name="Walmart")

        db_session.add_all([payee1, payee2, payee3])
        db_session.commit()

        # Should match "Starbucks" (exact match) over "Starbucks Coffee"
        matched = extraction_service.match_to_existing_payee(
            test_user.id,
            "Starbucks"
        )

        assert matched is not None
        assert matched.canonical_name == "Starbucks"

    def test_match_respects_user_boundary(self, extraction_service: PayeeExtractionService, test_user: User, db_session: Session):
        """Test that matching only finds payees for the correct user"""
        # Create another user
        from app.core.security import get_password_hash
        other_user = User(
            email="other@test.com",
            hashed_password=get_password_hash("pass123"),
            full_name="Other User"
        )
        db_session.add(other_user)
        db_session.commit()

        # Create payee for other user
        other_payee = Payee(
            user_id=other_user.id,
            canonical_name="Starbucks"
        )
        db_session.add(other_payee)
        db_session.commit()

        # Should NOT match other user's payee
        matched = extraction_service.match_to_existing_payee(
            test_user.id,
            "Starbucks"
        )

        assert matched is None


class TestCompleteExtractAndMatch:
    """Test complete extraction and matching pipeline"""

    def test_extract_and_match_with_existing(self, extraction_service: PayeeExtractionService, test_user: User, db_session: Session):
        """Test complete pipeline with existing payee"""
        # Create existing payee
        payee = Payee(
            user_id=test_user.id,
            canonical_name="Starbucks"
        )
        db_session.add(payee)
        db_session.commit()

        # Extract and match
        extracted, matched, extract_conf, match_score = extraction_service.extract_and_match(
            test_user.id,
            "STARBUCKS STORE 9876"
        )

        assert extracted == "Starbucks"
        assert matched is not None
        assert matched.canonical_name == "Starbucks"
        assert extract_conf > 0.5
        assert match_score > 0.9  # Very high match

    def test_extract_and_match_without_existing(self, extraction_service: PayeeExtractionService, test_user: User, db_session: Session):
        """Test complete pipeline without existing payee"""
        extracted, matched, extract_conf, match_score = extraction_service.extract_and_match(
            test_user.id,
            "SQ *NEW COFFEE SHOP #123"
        )

        assert extracted == "New Coffee Shop"
        assert matched is None  # No existing payee
        assert extract_conf > 0.6
        assert match_score == 0.0  # No match

    def test_extract_and_match_complex_real_world(self, extraction_service: PayeeExtractionService, test_user: User, db_session: Session):
        """Test with complex real-world scenario"""
        # Create existing payee with clean name
        payee = Payee(
            user_id=test_user.id,
            canonical_name="Whole Foods Market"
        )
        db_session.add(payee)
        db_session.commit()

        # Extract from messy description
        extracted, matched, extract_conf, match_score = extraction_service.extract_and_match(
            test_user.id,
            "WHOLE FOODS MARKET #456"
        )

        assert "Whole Foods Market" in extracted
        assert matched is not None
        assert matched.canonical_name == "Whole Foods Market"
        assert extract_conf > 0.5
        assert match_score > 0.8
