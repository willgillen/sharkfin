from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
import re

from app.models.payee import Payee
from app.schemas.payee import PayeeCreate, PayeeUpdate


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

        # Create new payee
        payee = Payee(
            user_id=user_id,
            canonical_name=normalized_name,
            default_category_id=default_category_id,
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
            List of matching Payee entities
        """
        query_upper = query.upper()

        # Build the search query
        db_query = self.db.query(Payee).filter(Payee.user_id == user_id)

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
            List of Payee entities
        """
        return self.db.query(Payee).filter(
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

        Note: Prefer get_or_create() to avoid duplicates.

        Args:
            user_id: User ID who owns the payee
            payee_data: Payee creation data

        Returns:
            Created Payee
        """
        # Use get_or_create to avoid duplicates
        return self.get_or_create(
            user_id=user_id,
            canonical_name=payee_data.canonical_name,
            default_category_id=payee_data.default_category_id
        )

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
            r'\s+\d{10,}$',  # Long number at end
            r'\s+(INC|LLC|CORP|CO|LTD)\.?$',  # Company suffixes
            r'\s+CHRG\s+SVCS$',
        ]

        for suffix_pattern in suffixes_to_remove:
            text = re.sub(suffix_pattern, '', text, flags=re.IGNORECASE)

        # Clean up extra whitespace
        text = ' '.join(text.split())

        # Title case for consistency
        text = text.title()

        # Truncate to 200 chars
        return text[:200]
