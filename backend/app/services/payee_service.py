from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_
import re

from app.models.payee import Payee
from app.schemas.payee import PayeeCreate, PayeeUpdate
from app.services.payee_icon_service import payee_icon_service


class PayeeService:
    """
    Service for managing Payee entities.

    Handles payee creation, normalization, searching, and usage tracking.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_or_create(
        self,
        user_id: int,
        canonical_name: str,
        default_category_id: Optional[int] = None
    ) -> Payee:
        """
        Get existing payee or create new one.

        This is the primary method used during transaction creation and import.

        Args:
            user_id: User ID who owns the payee
            canonical_name: Raw payee name (will be normalized)
            default_category_id: Optional default category

        Returns:
            Payee entity (existing or newly created)
        """
        # Normalize the name
        normalized_name = self._normalize_payee_name(canonical_name)

        if not normalized_name:
            # If normalization results in empty string, use original (truncated)
            normalized_name = canonical_name.strip()[:200]

        # Try to find existing payee
        payee = self.db.query(Payee).filter(
            Payee.user_id == user_id,
            Payee.canonical_name == normalized_name
        ).first()

        if payee:
            return payee

        # Auto-suggest icon for new payee
        icon_suggestion = payee_icon_service.suggest_icon(normalized_name)
        # Use lower threshold (0.5) for real-world transaction descriptions with store numbers/locations
        logo_url = (
            icon_suggestion.get("icon_value")
            if icon_suggestion.get("confidence", 0) >= 0.5
            else None
        )

        # Create new payee with auto-suggested icon
        payee = Payee(
            user_id=user_id,
            canonical_name=normalized_name,
            default_category_id=default_category_id,
            logo_url=logo_url,
            transaction_count=0
        )
        self.db.add(payee)
        self.db.commit()
        self.db.refresh(payee)

        return payee

    def increment_usage(self, payee_id: int) -> None:
        """
        Update transaction_count and last_used_at statistics.

        Args:
            payee_id: ID of payee to update
        """
        payee = self.db.query(Payee).filter(Payee.id == payee_id).first()
        if payee:
            payee.transaction_count += 1
            payee.last_used_at = datetime.utcnow()
            self.db.commit()

    def search_payees(
        self,
        user_id: int,
        query: str,
        limit: int = 10
    ) -> List[Payee]:
        """
        Search payees for autocomplete.

        Ranks by:
        1. Exact name match first
        2. Starts with query
        3. Contains query
        4. Within each group, by usage frequency and recency

        Args:
            user_id: User ID to search within
            query: Search query string
            limit: Maximum number of results

        Returns:
            List of matching Payee entities (with default_category eager loaded)
        """
        query_upper = query.upper()

        # Build the search query with eager loading of default_category
        db_query = self.db.query(Payee).options(
            joinedload(Payee.default_category)
        ).filter(Payee.user_id == user_id)

        if query:
            # Search in canonical_name (case-insensitive)
            db_query = db_query.filter(
                func.upper(Payee.canonical_name).like(f"%{query_upper}%")
            )

        # Order by:
        # 1. Exact match first
        # 2. Starts with query
        # 3. Transaction count (descending)
        # 4. Last used (descending)
        db_query = db_query.order_by(
            # Exact match first
            (func.upper(Payee.canonical_name) == query_upper).desc(),
            # Starts with query second
            func.upper(Payee.canonical_name).startswith(query_upper).desc(),
            # Then by usage
            Payee.transaction_count.desc(),
            Payee.last_used_at.desc().nullslast()
        )

        return db_query.limit(limit).all()

    def update_default_category(
        self,
        payee_id: int,
        category_id: Optional[int]
    ) -> Optional[Payee]:
        """
        Learn default category from user behavior.

        Args:
            payee_id: ID of payee to update
            category_id: New default category ID (or None to clear)

        Returns:
            Updated Payee or None if not found
        """
        payee = self.db.query(Payee).filter(Payee.id == payee_id).first()
        if payee:
            payee.default_category_id = category_id
            self.db.commit()
            self.db.refresh(payee)
        return payee

    def get_by_id(self, payee_id: int, user_id: int) -> Optional[Payee]:
        """
        Get payee by ID (with user ownership check).

        Args:
            payee_id: ID of payee
            user_id: User ID who should own the payee

        Returns:
            Payee or None if not found or not owned by user
        """
        return self.db.query(Payee).filter(
            Payee.id == payee_id,
            Payee.user_id == user_id
        ).first()

    def get_all(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Payee]:
        """
        Get all payees for a user.

        Args:
            user_id: User ID
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return

        Returns:
            List of Payee entities (with default_category eager loaded)
        """
        return self.db.query(Payee).options(
            joinedload(Payee.default_category)
        ).filter(
            Payee.user_id == user_id
        ).order_by(
            Payee.transaction_count.desc(),
            Payee.last_used_at.desc().nullslast(),
            Payee.canonical_name
        ).offset(skip).limit(limit).all()

    def create(
        self,
        user_id: int,
        payee_data: PayeeCreate
    ) -> Payee:
        """
        Create a new payee explicitly.

        Note: Uses get_or_create to avoid duplicates, then updates with additional metadata.

        Args:
            user_id: User ID who owns the payee
            payee_data: Payee creation data

        Returns:
            Created Payee (existing or new)
        """
        # Use get_or_create to find or create the basic payee
        payee = self.get_or_create(
            user_id=user_id,
            canonical_name=payee_data.canonical_name,
            default_category_id=payee_data.default_category_id
        )

        # Update with additional metadata if provided
        update_data = payee_data.model_dump(exclude_unset=True, exclude={'canonical_name', 'default_category_id'})
        if update_data:
            for field, value in update_data.items():
                setattr(payee, field, value)
            self.db.commit()
            self.db.refresh(payee)

        return payee

    def update(
        self,
        payee_id: int,
        user_id: int,
        payee_data: PayeeUpdate
    ) -> Optional[Payee]:
        """
        Update payee metadata.

        Args:
            payee_id: ID of payee to update
            user_id: User ID (for ownership check)
            payee_data: Updated payee data

        Returns:
            Updated Payee or None if not found/not owned
        """
        payee = self.get_by_id(payee_id, user_id)
        if not payee:
            return None

        update_data = payee_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(payee, field, value)

        self.db.commit()
        self.db.refresh(payee)
        return payee

    def delete(self, payee_id: int, user_id: int) -> bool:
        """
        Delete a payee.

        Note: This sets transactions.payee_id to NULL (ON DELETE SET NULL).

        Args:
            payee_id: ID of payee to delete
            user_id: User ID (for ownership check)

        Returns:
            True if deleted, False if not found/not owned
        """
        payee = self.get_by_id(payee_id, user_id)
        if not payee:
            return False

        self.db.delete(payee)
        self.db.commit()
        return True

    def _normalize_payee_name(self, text: str) -> str:
        """
        Normalize payee string to canonical name.

        Normalization rules:
        - Title case for consistency
        - Remove store numbers (#1234)
        - Remove transaction IDs (long numbers at start/end)
        - Strip payment processor prefixes (SQ *, TST *, PAYPAL *)
        - Truncate to 200 chars

        Args:
            text: Raw payee text

        Returns:
            Normalized canonical name
        """
        if not text:
            return ""

        text = text.strip()

        # Remove common prefixes
        prefixes_to_remove = [
            r'^DEBIT\s+CARD\s+PURCHASE\s*-?\s*',
            r'^CREDIT\s+CARD\s+PURCHASE\s*-?\s*',
            r'^POS\s+PURCHASE\s*-?\s*',
            r'^PURCHASE\s+AUTHORIZED\s+ON\s+\d{2}/\d{2}\s+',
            r'^XX\d+\s+',  # Transaction ID like XX7800
            r'^\d{4,}\s+',  # Long number at start
            r'^SQ\s*\*\s*',  # Square payments
            r'^TST\s*\*\s*',  # Toast payments
            r'^PAYPAL\s*\*\s*',  # PayPal
        ]

        for prefix_pattern in prefixes_to_remove:
            text = re.sub(prefix_pattern, '', text, flags=re.IGNORECASE)

        # Remove common suffixes
        suffixes_to_remove = [
            r'\s+STORE\s*#?\d+$',  # Store number with "STORE" keyword (do this first)
            r'\s+\d{1,2}/\d{1,2}$',  # Date like 8/18
            r'\s+#\d+$',  # Store number
            r'\s+\.\.\.\d+$',  # ...123456 format
            r'\s+\d{10,}$',  # Long number at end
            r'\s+(INC|LLC|CORP|CO|LTD)\.?$',  # Company suffixes
            r'\s+CHRG\s+SVCS$',
            r'\s+HTTPS?://.*$',  # Remove URLs
            r'\s+HTTPS?:/.*$',  # Remove partial URLs (malformed)
            r'\s+WWW\..*$',  # Remove web addresses
            r'\s+[A-Z0-9]+\.COM$',  # Remove .com domains
            r'\s+[A-Z0-9]+\.NET$',  # Remove .net domains
            r'\s+[A-Z0-9]+\.ORG$',  # Remove .org domains
            # Remove common city suffixes (usually at end after business name)
            r'\s+(AUSTIN|LEANDER|CEDAR PARK|GEORGETOWN|ROUND ROCK)$',
        ]

        for suffix_pattern in suffixes_to_remove:
            text = re.sub(suffix_pattern, '', text, flags=re.IGNORECASE)

        # Remove city/location suffixes if they duplicate the merchant name
        # For patterns like "CS AUSTIN CAFE AUSTIN" -> "CS AUSTIN CAFE"
        # or "MAIDS AND MOORE MAIDSANDMOORE" -> "MAIDS AND MOORE"
        words = text.split()
        if len(words) > 2:
            # Check if last word appears earlier (case-insensitive)
            last_word_upper = words[-1].upper()
            for i in range(len(words) - 1):
                if words[i].upper() == last_word_upper:
                    # Remove the duplicate at the end
                    text = ' '.join(words[:-1])
                    break

            # Also check if last word is a concatenation of earlier words (no spaces)
            # e.g., "MAIDS AND MOORE MAIDSANDMOORE" -> check if "MAIDSANDMOORE" == "MAIDSANDMOORE"
            last_word = words[-1]
            first_words_concatenated = ''.join(words[:-1]).upper()
            if last_word.upper() == first_words_concatenated:
                text = ' '.join(words[:-1])

        # Clean up extra whitespace
        text = ' '.join(text.split())

        # Title case for consistency
        text = text.title()

        # Truncate to 200 chars
        return text[:200]

    def get_transactions(
        self,
        payee_id: int,
        user_id: int,
        limit: int = 50
    ) -> List[dict]:
        """
        Get recent transactions for a payee.

        Args:
            payee_id: ID of payee
            user_id: User ID (for ownership check)
            limit: Maximum number of transactions to return

        Returns:
            List of transaction dicts with account and category names
        """
        from app.models.transaction import Transaction
        from app.models.account import Account
        from app.models.category import Category

        # Verify payee exists and belongs to user
        payee = self.get_by_id(payee_id, user_id)
        if not payee:
            return []

        # Query transactions for this payee
        transactions = self.db.query(Transaction).options(
            joinedload(Transaction.account),
            joinedload(Transaction.category)
        ).filter(
            Transaction.payee_id == payee_id,
            Transaction.user_id == user_id
        ).order_by(
            Transaction.date.desc(),
            Transaction.created_at.desc()
        ).limit(limit).all()

        # Build response
        results = []
        for txn in transactions:
            results.append({
                "id": txn.id,
                "date": txn.date,
                "amount": txn.amount,
                "type": txn.type.value,
                "account_id": txn.account_id,
                "account_name": txn.account.name if txn.account else "Unknown",
                "category_id": txn.category_id,
                "category_name": txn.category.name if txn.category else None,
                "description": txn.description
            })

        return results

    def get_stats(self, payee_id: int, user_id: int) -> Optional[dict]:
        """
        Get spending statistics for a payee.

        Args:
            payee_id: ID of payee
            user_id: User ID (for ownership check)

        Returns:
            Dict with spending statistics or None if payee not found
        """
        from app.models.transaction import Transaction, TransactionType
        from datetime import date
        from decimal import Decimal

        # Verify payee exists and belongs to user
        payee = self.get_by_id(payee_id, user_id)
        if not payee:
            return None

        # Get current month and year
        today = date.today()
        first_of_month = date(today.year, today.month, 1)
        first_of_year = date(today.year, 1, 1)

        # Base query for this payee's transactions
        base_query = self.db.query(Transaction).filter(
            Transaction.payee_id == payee_id,
            Transaction.user_id == user_id
        )

        # Get all transactions to calculate stats
        all_transactions = base_query.all()

        if not all_transactions:
            return {
                "total_spent_all_time": Decimal("0.00"),
                "total_spent_this_month": Decimal("0.00"),
                "total_spent_this_year": Decimal("0.00"),
                "total_income_all_time": Decimal("0.00"),
                "average_transaction_amount": None,
                "transaction_count": 0,
                "first_transaction_date": None,
                "last_transaction_date": None
            }

        # Calculate stats
        total_spent = Decimal("0.00")
        total_income = Decimal("0.00")
        total_this_month = Decimal("0.00")
        total_this_year = Decimal("0.00")
        dates = []

        for txn in all_transactions:
            dates.append(txn.date)

            if txn.type == TransactionType.DEBIT:
                total_spent += txn.amount
                if txn.date >= first_of_month:
                    total_this_month += txn.amount
                if txn.date >= first_of_year:
                    total_this_year += txn.amount
            elif txn.type == TransactionType.CREDIT:
                total_income += txn.amount

        transaction_count = len(all_transactions)
        total_amount = total_spent + total_income
        avg_amount = total_amount / transaction_count if transaction_count > 0 else None

        return {
            "total_spent_all_time": total_spent,
            "total_spent_this_month": total_this_month,
            "total_spent_this_year": total_this_year,
            "total_income_all_time": total_income,
            "average_transaction_amount": avg_amount,
            "transaction_count": transaction_count,
            "first_transaction_date": min(dates) if dates else None,
            "last_transaction_date": max(dates) if dates else None
        }

    # ========================================================================
    # Pattern Management Methods
    # ========================================================================

    def get_patterns(
        self,
        payee_id: int,
        user_id: int
    ) -> List:
        """
        Get all matching patterns for a payee.

        Args:
            payee_id: ID of payee
            user_id: User ID (for ownership check)

        Returns:
            List of PayeeMatchingPattern entities
        """
        from app.models.payee_matching_pattern import PayeeMatchingPattern

        # Verify payee exists and belongs to user
        payee = self.get_by_id(payee_id, user_id)
        if not payee:
            return []

        return self.db.query(PayeeMatchingPattern).filter(
            PayeeMatchingPattern.payee_id == payee_id,
            PayeeMatchingPattern.user_id == user_id
        ).order_by(
            PayeeMatchingPattern.confidence_score.desc(),
            PayeeMatchingPattern.match_count.desc()
        ).all()

    def create_pattern(
        self,
        payee_id: int,
        user_id: int,
        pattern_type: str,
        pattern_value: str,
        confidence_score: float = 0.80
    ):
        """
        Create a new matching pattern for a payee.

        Args:
            payee_id: ID of payee
            user_id: User ID (for ownership check)
            pattern_type: Type of pattern (description_contains, exact_match, etc.)
            pattern_value: The pattern text to match
            confidence_score: Initial confidence score (0.0 to 1.0)

        Returns:
            Created PayeeMatchingPattern or None if payee not found
        """
        from app.models.payee_matching_pattern import PayeeMatchingPattern
        from decimal import Decimal

        # Verify payee exists and belongs to user
        payee = self.get_by_id(payee_id, user_id)
        if not payee:
            return None

        # Check if pattern already exists
        existing = self.db.query(PayeeMatchingPattern).filter(
            PayeeMatchingPattern.payee_id == payee_id,
            PayeeMatchingPattern.pattern_type == pattern_type,
            PayeeMatchingPattern.pattern_value == pattern_value
        ).first()

        if existing:
            # Update existing pattern
            existing.confidence_score = Decimal(str(confidence_score))
            self.db.commit()
            self.db.refresh(existing)
            return existing

        # Create new pattern
        pattern = PayeeMatchingPattern(
            payee_id=payee_id,
            user_id=user_id,
            pattern_type=pattern_type,
            pattern_value=pattern_value,
            confidence_score=Decimal(str(confidence_score)),
            source='user_created',
            match_count=0
        )
        self.db.add(pattern)
        self.db.commit()
        self.db.refresh(pattern)
        return pattern

    def get_pattern_by_id(
        self,
        pattern_id: int,
        user_id: int
    ):
        """
        Get a pattern by ID with user ownership check.

        Args:
            pattern_id: ID of pattern
            user_id: User ID (for ownership check)

        Returns:
            PayeeMatchingPattern or None if not found/not owned
        """
        from app.models.payee_matching_pattern import PayeeMatchingPattern

        return self.db.query(PayeeMatchingPattern).filter(
            PayeeMatchingPattern.id == pattern_id,
            PayeeMatchingPattern.user_id == user_id
        ).first()

    def update_pattern(
        self,
        pattern_id: int,
        user_id: int,
        pattern_type: Optional[str] = None,
        pattern_value: Optional[str] = None,
        confidence_score: Optional[float] = None
    ):
        """
        Update a pattern's fields.

        Args:
            pattern_id: ID of pattern
            user_id: User ID (for ownership check)
            pattern_type: Optional new pattern type
            pattern_value: Optional new pattern value
            confidence_score: Optional new confidence score

        Returns:
            Updated PayeeMatchingPattern or None if not found
        """
        from decimal import Decimal

        pattern = self.get_pattern_by_id(pattern_id, user_id)
        if not pattern:
            return None

        if pattern_type is not None:
            pattern.pattern_type = pattern_type
        if pattern_value is not None:
            pattern.pattern_value = pattern_value
        if confidence_score is not None:
            pattern.confidence_score = Decimal(str(confidence_score))

        self.db.commit()
        self.db.refresh(pattern)
        return pattern

    def delete_pattern(self, pattern_id: int, user_id: int) -> bool:
        """
        Delete a pattern.

        Args:
            pattern_id: ID of pattern
            user_id: User ID (for ownership check)

        Returns:
            True if deleted, False if not found/not owned
        """
        pattern = self.get_pattern_by_id(pattern_id, user_id)
        if not pattern:
            return False

        self.db.delete(pattern)
        self.db.commit()
        return True

    def test_pattern(
        self,
        pattern_type: str,
        pattern_value: str,
        description: str
    ) -> dict:
        """
        Test if a pattern matches a given description.

        Args:
            pattern_type: Type of pattern
            pattern_value: The pattern text
            description: Transaction description to test against

        Returns:
            Dict with match result and details
        """
        import re
        from difflib import SequenceMatcher

        matches = False
        match_details = None

        if pattern_type == "description_contains":
            # Case-insensitive substring search
            matches = pattern_value.upper() in description.upper()
            if matches:
                match_details = f"Found '{pattern_value}' in description"
            else:
                match_details = f"'{pattern_value}' not found in description"

        elif pattern_type == "exact_match":
            # Extract payee name first, then compare
            from app.services.payee_extraction_service import PayeeExtractionService
            extraction_service = PayeeExtractionService()
            extracted_name, _ = extraction_service.extract_payee_name(description)
            matches = extracted_name.upper() == pattern_value.upper()
            if matches:
                match_details = f"Exact match: extracted '{extracted_name}'"
            else:
                match_details = f"No match: extracted '{extracted_name}' vs pattern '{pattern_value}'"

        elif pattern_type == "fuzzy_match_base":
            # Levenshtein similarity
            from app.services.payee_extraction_service import PayeeExtractionService
            extraction_service = PayeeExtractionService()
            extracted_name, _ = extraction_service.extract_payee_name(description)

            ratio = SequenceMatcher(
                None,
                pattern_value.upper(),
                extracted_name.upper()
            ).ratio()

            matches = ratio >= 0.80
            match_details = f"Similarity: {ratio:.1%} (threshold: 80%)"

        elif pattern_type == "description_regex":
            try:
                matches = bool(re.search(pattern_value, description, re.IGNORECASE))
                if matches:
                    match_details = f"Regex matched"
                else:
                    match_details = f"Regex did not match"
            except re.error as e:
                matches = False
                match_details = f"Invalid regex: {str(e)}"

        else:
            match_details = f"Unknown pattern type: {pattern_type}"

        return {
            "matches": matches,
            "pattern_type": pattern_type,
            "pattern_value": pattern_value,
            "description": description,
            "match_details": match_details
        }
