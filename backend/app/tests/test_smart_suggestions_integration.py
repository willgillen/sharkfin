"""
Tests for SmartRuleSuggestionService integration with PayeeExtractionService

Tests intelligent merchant detection and pattern recognition using
payee extraction for cleaning and grouping transaction descriptions.
"""
import pytest
from app.services.smart_rule_suggestion_service import SmartRuleSuggestionService
from app.models.user import User
from sqlalchemy.orm import Session


@pytest.fixture
def suggestion_service(db_session: Session):
    """Create SmartRuleSuggestionService with database session"""
    return SmartRuleSuggestionService(db=db_session)


@pytest.fixture
def test_user(db_session: Session):
    """Create test user"""
    from app.core.security import get_password_hash
    user = User(
        email="smart_suggestions@test.com",
        hashed_password=get_password_hash("testpass123"),
        full_name="Smart Suggestions Test User"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


class TestMerchantDetectionWithExtraction:
    """Test merchant detection using payee extraction"""

    def test_detect_starbucks_with_store_numbers(self, suggestion_service):
        """Test detecting Starbucks across transactions with different store numbers"""
        transactions = [
            {'description': 'STARBUCKS STORE 9876', 'payee': '', 'amount': -5.50},
            {'description': 'STARBUCKS #1234', 'payee': '', 'amount': -4.25},
            {'description': 'SQ *STARBUCKS COFFEE', 'payee': '', 'amount': -6.00},
        ]

        suggestions = suggestion_service.analyze_import_data(
            transactions=transactions,
            min_occurrences=2,
            min_confidence=0.6
        )

        # Should detect Starbucks pattern
        starbucks_suggestions = [s for s in suggestions if 'Starbucks' in s.detected_merchant]
        assert len(starbucks_suggestions) >= 1

        starbucks_suggestion = starbucks_suggestions[0]
        assert len(starbucks_suggestion.matching_rows) == 3
        assert starbucks_suggestion.confidence > 0.7
        # Should have extraction data
        assert starbucks_suggestion.extracted_payee_name is not None

    def test_detect_amazon_with_transaction_ids(self, suggestion_service):
        """Test detecting Amazon with different transaction IDs"""
        transactions = [
            {'description': 'AMAZON.COM*AB3CD4EF5', 'payee': '', 'amount': -25.99},
            {'description': 'AMAZON.COM*XY1ZW2QR3', 'payee': '', 'amount': -15.50},
            {'description': 'AMZN MKTP US*12AB34CD', 'payee': '', 'amount': -42.00},
        ]

        suggestions = suggestion_service.analyze_import_data(
            transactions=transactions,
            min_occurrences=2,
            min_confidence=0.6
        )

        # Should detect Amazon pattern
        amazon_suggestions = [s for s in suggestions if 'Amazon' in s.detected_merchant]
        assert len(amazon_suggestions) >= 1

        amazon_suggestion = amazon_suggestions[0]
        assert len(amazon_suggestion.matching_rows) >= 2
        assert amazon_suggestion.confidence > 0.6

    def test_square_payments_grouped_correctly(self, suggestion_service):
        """Test that Square payments are grouped by merchant, not by Square"""
        transactions = [
            {'description': 'SQ *COFFEE SHOP #123', 'payee': '', 'amount': -5.50},
            {'description': 'SQ *COFFEE SHOP #456', 'payee': '', 'amount': -6.00},
            {'description': 'SQ *RESTAURANT ABC', 'payee': '', 'amount': -25.00},
        ]

        suggestions = suggestion_service.analyze_import_data(
            transactions=transactions,
            min_occurrences=2,
            min_confidence=0.6
        )

        # Should suggest "Coffee Shop" pattern (appears 2 times)
        coffee_suggestions = [s for s in suggestions if 'Coffee Shop' in s.payee_pattern]
        assert len(coffee_suggestions) >= 1

        coffee_suggestion = coffee_suggestions[0]
        assert len(coffee_suggestion.matching_rows) == 2
        # Should have high extraction confidence (Square prefix removed)
        if coffee_suggestion.extraction_confidence:
            assert coffee_suggestion.extraction_confidence > 0.6


class TestPatternDetectionWithExtraction:
    """Test pattern detection for unknown merchants"""

    def test_find_common_payee_with_variations(self, suggestion_service):
        """Test finding common payee across variations"""
        transactions = [
            {'description': 'WHOLE FOODS MARKET #456', 'payee': '', 'amount': -50.00},
            {'description': 'WHOLE FOODS MKT STORE 789', 'payee': '', 'amount': -45.50},
            {'description': 'WHOLE FOODS #123', 'payee': '', 'amount': -62.00},
        ]

        suggestions = suggestion_service.analyze_import_data(
            transactions=transactions,
            min_occurrences=2,
            min_confidence=0.6
        )

        # Should detect Whole Foods pattern
        whole_foods_suggestions = [s for s in suggestions if 'Whole Foods' in s.detected_merchant]
        assert len(whole_foods_suggestions) >= 1

        suggestion = whole_foods_suggestions[0]
        assert len(suggestion.matching_rows) == 3
        assert suggestion.confidence > 0.6

    def test_url_based_merchants_cleaned(self, suggestion_service):
        """Test merchants with .com/.net cleaned properly"""
        transactions = [
            {'description': 'WWW.SPOTIFY.COM', 'payee': '', 'amount': -9.99},
            {'description': 'SPOTIFY.COM SUBSCRIPTION', 'payee': '', 'amount': -9.99},
            {'description': 'SPOTIFY PREMIUM', 'payee': '', 'amount': -9.99},
        ]

        suggestions = suggestion_service.analyze_import_data(
            transactions=transactions,
            min_occurrences=2,
            min_confidence=0.6
        )

        # Should detect Spotify pattern
        spotify_suggestions = [s for s in suggestions if 'Spotify' in s.detected_merchant]
        assert len(spotify_suggestions) >= 1

        suggestion = spotify_suggestions[0]
        assert len(suggestion.matching_rows) == 3
        # Extracted name should be clean "Spotify"
        if suggestion.extracted_payee_name:
            assert 'WWW' not in suggestion.extracted_payee_name.upper()
            assert '.COM' not in suggestion.extracted_payee_name.upper()

    def test_gas_stations_with_location_codes(self, suggestion_service):
        """Test gas stations with location codes grouped together"""
        transactions = [
            {'description': 'SHELL OIL 78912345', 'payee': '', 'amount': -45.00},
            {'description': 'SHELL 12345678', 'payee': '', 'amount': -50.00},
            {'description': 'SHELL #9876', 'payee': '', 'amount': -42.50},
        ]

        suggestions = suggestion_service.analyze_import_data(
            transactions=transactions,
            min_occurrences=2,
            min_confidence=0.6
        )

        # Should detect Shell pattern
        shell_suggestions = [s for s in suggestions if 'Shell' in s.detected_merchant]
        assert len(shell_suggestions) >= 1

        suggestion = shell_suggestions[0]
        assert len(suggestion.matching_rows) == 3
        # Location codes should be removed from extracted name
        if suggestion.extracted_payee_name:
            # Should not contain long numbers
            assert not any(char.isdigit() for word in suggestion.extracted_payee_name.split()
                          for char in word if len(word) > 4)


class TestConfidenceScoring:
    """Test confidence scoring with extraction"""

    def test_high_confidence_for_frequent_well_extracted(self, suggestion_service):
        """Test high confidence for frequently occurring, well-extracted payees"""
        transactions = [
            {'description': f'STARBUCKS STORE {i}', 'payee': '', 'amount': -5.00}
            for i in range(1000, 1006)  # 6 transactions
        ]

        suggestions = suggestion_service.analyze_import_data(
            transactions=transactions,
            min_occurrences=2,
            min_confidence=0.6
        )

        starbucks_suggestions = [s for s in suggestions if 'Starbucks' in s.detected_merchant]
        assert len(starbucks_suggestions) >= 1

        suggestion = starbucks_suggestions[0]
        # High frequency + good extraction = high confidence
        assert suggestion.confidence > 0.8

    def test_lower_confidence_for_infrequent(self, suggestion_service):
        """Test lower confidence for less frequently occurring patterns"""
        transactions = [
            {'description': 'RANDOM SHOP #123', 'payee': '', 'amount': -10.00},
            {'description': 'RANDOM SHOP #456', 'payee': '', 'amount': -12.00},
        ]

        suggestions = suggestion_service.analyze_import_data(
            transactions=transactions,
            min_occurrences=2,
            min_confidence=0.3  # Lower threshold
        )

        # Should still detect it, but with lower confidence
        random_suggestions = [s for s in suggestions if 'Random Shop' in s.payee_pattern]
        if len(random_suggestions) > 0:
            suggestion = random_suggestions[0]
            # Should have lower confidence than frequent patterns
            assert suggestion.confidence < 0.8

    def test_extraction_confidence_boosts_overall(self, suggestion_service):
        """Test that high extraction confidence boosts overall confidence"""
        # Transactions with clear, clean merchant names
        clean_transactions = [
            {'description': 'SQ *COFFEE SHOP', 'payee': '', 'amount': -5.00},
            {'description': 'SQ *COFFEE SHOP', 'payee': '', 'amount': -6.00},
        ]

        suggestions = suggestion_service.analyze_import_data(
            transactions=clean_transactions,
            min_occurrences=2,
            min_confidence=0.6
        )

        # Should have extraction confidence data
        if len(suggestions) > 0:
            suggestion = suggestions[0]
            assert suggestion.extraction_confidence is not None
            # Square prefix removal should have high extraction confidence
            assert suggestion.extraction_confidence > 0.6


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_empty_transactions_list(self, suggestion_service):
        """Test handling empty transactions"""
        suggestions = suggestion_service.analyze_import_data(
            transactions=[],
            min_occurrences=2,
            min_confidence=0.6
        )

        assert suggestions == []

    def test_transactions_with_empty_descriptions(self, suggestion_service):
        """Test handling transactions with empty descriptions"""
        transactions = [
            {'description': '', 'payee': '', 'amount': -10.00},
            {'description': None, 'payee': '', 'amount': -15.00},
        ]

        suggestions = suggestion_service.analyze_import_data(
            transactions=transactions,
            min_occurrences=1,
            min_confidence=0.3
        )

        # Should not crash, may have no suggestions
        assert isinstance(suggestions, list)

    def test_single_occurrence_below_threshold(self, suggestion_service):
        """Test that single occurrences don't create suggestions"""
        transactions = [
            {'description': 'UNIQUE MERCHANT #1', 'payee': '', 'amount': -10.00},
            {'description': 'ANOTHER MERCHANT #2', 'payee': '', 'amount': -15.00},
            {'description': 'THIRD MERCHANT #3', 'payee': '', 'amount': -20.00},
        ]

        suggestions = suggestion_service.analyze_import_data(
            transactions=transactions,
            min_occurrences=2,
            min_confidence=0.6
        )

        # Should have no suggestions (all unique)
        assert len(suggestions) == 0

    def test_very_short_merchant_names_filtered(self, suggestion_service):
        """Test that very short extracted names are filtered out"""
        transactions = [
            {'description': 'AB #123', 'payee': '', 'amount': -10.00},
            {'description': 'AB #456', 'payee': '', 'amount': -12.00},
            {'description': 'AB #789', 'payee': '', 'amount': -15.00},
        ]

        suggestions = suggestion_service.analyze_import_data(
            transactions=transactions,
            min_occurrences=2,
            min_confidence=0.6
        )

        # Should filter out "AB" (too short - less than 3 chars)
        ab_suggestions = [s for s in suggestions if s.payee_pattern == 'AB']
        assert len(ab_suggestions) == 0


class TestRealWorldScenarios:
    """Test real-world transaction scenarios"""

    def test_mixed_payment_processors(self, suggestion_service):
        """Test transactions from same merchant via different processors"""
        transactions = [
            {'description': 'SQ *LOCAL CAFE', 'payee': '', 'amount': -5.50},
            {'description': 'TST* LOCAL CAFE', 'payee': '', 'amount': -6.00},
            {'description': 'LOCAL CAFE #123', 'payee': '', 'amount': -7.50},
        ]

        suggestions = suggestion_service.analyze_import_data(
            transactions=transactions,
            min_occurrences=2,
            min_confidence=0.6
        )

        # Should group all as "Local Cafe"
        cafe_suggestions = [s for s in suggestions if 'Local Cafe' in s.payee_pattern]
        assert len(cafe_suggestions) >= 1

        suggestion = cafe_suggestions[0]
        assert len(suggestion.matching_rows) == 3

    def test_subscription_services(self, suggestion_service):
        """Test recurring subscription payments"""
        transactions = [
            {'description': 'NETFLIX.COM', 'payee': '', 'amount': -15.99},
            {'description': 'NETFLIX SUBSCRIPTION', 'payee': '', 'amount': -15.99},
            {'description': 'WWW.NETFLIX.COM', 'payee': '', 'amount': -15.99},
        ]

        suggestions = suggestion_service.analyze_import_data(
            transactions=transactions,
            min_occurrences=2,
            min_confidence=0.6
        )

        # Should detect Netflix
        netflix_suggestions = [s for s in suggestions if 'Netflix' in s.detected_merchant]
        assert len(netflix_suggestions) >= 1

        suggestion = netflix_suggestions[0]
        assert len(suggestion.matching_rows) == 3

    def test_walmart_with_various_formats(self, suggestion_service):
        """Test Walmart transactions with various description formats"""
        transactions = [
            {'description': 'WALMART STORE 1234', 'payee': '', 'amount': -50.00},
            {'description': 'WALMART #5678', 'payee': '', 'amount': -45.00},
            {'description': 'WAL-MART SUPERCENTER', 'payee': '', 'amount': -60.00},
            {'description': 'WALMART.COM', 'payee': '', 'amount': -35.00},
        ]

        suggestions = suggestion_service.analyze_import_data(
            transactions=transactions,
            min_occurrences=2,
            min_confidence=0.6
        )

        # Should detect Walmart
        walmart_suggestions = [s for s in suggestions if 'Walmart' in s.detected_merchant]
        assert len(walmart_suggestions) >= 1

        suggestion = walmart_suggestions[0]
        # Should match at least 3 of the 4 transactions
        assert len(suggestion.matching_rows) >= 3
