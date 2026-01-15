from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import re
from decimal import Decimal

from app.models.categorization_rule import CategorizationRule
from app.models.transaction import Transaction


class RuleEngine:
    """
    Rules engine for automatic transaction categorization.

    Evaluates transactions against user-defined rules and applies
    matching actions (category assignment, payee renaming, etc.).
    """

    def __init__(self, db: Session):
        self.db = db

    def get_active_rules(self, user_id: int) -> List[CategorizationRule]:
        """
        Get all active rules for a user, ordered by priority (highest first).

        Args:
            user_id: ID of the user

        Returns:
            List of active rules ordered by priority descending
        """
        return self.db.query(CategorizationRule).filter(
            CategorizationRule.user_id == user_id,
            CategorizationRule.enabled == True
        ).order_by(CategorizationRule.priority.desc()).all()

    def evaluate_transaction(
        self,
        transaction: Transaction,
        rules: List[CategorizationRule]
    ) -> Optional[CategorizationRule]:
        """
        Find the first matching rule for a transaction.

        Rules are evaluated in the order provided (should be priority desc).
        Returns the first rule that matches all its conditions.

        Args:
            transaction: Transaction to evaluate
            rules: List of rules to check (pre-ordered by priority)

        Returns:
            First matching rule, or None if no match
        """
        for rule in rules:
            if self._rule_matches(transaction, rule):
                return rule
        return None

    def _rule_matches(self, transaction: Transaction, rule: CategorizationRule) -> bool:
        """
        Check if all rule conditions match a transaction.

        All non-null conditions must match (AND logic).

        Args:
            transaction: Transaction to check
            rule: Rule to evaluate

        Returns:
            True if all conditions match, False otherwise
        """
        # Payee matching
        if rule.payee_pattern:
            if not self._text_matches(
                transaction.payee,
                rule.payee_pattern,
                rule.payee_match_type
            ):
                return False

        # Description matching
        if rule.description_pattern:
            if not self._text_matches(
                transaction.description,
                rule.description_pattern,
                rule.description_match_type
            ):
                return False

        # Amount range
        if rule.amount_min is not None:
            if transaction.amount < rule.amount_min:
                return False

        if rule.amount_max is not None:
            if transaction.amount > rule.amount_max:
                return False

        # Transaction type
        if rule.transaction_type:
            # Compare enum name, not value
            if transaction.type.name != rule.transaction_type:
                return False

        return True

    def _text_matches(
        self,
        text: Optional[str],
        pattern: str,
        match_type: str
    ) -> bool:
        """
        Match text against pattern using specified match type.

        Matching is case-insensitive.

        Args:
            text: Text to match (may be None)
            pattern: Pattern to match against
            match_type: Type of matching ('contains', 'starts_with', 'ends_with', 'exact', 'regex')

        Returns:
            True if text matches pattern, False otherwise
        """
        if not text:
            return False

        text_lower = text.lower()
        pattern_lower = pattern.lower()

        if match_type == 'contains':
            return pattern_lower in text_lower

        elif match_type == 'starts_with':
            return text_lower.startswith(pattern_lower)

        elif match_type == 'ends_with':
            return text_lower.endswith(pattern_lower)

        elif match_type == 'exact':
            return text_lower == pattern_lower

        elif match_type == 'regex':
            try:
                return bool(re.search(pattern, text, re.IGNORECASE))
            except re.error:
                # Invalid regex pattern - treat as no match
                return False

        return False

    def apply_rule(self, transaction: Transaction, rule: CategorizationRule):
        """
        Apply rule actions to a transaction.

        Modifies the transaction in place and updates rule statistics.

        Args:
            transaction: Transaction to modify
            rule: Rule to apply
        """
        # Apply category
        if rule.category_id:
            transaction.category_id = rule.category_id

        # Rename payee
        if rule.new_payee:
            transaction.payee = rule.new_payee

        # Append to notes
        if rule.notes_append:
            if transaction.notes:
                transaction.notes += f"\n{rule.notes_append}"
            else:
                transaction.notes = rule.notes_append

        # Update rule statistics
        rule.last_matched_at = datetime.utcnow()
        rule.match_count = (rule.match_count or 0) + 1

    def categorize_transactions(
        self,
        user_id: int,
        transactions: List[Transaction],
        overwrite_existing: bool = False
    ) -> Dict[str, int]:
        """
        Apply rules to multiple transactions.

        Args:
            user_id: ID of the user whose rules to use
            transactions: List of transactions to categorize
            overwrite_existing: If True, apply rules even if transaction already has a category

        Returns:
            Dictionary with statistics:
            - categorized: Number of transactions categorized
            - uncategorized: Number of transactions not matching any rule
            - rules_used: Number of distinct rules that matched
        """
        rules = self.get_active_rules(user_id)
        stats = {
            'categorized': 0,
            'uncategorized': 0,
            'rules_matched': set()
        }

        for transaction in transactions:
            # Skip if already categorized (unless overwrite_existing)
            if transaction.category_id and not overwrite_existing:
                continue

            matching_rule = self.evaluate_transaction(transaction, rules)
            if matching_rule:
                self.apply_rule(transaction, matching_rule)
                stats['categorized'] += 1
                stats['rules_matched'].add(matching_rule.id)
            else:
                stats['uncategorized'] += 1

        return {
            'categorized': stats['categorized'],
            'uncategorized': stats['uncategorized'],
            'rules_used': len(stats['rules_matched'])
        }

    def test_rule(
        self,
        rule: CategorizationRule,
        payee: Optional[str] = None,
        description: Optional[str] = None,
        amount: Decimal = Decimal("0"),
        transaction_type: str = "DEBIT"
    ) -> Dict[str, any]:
        """
        Test a rule against sample data without persisting changes.

        Useful for rule preview/testing in the UI.

        Args:
            rule: Rule to test
            payee: Sample payee
            description: Sample description
            amount: Sample amount
            transaction_type: Sample transaction type

        Returns:
            Dictionary with:
            - matches: Boolean indicating if rule matches
            - matched_conditions: List of condition names that matched
            - actions_to_apply: Dictionary of actions that would be applied
        """
        from app.models.transaction import TransactionType
        from datetime import date

        # Create a temporary transaction (not persisted)
        test_transaction = Transaction(
            payee=payee,
            description=description,
            amount=amount,
            type=TransactionType[transaction_type],
            date=date.today()
        )

        matched_conditions = []
        actions_to_apply = {}

        # Check each condition
        if rule.payee_pattern:
            if self._text_matches(payee, rule.payee_pattern, rule.payee_match_type):
                matched_conditions.append(f"Payee matches '{rule.payee_pattern}'")

        if rule.description_pattern:
            if self._text_matches(description, rule.description_pattern, rule.description_match_type):
                matched_conditions.append(f"Description matches '{rule.description_pattern}'")

        if rule.amount_min is not None:
            if amount >= rule.amount_min:
                matched_conditions.append(f"Amount >= {rule.amount_min}")

        if rule.amount_max is not None:
            if amount <= rule.amount_max:
                matched_conditions.append(f"Amount <= {rule.amount_max}")

        if rule.transaction_type:
            if transaction_type == rule.transaction_type:
                matched_conditions.append(f"Type is {rule.transaction_type}")

        # Check if all conditions match
        matches = self._rule_matches(test_transaction, rule)

        # Build actions that would be applied
        if rule.category_id:
            actions_to_apply['category_id'] = rule.category_id

        if rule.new_payee:
            actions_to_apply['payee'] = rule.new_payee

        if rule.notes_append:
            actions_to_apply['notes_append'] = rule.notes_append

        return {
            'matches': matches,
            'matched_conditions': matched_conditions,
            'actions_to_apply': actions_to_apply
        }
