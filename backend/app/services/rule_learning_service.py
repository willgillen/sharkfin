from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from collections import defaultdict, Counter
from decimal import Decimal
from dataclasses import dataclass

from app.models.transaction import Transaction
from app.models.categorization_rule import CategorizationRule
from app.models.category import Category


@dataclass
class RuleSuggestion:
    """Represents a suggested categorization rule based on user behavior."""

    suggested_rule_name: str
    payee_pattern: Optional[str] = None
    payee_match_type: Optional[str] = None
    description_pattern: Optional[str] = None
    description_match_type: Optional[str] = None
    amount_min: Optional[Decimal] = None
    amount_max: Optional[Decimal] = None
    transaction_type: Optional[str] = None
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    confidence_score: float = 0.0
    match_count: int = 0
    sample_transactions: List[int] = None  # Transaction IDs

    def __post_init__(self):
        if self.sample_transactions is None:
            self.sample_transactions = []


class RuleLearningService:
    """
    Service for analyzing user transaction categorization patterns
    and suggesting automation rules.

    Learns from user behavior to recommend categorization rules that
    can be approved and enabled by the user.
    """

    def __init__(self, db: Session):
        self.db = db

    def analyze_user_patterns(
        self,
        user_id: int,
        min_occurrences: int = 3,
        min_confidence: float = 0.7
    ) -> List[RuleSuggestion]:
        """
        Analyze user's transaction categorization patterns and suggest rules.

        Args:
            user_id: ID of the user
            min_occurrences: Minimum number of similar transactions to suggest a rule
            min_confidence: Minimum confidence score (0.0 to 1.0) for suggestions

        Returns:
            List of rule suggestions sorted by confidence score descending
        """
        # Get all categorized transactions for user
        transactions = self.db.query(Transaction).filter(
            and_(
                Transaction.user_id == user_id,
                Transaction.category_id.isnot(None)  # Only categorized transactions
            )
        ).all()

        if len(transactions) < min_occurrences:
            return []

        # Get existing rules to avoid duplicates
        existing_rules = self.db.query(CategorizationRule).filter(
            CategorizationRule.user_id == user_id
        ).all()

        # Group transactions by payee pattern
        payee_patterns = self._group_by_payee(transactions)

        suggestions = []

        for payee_key, txn_list in payee_patterns.items():
            if len(txn_list) < min_occurrences:
                continue

            # Skip if rule already exists for this pattern
            if self._pattern_already_exists(payee_key, existing_rules):
                continue

            # Analyze pattern
            suggestion = self._analyze_pattern(txn_list, payee_key)

            if suggestion and suggestion.confidence_score >= min_confidence:
                suggestions.append(suggestion)

        # Sort by confidence score descending
        suggestions.sort(key=lambda s: s.confidence_score, reverse=True)

        return suggestions

    def _group_by_payee(self, transactions: List[Transaction]) -> Dict[str, List[Transaction]]:
        """
        Group transactions by payee pattern.

        Detects common substrings in payee names to group similar transactions.
        """
        groups = defaultdict(list)

        for txn in transactions:
            if not txn.payee:
                continue

            # Normalize payee name (uppercase, remove numbers for grouping)
            payee_normalized = self._normalize_payee(txn.payee)

            # Group by exact match first
            groups[payee_normalized].append(txn)

        # Merge groups with common substrings
        merged_groups = self._merge_similar_groups(groups)

        return merged_groups

    def _normalize_payee(self, payee: str) -> str:
        """
        Normalize payee name for pattern matching.

        Removes transaction-specific details like store numbers, transaction IDs.
        """
        import re

        # Convert to uppercase
        normalized = payee.upper().strip()

        # Remove common suffixes with numbers
        normalized = re.sub(r'\s*#\d+', '', normalized)  # Remove #1234
        normalized = re.sub(r'\s*STORE\s*#?\d+', '', normalized)  # Remove STORE #1234
        normalized = re.sub(r'\*[A-Z0-9]+$', '', normalized)  # Remove *123ABC suffix

        return normalized.strip()

    def _merge_similar_groups(
        self,
        groups: Dict[str, List[Transaction]]
    ) -> Dict[str, List[Transaction]]:
        """
        Merge groups that share common substrings.

        For example: "SAFEWAY STORE", "SAFEWAY #1234", "SAFEWAY GAS" -> "SAFEWAY"
        """
        if len(groups) <= 1:
            return groups

        merged = {}

        for key, txns in groups.items():
            # Find if this key shares a common substring with existing merged groups
            merged_into = None

            for merged_key in list(merged.keys()):
                common = self._find_common_substring([key, merged_key])
                # If common substring is significant (>= 4 chars), merge
                if common and len(common) >= 4:
                    merged_into = merged_key
                    break

            if merged_into:
                # Merge into existing group
                merged[merged_into].extend(txns)
                # Update key to be the shorter/cleaner common substring
                if len(common) < len(merged_into):
                    merged[common] = merged.pop(merged_into)
            else:
                merged[key] = txns

        return merged

    def _find_common_substring(self, strings: List[str]) -> Optional[str]:
        """
        Find longest common substring among a list of strings.

        Returns the longest common substring, or None if no significant match.
        """
        if not strings or len(strings) < 2:
            return strings[0] if strings else None

        # Start with first string
        common = strings[0]

        for s in strings[1:]:
            # Find longest common substring between common and s
            new_common = ""
            for i in range(len(common)):
                for j in range(len(common) - i):
                    substring = common[i:i + j + 1]
                    if substring in s and len(substring) > len(new_common):
                        new_common = substring

            common = new_common

            if not common or len(common) < 4:
                return None

        return common.strip()

    def _pattern_already_exists(
        self,
        payee_pattern: str,
        existing_rules: List[CategorizationRule]
    ) -> bool:
        """
        Check if a similar rule already exists.
        """
        payee_lower = payee_pattern.lower()

        for rule in existing_rules:
            if rule.payee_pattern:
                if payee_lower in rule.payee_pattern.lower() or rule.payee_pattern.lower() in payee_lower:
                    return True

        return False

    def _analyze_pattern(
        self,
        transactions: List[Transaction],
        payee_pattern: str
    ) -> Optional[RuleSuggestion]:
        """
        Analyze a group of transactions and create a rule suggestion.
        """
        if not transactions:
            return None

        # Extract categories
        categories = [txn.category_id for txn in transactions if txn.category_id]

        if not categories:
            return None

        # Find most common category
        category_counts = Counter(categories)
        most_common_category, match_count = category_counts.most_common(1)[0]

        # Calculate confidence based on consistency
        consistency = match_count / len(categories)

        # Get category name
        category = self.db.query(Category).filter(
            Category.id == most_common_category
        ).first()

        category_name = category.name if category else "Unknown"

        # Determine match type
        # Check if all payees are identical
        unique_payees = set(txn.payee for txn in transactions if txn.payee)

        if len(unique_payees) == 1:
            match_type = "exact"
            pattern = list(unique_payees)[0]
        else:
            match_type = "contains"
            pattern = payee_pattern

        # Analyze amount range (optional)
        amounts = [txn.amount for txn in transactions if txn.amount]
        amount_min = None
        amount_max = None

        if amounts:
            amount_variance = (max(amounts) - min(amounts)) / max(amounts) if max(amounts) > 0 else 0
            # Only suggest amount range if variance is low (< 30%)
            if amount_variance < 0.3:
                amount_min = min(amounts) * Decimal("0.9")  # 10% buffer
                amount_max = max(amounts) * Decimal("1.1")

        # Analyze transaction type
        transaction_types = [txn.type.name for txn in transactions]
        type_consistency = Counter(transaction_types).most_common(1)[0][1] / len(transaction_types)

        transaction_type = None
        if type_consistency >= 0.9:  # 90% consistency
            transaction_type = Counter(transaction_types).most_common(1)[0][0]

        # Calculate final confidence score
        # Factors: consistency, frequency, recency
        confidence = self._calculate_confidence_score(
            consistency=consistency,
            frequency=len(transactions),
            transactions=transactions
        )

        # Generate suggested rule name
        rule_name = self._generate_rule_name(pattern, category_name)

        # Get sample transaction IDs
        sample_ids = [txn.id for txn in transactions[:5]]

        return RuleSuggestion(
            suggested_rule_name=rule_name,
            payee_pattern=pattern,
            payee_match_type=match_type,
            amount_min=amount_min,
            amount_max=amount_max,
            transaction_type=transaction_type,
            category_id=most_common_category,
            category_name=category_name,
            confidence_score=confidence,
            match_count=match_count,
            sample_transactions=sample_ids
        )

    def _calculate_confidence_score(
        self,
        consistency: float,
        frequency: int,
        transactions: List[Transaction]
    ) -> float:
        """
        Calculate confidence score for a rule suggestion.

        Factors:
        - Consistency: How consistently the same category is used
        - Frequency: Number of transactions matching the pattern
        - Recency: How recent the transactions are

        Returns:
            Confidence score between 0.0 and 1.0
        """
        # Base score from consistency (most important factor)
        score = consistency * 0.7

        # Frequency bonus (more transactions = higher confidence)
        frequency_score = min(frequency / 10.0, 1.0) * 0.2
        score += frequency_score

        # Recency bonus (recent transactions = higher confidence)
        from datetime import date, timedelta
        recent_threshold = date.today() - timedelta(days=90)
        recent_count = sum(1 for txn in transactions if txn.date >= recent_threshold)
        recency_score = (recent_count / len(transactions)) * 0.1
        score += recency_score

        return min(score, 1.0)

    def _calculate_consistency(self, categories: List[int]) -> float:
        """
        Calculate consistency of categorization.

        Returns proportion of transactions with the most common category.
        """
        if not categories:
            return 0.0

        most_common_count = Counter(categories).most_common(1)[0][1]
        return most_common_count / len(categories)

    def _generate_rule_name(self, payee_pattern: str, category_name: str) -> str:
        """
        Generate a human-readable rule name.

        Example: "Auto: SAFEWAY -> Groceries"
        """
        # Capitalize first letter of each word in payee
        payee_display = payee_pattern.title()

        # Limit length
        if len(payee_display) > 30:
            payee_display = payee_display[:27] + "..."

        return f"Auto: {payee_display} → {category_name}"
