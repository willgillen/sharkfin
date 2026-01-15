import pytest
from decimal import Decimal
from app.services.rule_engine import RuleEngine
from app.models.categorization_rule import CategorizationRule
from app.models.transaction import Transaction, TransactionType
from app.models.category import Category
from datetime import date


class TestRuleEngine:
    """Test suite for RuleEngine service"""

    @pytest.fixture
    def rule_engine(self, db_session):
        """Create a RuleEngine instance with test database session"""
        return RuleEngine(db_session)

    @pytest.fixture
    def test_category(self, db_session, test_user):
        """Create a test category"""
        category = Category(
            user_id=test_user.id,
            name="Groceries",
            type="expense"
        )
        db_session.add(category)
        db_session.commit()
        db_session.refresh(category)
        return category

    # Test: Pattern matching - contains
    def test_payee_contains_match(self, rule_engine):
        """Test 'contains' pattern matching for payee"""
        rule = CategorizationRule(
            user_id=1,
            name="Amazon Rule",
            payee_pattern="AMAZON",
            payee_match_type="contains",
            enabled=True
        )

        transaction = Transaction(
            payee="AMAZON.COM*123ABC",
            amount=Decimal("50.00"),
            type=TransactionType.DEBIT,
            date=date.today()
        )

        assert rule_engine._text_matches(transaction.payee, rule.payee_pattern, rule.payee_match_type) is True

    def test_payee_contains_no_match(self, rule_engine):
        """Test 'contains' pattern matching when it should not match"""
        rule = CategorizationRule(
            user_id=1,
            name="Amazon Rule",
            payee_pattern="AMAZON",
            payee_match_type="contains",
            enabled=True
        )

        transaction = Transaction(
            payee="WALMART STORE #123",
            amount=Decimal("50.00"),
            type=TransactionType.DEBIT,
            date=date.today()
        )

        assert rule_engine._text_matches(transaction.payee, rule.payee_pattern, rule.payee_match_type) is False

    # Test: Pattern matching - starts_with
    def test_payee_starts_with_match(self, rule_engine):
        """Test 'starts_with' pattern matching"""
        rule = CategorizationRule(
            user_id=1,
            name="Starbucks Rule",
            payee_pattern="STARBUCKS",
            payee_match_type="starts_with",
            enabled=True
        )

        transaction = Transaction(
            payee="STARBUCKS #1234",
            amount=Decimal("5.50"),
            type=TransactionType.DEBIT,
            date=date.today()
        )

        assert rule_engine._text_matches(transaction.payee, rule.payee_pattern, rule.payee_match_type) is True

    def test_payee_starts_with_no_match(self, rule_engine):
        """Test 'starts_with' when payee doesn't start with pattern"""
        rule = CategorizationRule(
            user_id=1,
            name="Starbucks Rule",
            payee_pattern="STARBUCKS",
            payee_match_type="starts_with",
            enabled=True
        )

        transaction = Transaction(
            payee="COFFEE AT STARBUCKS",
            amount=Decimal("5.50"),
            type=TransactionType.DEBIT,
            date=date.today()
        )

        assert rule_engine._text_matches(transaction.payee, rule.payee_pattern, rule.payee_match_type) is False

    # Test: Pattern matching - ends_with
    def test_payee_ends_with_match(self, rule_engine):
        """Test 'ends_with' pattern matching"""
        rule = CategorizationRule(
            user_id=1,
            name="Direct Deposit Rule",
            description_pattern="DIRECT DEP",
            description_match_type="ends_with",
            enabled=True
        )

        transaction = Transaction(
            description="PAYROLL DIRECT DEP",
            amount=Decimal("2000.00"),
            type=TransactionType.CREDIT,
            date=date.today()
        )

        assert rule_engine._text_matches(transaction.description, rule.description_pattern, rule.description_match_type) is True

    # Test: Pattern matching - exact
    def test_payee_exact_match(self, rule_engine):
        """Test 'exact' pattern matching"""
        rule = CategorizationRule(
            user_id=1,
            name="Exact Payee Rule",
            payee_pattern="NETFLIX.COM",
            payee_match_type="exact",
            enabled=True
        )

        transaction = Transaction(
            payee="NETFLIX.COM",
            amount=Decimal("15.99"),
            type=TransactionType.DEBIT,
            date=date.today()
        )

        assert rule_engine._text_matches(transaction.payee, rule.payee_pattern, rule.payee_match_type) is True

    def test_payee_exact_no_match(self, rule_engine):
        """Test 'exact' matching when not exact"""
        rule = CategorizationRule(
            user_id=1,
            name="Exact Payee Rule",
            payee_pattern="NETFLIX.COM",
            payee_match_type="exact",
            enabled=True
        )

        transaction = Transaction(
            payee="NETFLIX.COM SUBSCRIPTION",
            amount=Decimal("15.99"),
            type=TransactionType.DEBIT,
            date=date.today()
        )

        assert rule_engine._text_matches(transaction.payee, rule.payee_pattern, rule.payee_match_type) is False

    # Test: Pattern matching - regex
    def test_payee_regex_match(self, rule_engine):
        """Test regex pattern matching"""
        rule = CategorizationRule(
            user_id=1,
            name="Ride Share Rule",
            payee_pattern="UBER|LYFT",
            payee_match_type="regex",
            enabled=True
        )

        uber_transaction = Transaction(
            payee="UBER TECHNOLOGIES",
            amount=Decimal("15.00"),
            type=TransactionType.DEBIT,
            date=date.today()
        )

        lyft_transaction = Transaction(
            payee="LYFT RIDE",
            amount=Decimal("12.00"),
            type=TransactionType.DEBIT,
            date=date.today()
        )

        assert rule_engine._text_matches(uber_transaction.payee, rule.payee_pattern, rule.payee_match_type) is True
        assert rule_engine._text_matches(lyft_transaction.payee, rule.payee_pattern, rule.payee_match_type) is True

    # Test: Case insensitivity
    def test_pattern_matching_case_insensitive(self, rule_engine):
        """Test that pattern matching is case insensitive"""
        rule = CategorizationRule(
            user_id=1,
            name="Case Test",
            payee_pattern="amazon",
            payee_match_type="contains",
            enabled=True
        )

        transaction = Transaction(
            payee="AMAZON.COM",
            amount=Decimal("50.00"),
            type=TransactionType.DEBIT,
            date=date.today()
        )

        assert rule_engine._text_matches(transaction.payee, rule.payee_pattern, rule.payee_match_type) is True

    # Test: Amount range matching
    def test_amount_range_match(self, rule_engine):
        """Test amount range conditions"""
        rule = CategorizationRule(
            user_id=1,
            name="Small Purchases",
            amount_min=Decimal("1.00"),
            amount_max=Decimal("10.00"),
            enabled=True
        )

        # Within range
        transaction1 = Transaction(
            amount=Decimal("5.00"),
            type=TransactionType.DEBIT,
            date=date.today()
        )
        assert rule_engine._rule_matches(transaction1, rule) is True

        # Below minimum
        transaction2 = Transaction(
            amount=Decimal("0.50"),
            type=TransactionType.DEBIT,
            date=date.today()
        )
        assert rule_engine._rule_matches(transaction2, rule) is False

        # Above maximum
        transaction3 = Transaction(
            amount=Decimal("15.00"),
            type=TransactionType.DEBIT,
            date=date.today()
        )
        assert rule_engine._rule_matches(transaction3, rule) is False

    # Test: Transaction type filtering
    def test_transaction_type_filter(self, rule_engine):
        """Test transaction type filtering"""
        rule = CategorizationRule(
            user_id=1,
            name="Debit Only",
            transaction_type="DEBIT",
            enabled=True
        )

        debit_transaction = Transaction(
            amount=Decimal("50.00"),
            type=TransactionType.DEBIT,
            date=date.today()
        )
        assert rule_engine._rule_matches(debit_transaction, rule) is True

        credit_transaction = Transaction(
            amount=Decimal("1000.00"),
            type=TransactionType.CREDIT,
            date=date.today()
        )
        assert rule_engine._rule_matches(credit_transaction, rule) is False

    # Test: Multiple conditions (AND logic)
    def test_multiple_conditions_all_match(self, rule_engine):
        """Test that all non-null conditions must match"""
        rule = CategorizationRule(
            user_id=1,
            name="Complex Rule",
            payee_pattern="AMAZON",
            payee_match_type="contains",
            amount_min=Decimal("20.00"),
            amount_max=Decimal("100.00"),
            transaction_type="DEBIT",
            enabled=True
        )

        # All conditions match
        transaction1 = Transaction(
            payee="AMAZON.COM",
            amount=Decimal("50.00"),
            type=TransactionType.DEBIT,
            date=date.today()
        )
        assert rule_engine._rule_matches(transaction1, rule) is True

        # Payee doesn't match
        transaction2 = Transaction(
            payee="WALMART",
            amount=Decimal("50.00"),
            type=TransactionType.DEBIT,
            date=date.today()
        )
        assert rule_engine._rule_matches(transaction2, rule) is False

        # Amount out of range
        transaction3 = Transaction(
            payee="AMAZON.COM",
            amount=Decimal("150.00"),
            type=TransactionType.DEBIT,
            date=date.today()
        )
        assert rule_engine._rule_matches(transaction3, rule) is False

        # Wrong transaction type
        transaction4 = Transaction(
            payee="AMAZON.COM",
            amount=Decimal("50.00"),
            type=TransactionType.CREDIT,
            date=date.today()
        )
        assert rule_engine._rule_matches(transaction4, rule) is False

    # Test: Apply rule actions
    def test_apply_rule_sets_category(self, rule_engine, test_category, test_account, db_session):
        """Test applying a rule sets the category"""
        rule = CategorizationRule(
            user_id=test_category.user_id,
            name="Grocery Rule",
            category_id=test_category.id,
            enabled=True
        )
        db_session.add(rule)
        db_session.commit()

        transaction = Transaction(
            user_id=test_category.user_id,
            account_id=test_account.id,
            amount=Decimal("50.00"),
            type=TransactionType.DEBIT,
            date=date.today()
        )
        db_session.add(transaction)
        db_session.commit()

        rule_engine.apply_rule(transaction, rule)
        db_session.commit()

        assert transaction.category_id == test_category.id
        assert rule.match_count == 1
        assert rule.last_matched_at is not None

    def test_apply_rule_renames_payee(self, rule_engine, test_user, test_account, db_session):
        """Test applying a rule renames the payee"""
        rule = CategorizationRule(
            user_id=test_user.id,
            name="Clean Payee Rule",
            new_payee="Amazon",
            enabled=True
        )
        db_session.add(rule)
        db_session.commit()

        transaction = Transaction(
            user_id=test_user.id,
            account_id=test_account.id,
            payee="AMAZON.COM*123ABC",
            amount=Decimal("50.00"),
            type=TransactionType.DEBIT,
            date=date.today()
        )
        db_session.add(transaction)
        db_session.commit()

        rule_engine.apply_rule(transaction, rule)
        db_session.commit()

        assert transaction.payee == "Amazon"

    def test_apply_rule_appends_notes(self, rule_engine, test_user, test_account, db_session):
        """Test applying a rule appends to notes"""
        rule = CategorizationRule(
            user_id=test_user.id,
            name="Note Rule",
            notes_append="Auto-categorized by rule",
            enabled=True
        )
        db_session.add(rule)
        db_session.commit()

        transaction = Transaction(
            user_id=test_user.id,
            account_id=test_account.id,
            amount=Decimal("50.00"),
            type=TransactionType.DEBIT,
            date=date.today(),
            notes="Existing note"
        )
        db_session.add(transaction)
        db_session.commit()

        rule_engine.apply_rule(transaction, rule)
        db_session.commit()

        assert "Existing note" in transaction.notes
        assert "Auto-categorized by rule" in transaction.notes

    # Test: Priority ordering
    def test_rules_evaluated_by_priority(self, rule_engine, test_category, db_session):
        """Test that rules are evaluated in priority order (highest first)"""
        # Create two rules with different priorities
        low_priority_rule = CategorizationRule(
            user_id=test_category.user_id,
            name="Low Priority",
            priority=1,
            payee_pattern="AMAZON",
            payee_match_type="contains",
            category_id=test_category.id,
            enabled=True
        )

        category2 = Category(
            user_id=test_category.user_id,
            name="Electronics",
            type="expense"
        )
        db_session.add(category2)
        db_session.commit()

        high_priority_rule = CategorizationRule(
            user_id=test_category.user_id,
            name="High Priority",
            priority=10,
            payee_pattern="AMAZON",
            payee_match_type="contains",
            category_id=category2.id,
            enabled=True
        )

        db_session.add_all([low_priority_rule, high_priority_rule])
        db_session.commit()

        transaction = Transaction(
            user_id=test_category.user_id,
            account_id=1,
            payee="AMAZON.COM",
            amount=Decimal("50.00"),
            type=TransactionType.DEBIT,
            date=date.today()
        )

        # Get active rules (should be ordered by priority desc)
        rules = rule_engine.get_active_rules(test_category.user_id)
        assert rules[0].id == high_priority_rule.id  # Higher priority first
        assert rules[1].id == low_priority_rule.id

        # Evaluate should match the high priority rule first
        matching_rule = rule_engine.evaluate_transaction(transaction, rules)
        assert matching_rule.id == high_priority_rule.id

    # Test: Disabled rules are skipped
    def test_disabled_rules_not_evaluated(self, rule_engine, test_category, db_session):
        """Test that disabled rules are not returned"""
        enabled_rule = CategorizationRule(
            user_id=test_category.user_id,
            name="Enabled Rule",
            enabled=True
        )

        disabled_rule = CategorizationRule(
            user_id=test_category.user_id,
            name="Disabled Rule",
            enabled=False
        )

        db_session.add_all([enabled_rule, disabled_rule])
        db_session.commit()

        rules = rule_engine.get_active_rules(test_category.user_id)

        assert len(rules) == 1
        assert rules[0].id == enabled_rule.id

    # Test: Null/empty text handling
    def test_null_payee_no_match(self, rule_engine):
        """Test that null/empty payee doesn't match"""
        rule = CategorizationRule(
            user_id=1,
            name="Test Rule",
            payee_pattern="AMAZON",
            payee_match_type="contains",
            enabled=True
        )

        transaction = Transaction(
            payee=None,
            amount=Decimal("50.00"),
            type=TransactionType.DEBIT,
            date=date.today()
        )

        assert rule_engine._text_matches(transaction.payee, rule.payee_pattern, rule.payee_match_type) is False

    # Test: Batch categorization
    def test_categorize_multiple_transactions(self, rule_engine, test_category, test_account, db_session):
        """Test categorizing multiple transactions at once"""
        rule = CategorizationRule(
            user_id=test_category.user_id,
            name="Grocery Rule",
            payee_pattern="SAFEWAY|KROGER|WHOLE FOODS",
            payee_match_type="regex",
            category_id=test_category.id,
            enabled=True
        )
        db_session.add(rule)
        db_session.commit()

        transactions = [
            Transaction(
                user_id=test_category.user_id,
                account_id=test_account.id,
                payee="SAFEWAY #123",
                amount=Decimal("50.00"),
                type=TransactionType.DEBIT,
                date=date.today()
            ),
            Transaction(
                user_id=test_category.user_id,
                account_id=test_account.id,
                payee="KROGER",
                amount=Decimal("75.00"),
                type=TransactionType.DEBIT,
                date=date.today()
            ),
            Transaction(
                user_id=test_category.user_id,
                account_id=test_account.id,
                payee="WALMART",  # Should not match
                amount=Decimal("100.00"),
                type=TransactionType.DEBIT,
                date=date.today()
            ),
        ]

        for txn in transactions:
            db_session.add(txn)
        db_session.commit()

        stats = rule_engine.categorize_transactions(test_category.user_id, transactions)

        assert stats['categorized'] == 2
        assert stats['uncategorized'] == 1
        assert stats['rules_used'] == 1
        assert transactions[0].category_id == test_category.id
        assert transactions[1].category_id == test_category.id
        assert transactions[2].category_id is None
