import pytest
from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from app.models.transaction import Transaction, TransactionType
from app.models.category import Category
from app.models.account import Account, AccountType
from app.models.user import User
from app.services.rule_learning_service import RuleLearningService, RuleSuggestion


class TestRuleLearningService:
    """Test suite for automatic rule learning from user behavior."""

    @pytest.fixture
    def rule_learning_service(self, db_session):
        """Create RuleLearningService instance."""
        return RuleLearningService(db_session)

    @pytest.fixture
    def test_category_groceries(self, db_session, test_user):
        """Create a test groceries category."""
        category = Category(
            user_id=test_user.id,
            name="Groceries",
            type="expense"
        )
        db_session.add(category)
        db_session.commit()
        db_session.refresh(category)
        return category

    @pytest.fixture
    def test_category_gas(self, db_session, test_user):
        """Create a test gas category."""
        category = Category(
            user_id=test_user.id,
            name="Gas & Fuel",
            type="expense"
        )
        db_session.add(category)
        db_session.commit()
        db_session.refresh(category)
        return category

    def test_detect_payee_pattern_exact_match(self, rule_learning_service, test_user,
                                              test_account, test_category_groceries, db_session):
        """Test detecting exact payee pattern when user consistently categorizes same payee."""
        # Create 5 transactions with identical payee, all categorized the same
        for i in range(5):
            txn = Transaction(
                user_id=test_user.id,
                account_id=test_account.id,
                date=date.today() - timedelta(days=i),
                amount=Decimal("50.00"),
                type=TransactionType.DEBIT,
                payee="SAFEWAY STORE #1234",
                category_id=test_category_groceries.id
            )
            db_session.add(txn)
        db_session.commit()

        suggestions = rule_learning_service.analyze_user_patterns(test_user.id)

        assert len(suggestions) >= 1
        safeway_suggestion = next((s for s in suggestions if "SAFEWAY" in s.payee_pattern), None)
        assert safeway_suggestion is not None
        assert safeway_suggestion.category_id == test_category_groceries.id
        assert safeway_suggestion.confidence_score >= 0.8  # High confidence
        assert safeway_suggestion.match_count == 5

    def test_detect_payee_pattern_contains_match(self, rule_learning_service, test_user,
                                                 test_account, test_category_groceries, db_session):
        """Test detecting 'contains' pattern when payee has common substring."""
        # Create transactions with variations of same payee
        payees = ["SAFEWAY STORE #1234", "SAFEWAY #5678", "SAFEWAY ONLINE", "SAFEWAY GAS"]
        for payee in payees:
            txn = Transaction(
                user_id=test_user.id,
                account_id=test_account.id,
                date=date.today(),
                amount=Decimal("50.00"),
                type=TransactionType.DEBIT,
                payee=payee,
                category_id=test_category_groceries.id
            )
            db_session.add(txn)
        db_session.commit()

        suggestions = rule_learning_service.analyze_user_patterns(test_user.id)

        safeway_suggestion = next((s for s in suggestions if "SAFEWAY" in s.payee_pattern), None)
        assert safeway_suggestion is not None
        assert safeway_suggestion.payee_match_type == "contains"
        assert safeway_suggestion.category_id == test_category_groceries.id

    def test_detect_multiple_patterns(self, rule_learning_service, test_user, test_account,
                                     test_category_groceries, test_category_gas, db_session):
        """Test detecting multiple distinct patterns for different categories."""
        # Groceries transactions
        for i in range(4):
            txn = Transaction(
                user_id=test_user.id,
                account_id=test_account.id,
                date=date.today(),
                amount=Decimal("50.00"),
                type=TransactionType.DEBIT,
                payee=f"WHOLE FOODS #{i}",
                category_id=test_category_groceries.id
            )
            db_session.add(txn)

        # Gas transactions
        for i in range(4):
            txn = Transaction(
                user_id=test_user.id,
                account_id=test_account.id,
                date=date.today(),
                amount=Decimal("40.00"),
                type=TransactionType.DEBIT,
                payee=f"CHEVRON #{i}",
                category_id=test_category_gas.id
            )
            db_session.add(txn)
        db_session.commit()

        suggestions = rule_learning_service.analyze_user_patterns(test_user.id)

        assert len(suggestions) >= 2
        groceries_suggestions = [s for s in suggestions if s.category_id == test_category_groceries.id]
        gas_suggestions = [s for s in suggestions if s.category_id == test_category_gas.id]

        assert len(groceries_suggestions) >= 1
        assert len(gas_suggestions) >= 1

    def test_ignore_low_frequency_patterns(self, rule_learning_service, test_user,
                                          test_account, test_category_groceries, db_session):
        """Test that patterns with low frequency (< 3 occurrences) are not suggested."""
        # Create only 2 transactions with same payee
        for i in range(2):
            txn = Transaction(
                user_id=test_user.id,
                account_id=test_account.id,
                date=date.today(),
                amount=Decimal("50.00"),
                type=TransactionType.DEBIT,
                payee="RARE MERCHANT",
                category_id=test_category_groceries.id
            )
            db_session.add(txn)
        db_session.commit()

        suggestions = rule_learning_service.analyze_user_patterns(test_user.id, min_occurrences=3)

        # Should not suggest rule for "RARE MERCHANT" since it only has 2 occurrences
        rare_suggestions = [s for s in suggestions if "RARE MERCHANT" in s.payee_pattern]
        assert len(rare_suggestions) == 0

    def test_confidence_score_calculation(self, rule_learning_service, test_user,
                                         test_account, test_category_groceries, db_session):
        """Test confidence score is based on consistency and frequency."""
        # Create 10 consistent transactions
        for i in range(10):
            txn = Transaction(
                user_id=test_user.id,
                account_id=test_account.id,
                date=date.today() - timedelta(days=i),
                amount=Decimal("50.00"),
                type=TransactionType.DEBIT,
                payee="CONSISTENT MERCHANT",
                category_id=test_category_groceries.id
            )
            db_session.add(txn)
        db_session.commit()

        suggestions = rule_learning_service.analyze_user_patterns(test_user.id)

        consistent_suggestion = next((s for s in suggestions if "CONSISTENT MERCHANT" in s.payee_pattern), None)
        assert consistent_suggestion is not None
        # High consistency and frequency should yield high confidence
        assert consistent_suggestion.confidence_score >= 0.85

    def test_exclude_already_ruled_patterns(self, rule_learning_service, test_user,
                                           test_account, test_category_groceries, db_session):
        """Test that existing rules are not suggested again."""
        from app.models.categorization_rule import CategorizationRule

        # Create existing rule
        existing_rule = CategorizationRule(
            user_id=test_user.id,
            name="Safeway Rule",
            payee_pattern="SAFEWAY",
            payee_match_type="contains",
            category_id=test_category_groceries.id,
            enabled=True
        )
        db_session.add(existing_rule)

        # Create transactions matching the existing rule
        for i in range(5):
            txn = Transaction(
                user_id=test_user.id,
                account_id=test_account.id,
                date=date.today(),
                amount=Decimal("50.00"),
                type=TransactionType.DEBIT,
                payee="SAFEWAY STORE",
                category_id=test_category_groceries.id
            )
            db_session.add(txn)
        db_session.commit()

        suggestions = rule_learning_service.analyze_user_patterns(test_user.id)

        # Should not suggest SAFEWAY since rule already exists
        safeway_suggestions = [s for s in suggestions if "SAFEWAY" in s.payee_pattern]
        assert len(safeway_suggestions) == 0

    def test_detect_amount_range_pattern(self, rule_learning_service, test_user,
                                        test_account, test_category_gas, db_session):
        """Test detecting amount range patterns for recurring bills."""
        # Create transactions with consistent amount range
        amounts = [Decimal("45.00"), Decimal("48.50"), Decimal("47.25"), Decimal("46.00"), Decimal("49.00")]
        for amt in amounts:
            txn = Transaction(
                user_id=test_user.id,
                account_id=test_account.id,
                date=date.today(),
                amount=amt,
                type=TransactionType.DEBIT,
                payee="UTILITY COMPANY",
                category_id=test_category_gas.id
            )
            db_session.add(txn)
        db_session.commit()

        suggestions = rule_learning_service.analyze_user_patterns(test_user.id)

        utility_suggestion = next((s for s in suggestions if "UTILITY COMPANY" in s.payee_pattern), None)
        assert utility_suggestion is not None
        # Should suggest amount range based on observed values
        if utility_suggestion.amount_min is not None and utility_suggestion.amount_max is not None:
            assert utility_suggestion.amount_min <= Decimal("45.00")
            assert utility_suggestion.amount_max >= Decimal("49.00")

    def test_ignore_uncategorized_transactions(self, rule_learning_service, test_user,
                                              test_account, db_session):
        """Test that uncategorized transactions are not used for pattern learning."""
        # Create uncategorized transactions
        for i in range(10):
            txn = Transaction(
                user_id=test_user.id,
                account_id=test_account.id,
                date=date.today(),
                amount=Decimal("50.00"),
                type=TransactionType.DEBIT,
                payee="UNCATEGORIZED MERCHANT",
                category_id=None  # No category
            )
            db_session.add(txn)
        db_session.commit()

        suggestions = rule_learning_service.analyze_user_patterns(test_user.id)

        # Should not suggest rule for uncategorized transactions
        uncategorized_suggestions = [s for s in suggestions if "UNCATEGORIZED MERCHANT" in (s.payee_pattern or "")]
        assert len(uncategorized_suggestions) == 0

    def test_transaction_type_filtering(self, rule_learning_service, test_user,
                                       test_account, test_category_groceries, db_session):
        """Test that transaction type is included in rule suggestion when consistent."""
        # Create all DEBIT transactions
        for i in range(5):
            txn = Transaction(
                user_id=test_user.id,
                account_id=test_account.id,
                date=date.today(),
                amount=Decimal("50.00"),
                type=TransactionType.DEBIT,
                payee="GROCERY STORE",
                category_id=test_category_groceries.id
            )
            db_session.add(txn)
        db_session.commit()

        suggestions = rule_learning_service.analyze_user_patterns(test_user.id)

        grocery_suggestion = next((s for s in suggestions if "GROCERY STORE" in s.payee_pattern), None)
        assert grocery_suggestion is not None
        assert grocery_suggestion.transaction_type == "DEBIT"

    def test_suggest_rule_name_generation(self, rule_learning_service, test_user,
                                         test_account, test_category_groceries, db_session):
        """Test that suggested rules have meaningful auto-generated names."""
        for i in range(4):
            txn = Transaction(
                user_id=test_user.id,
                account_id=test_account.id,
                date=date.today(),
                amount=Decimal("50.00"),
                type=TransactionType.DEBIT,
                payee="TARGET STORE",
                category_id=test_category_groceries.id
            )
            db_session.add(txn)
        db_session.commit()

        suggestions = rule_learning_service.analyze_user_patterns(test_user.id)

        target_suggestion = next((s for s in suggestions if "TARGET" in s.payee_pattern), None)
        assert target_suggestion is not None
        assert target_suggestion.suggested_rule_name is not None
        assert len(target_suggestion.suggested_rule_name) > 0
        # Name should reference the payee pattern
        assert "TARGET" in target_suggestion.suggested_rule_name.upper()

    def test_find_common_substring(self, rule_learning_service):
        """Test helper method to find longest common substring."""
        payees = ["AMAZON.COM*123ABC", "AMAZON.COM*456DEF", "AMAZON PRIME", "AMAZON AWS"]
        common = rule_learning_service._find_common_substring(payees)

        assert "AMAZON" in common.upper()

    def test_calculate_pattern_consistency(self, rule_learning_service):
        """Test consistency calculation for pattern matching."""
        # All same category = 100% consistency
        categories = [1, 1, 1, 1, 1]
        consistency = rule_learning_service._calculate_consistency(categories)
        assert consistency == 1.0

        # 4 out of 5 same = 80% consistency
        categories = [1, 1, 1, 1, 2]
        consistency = rule_learning_service._calculate_consistency(categories)
        assert consistency == 0.8

    def test_minimum_confidence_threshold(self, rule_learning_service, test_user,
                                         test_account, test_category_groceries, db_session):
        """Test that only suggestions above confidence threshold are returned."""
        # Create inconsistent pattern (50/50 split between categories)
        category2 = Category(user_id=test_user.id, name="Other", type="expense")
        db_session.add(category2)
        db_session.commit()

        for i in range(3):
            txn = Transaction(
                user_id=test_user.id,
                account_id=test_account.id,
                date=date.today(),
                amount=Decimal("50.00"),
                type=TransactionType.DEBIT,
                payee="INCONSISTENT MERCHANT",
                category_id=test_category_groceries.id if i % 2 == 0 else category2.id
            )
            db_session.add(txn)
        db_session.commit()

        suggestions = rule_learning_service.analyze_user_patterns(test_user.id, min_confidence=0.7)

        # Should not suggest rule with low consistency
        inconsistent_suggestions = [s for s in suggestions if "INCONSISTENT MERCHANT" in (s.payee_pattern or "")]
        assert len(inconsistent_suggestions) == 0
