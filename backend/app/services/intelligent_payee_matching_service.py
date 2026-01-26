"""
Intelligent Payee Matching Service

Provides smart payee matching during imports using:
1. Known merchant patterns (known_merchants.json)
2. User's learned patterns (from previous imports)
3. Fuzzy string matching (Levenshtein distance)

Classifies matches into three confidence tiers:
- HIGH_CONFIDENCE (0.85+): Auto-apply with user review option
- LOW_CONFIDENCE (0.70-0.84): Suggest to user for approval
- NO_MATCH (<0.70): New payee needed
"""
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from sqlalchemy.orm import Session
from Levenshtein import ratio
from app.models.payee import Payee
from app.models.payee_matching_pattern import PayeeMatchingPattern
from app.services.payee_extraction_service import PayeeExtractionService


@dataclass
class AlternativeMatch:
    """A potential payee match shown as an alternative to user."""
    payee_id: int
    payee_name: str
    confidence: float


@dataclass
class TransactionPayeeAnalysis:
    """Result of analyzing one transaction for payee matching."""
    transaction_index: int
    original_description: str
    extracted_payee_name: str
    extraction_confidence: float

    # Matching results
    match_type: str  # 'HIGH_CONFIDENCE', 'LOW_CONFIDENCE', 'NO_MATCH'
    matched_payee_id: Optional[int]
    matched_payee_name: Optional[str]
    match_confidence: float
    match_reason: str  # "Known merchant: Uber" or "Pattern match: UBER (92%)"

    # Suggested category (from known merchants or matched payee's default)
    suggested_category: Optional[str] = None

    # Alternatives for user selection
    alternative_matches: List[AlternativeMatch] = None

    def __post_init__(self):
        if self.alternative_matches is None:
            self.alternative_matches = []


class IntelligentPayeeMatchingService:
    """
    Service for intelligently matching transaction descriptions to existing payees.

    Uses a three-tier matching strategy:
    1. Known merchants (0.95 confidence) - From known_merchants.json
    2. Pattern matching (variable confidence) - User's learned patterns
    3. Fuzzy matching (0.70+ confidence) - Levenshtein similarity

    Learning: Creates patterns when users accept matches or create new payees.
    """

    # Confidence thresholds
    HIGH_CONFIDENCE_THRESHOLD = 0.85
    LOW_CONFIDENCE_THRESHOLD = 0.70
    FUZZY_MATCH_THRESHOLD = 0.70

    # Minimum payee name length to consider for matching
    # Short names like "An", "Al" tend to create false positives
    MIN_PAYEE_NAME_LENGTH = 3

    # Minimum pattern value length for description_contains patterns
    # Short patterns like "LS", "AN" match too many unrelated transactions
    MIN_PATTERN_VALUE_LENGTH = 4

    def __init__(self, db: Session):
        self.db = db
        self.extraction_service = PayeeExtractionService(db)
        self._pattern_cache = {}  # Cache patterns during import analysis

    def analyze_transactions_for_import(
        self,
        user_id: int,
        transactions: List[Dict]
    ) -> List[TransactionPayeeAnalysis]:
        """
        Analyze ALL transactions from import and match to existing payees.

        For each transaction:
        1. Extract payee name using PayeeExtractionService
        2. Check known merchants first (0.95 confidence)
        3. Check user's learned patterns (pattern-based matching)
        4. Fuzzy match to existing payees (Levenshtein >= 0.70)
        5. Classify as HIGH_CONFIDENCE, LOW_CONFIDENCE, or NO_MATCH
        6. Find alternative matches for user selection

        Args:
            user_id: User ID for filtering patterns and payees
            transactions: List of transaction dicts with 'description' and 'payee' fields

        Returns:
            List of TransactionPayeeAnalysis objects, one per transaction
        """
        # Load and cache user's patterns
        self._load_patterns_cache(user_id)

        # Load all user's payees for fuzzy matching
        user_payees = self._get_user_payees(user_id)

        analyses = []

        for idx, txn in enumerate(transactions):
            description = txn.get('description', '')
            payee = txn.get('payee', '')
            text_to_extract = description or payee

            if not text_to_extract or not text_to_extract.strip():
                # No payee information available
                analyses.append(TransactionPayeeAnalysis(
                    transaction_index=idx,
                    original_description=text_to_extract,
                    extracted_payee_name="",
                    extraction_confidence=0.0,
                    match_type='NO_MATCH',
                    matched_payee_id=None,
                    matched_payee_name=None,
                    match_confidence=0.0,
                    match_reason="No description available",
                    alternative_matches=[]
                ))
                continue

            # Step 1: Extract payee name with category suggestion
            extracted_name, extraction_confidence, suggested_category = \
                self.extraction_service.extract_payee_name_with_category(text_to_extract)

            # Step 2: Try pattern matching (includes known merchants)
            pattern_match = self._match_against_patterns(
                user_id,
                text_to_extract,
                extracted_name
            )

            # Step 3: Try fuzzy matching if no pattern match
            fuzzy_matches = []
            if not pattern_match:
                fuzzy_matches = self._fuzzy_match_to_payees(
                    user_payees,
                    extracted_name,
                    threshold=self.FUZZY_MATCH_THRESHOLD
                )

            # Determine best match and confidence tier
            if pattern_match:
                matched_payee, confidence, reason = pattern_match
                match_type = self._classify_confidence(confidence)
                matched_payee_id = matched_payee.id
                matched_payee_name = matched_payee.canonical_name

                # Use matched payee's default category if available
                if matched_payee.default_category:
                    suggested_category = matched_payee.default_category.name

                # Find alternatives (other patterns or fuzzy matches)
                alternatives = self._find_alternative_matches(
                    user_payees,
                    extracted_name,
                    exclude_payee_id=matched_payee_id
                )

            elif fuzzy_matches:
                # Use best fuzzy match
                matched_payee, confidence = fuzzy_matches[0]
                match_type = self._classify_confidence(confidence)
                matched_payee_id = matched_payee.id
                matched_payee_name = matched_payee.canonical_name
                reason = f"Similar to: {matched_payee_name} ({int(confidence * 100)}%)"

                # Use matched payee's default category if available
                if matched_payee.default_category:
                    suggested_category = matched_payee.default_category.name

                # Rest of fuzzy matches are alternatives
                alternatives = [
                    AlternativeMatch(p.id, p.canonical_name, conf)
                    for p, conf in fuzzy_matches[1:4]  # Top 3 alternatives
                ]

            else:
                # No match found - suggested_category from known merchants is already set
                match_type = 'NO_MATCH'
                matched_payee_id = None
                matched_payee_name = None
                confidence = 0.0
                reason = f"New payee suggested: {extracted_name}"
                alternatives = []

            analyses.append(TransactionPayeeAnalysis(
                transaction_index=idx,
                original_description=text_to_extract,
                extracted_payee_name=extracted_name,
                extraction_confidence=extraction_confidence,
                match_type=match_type,
                matched_payee_id=matched_payee_id,
                matched_payee_name=matched_payee_name,
                match_confidence=confidence,
                match_reason=reason,
                suggested_category=suggested_category,
                alternative_matches=alternatives
            ))

        return analyses

    def _load_patterns_cache(self, user_id: int):
        """Load user's patterns into memory cache for fast matching."""
        patterns = self.db.query(PayeeMatchingPattern).filter(
            PayeeMatchingPattern.user_id == user_id
        ).all()

        self._pattern_cache[user_id] = patterns

    def _get_user_payees(self, user_id: int) -> List[Payee]:
        """Get all user's payees for fuzzy matching."""
        return self.db.query(Payee).filter(
            Payee.user_id == user_id
        ).all()

    def _match_against_patterns(
        self,
        user_id: int,
        description: str,
        extracted_name: str
    ) -> Optional[Tuple[Payee, float, str]]:
        """
        Match transaction against user's learned patterns.

        Checks patterns in order of confidence score (highest first).

        Args:
            user_id: User ID
            description: Original transaction description
            extracted_name: Extracted payee name

        Returns:
            Tuple of (matched_payee, confidence, match_reason) or None
        """
        patterns = self._pattern_cache.get(user_id, [])

        # Sort by confidence score descending
        patterns_sorted = sorted(patterns, key=lambda p: p.confidence_score, reverse=True)

        for pattern in patterns_sorted:
            # Skip patterns for payees with very short names - they create false positives
            # e.g., pattern "AN" for payee "An" matches almost everything
            if len(pattern.payee.canonical_name) < self.MIN_PAYEE_NAME_LENGTH:
                continue

            # Skip description_contains patterns with very short values
            # e.g., "LS" matches "MANUELS", "RANDALLS", "TULSA", etc.
            if (pattern.pattern_type == 'description_contains' and
                    len(pattern.pattern_value) < self.MIN_PATTERN_VALUE_LENGTH):
                continue

            matched = False

            if pattern.pattern_type == 'description_contains':
                # Case-insensitive substring match
                if pattern.pattern_value.lower() in description.lower():
                    matched = True

            elif pattern.pattern_type == 'exact_match':
                # Exact match on extracted name
                if pattern.pattern_value.lower() == extracted_name.lower():
                    matched = True

            elif pattern.pattern_type == 'fuzzy_match_base':
                # Fuzzy match using Levenshtein
                similarity = ratio(
                    pattern.pattern_value.lower(),
                    extracted_name.lower()
                )
                if similarity >= 0.80:  # High threshold for pattern-based fuzzy match
                    matched = True

            # TODO: Add description_regex support

            if matched:
                payee = pattern.payee
                confidence = float(pattern.confidence_score)

                # Determine reason
                if pattern.source == 'known_merchant':
                    reason = f"Known merchant: {payee.canonical_name}"
                else:
                    reason = f"Pattern match: {pattern.pattern_value} ({int(confidence * 100)}%)"

                return (payee, confidence, reason)

        return None

    def _fuzzy_match_to_payees(
        self,
        payees: List[Payee],
        extracted_name: str,
        threshold: float = 0.70
    ) -> List[Tuple[Payee, float]]:
        """
        Fuzzy match extracted name to existing payees using Levenshtein distance.

        Args:
            payees: List of user's payees
            extracted_name: Extracted payee name to match
            threshold: Minimum similarity score (0.0-1.0)

        Returns:
            List of (payee, similarity_score) tuples sorted by score descending
        """
        if not extracted_name or len(extracted_name) < 2:
            return []

        matches = []

        for payee in payees:
            # Skip payees with very short names - they create false positives
            # e.g., "An" matching "Amazon" with high similarity
            if len(payee.canonical_name) < self.MIN_PAYEE_NAME_LENGTH:
                continue

            similarity = ratio(
                extracted_name.lower(),
                payee.canonical_name.lower()
            )

            if similarity >= threshold:
                matches.append((payee, similarity))

        # Sort by similarity score descending
        matches.sort(key=lambda x: x[1], reverse=True)

        return matches

    def _classify_confidence(self, confidence: float) -> str:
        """
        Classify confidence score into tier.

        Returns: 'HIGH_CONFIDENCE', 'LOW_CONFIDENCE', or 'NO_MATCH'
        """
        if confidence >= self.HIGH_CONFIDENCE_THRESHOLD:
            return 'HIGH_CONFIDENCE'
        elif confidence >= self.LOW_CONFIDENCE_THRESHOLD:
            return 'LOW_CONFIDENCE'
        else:
            return 'NO_MATCH'

    def _find_alternative_matches(
        self,
        payees: List[Payee],
        extracted_name: str,
        exclude_payee_id: int,
        limit: int = 3
    ) -> List[AlternativeMatch]:
        """
        Find alternative payee matches to show user as options.

        Args:
            payees: List of user's payees
            extracted_name: Extracted payee name
            exclude_payee_id: Payee ID to exclude (primary match)
            limit: Maximum alternatives to return

        Returns:
            List of AlternativeMatch objects
        """
        fuzzy_matches = self._fuzzy_match_to_payees(
            payees,
            extracted_name,
            threshold=0.60  # Lower threshold for alternatives
        )

        alternatives = []
        for payee, confidence in fuzzy_matches:
            if payee.id != exclude_payee_id:
                alternatives.append(AlternativeMatch(
                    payee_id=payee.id,
                    payee_name=payee.canonical_name,
                    confidence=confidence
                ))

            if len(alternatives) >= limit:
                break

        return alternatives

    def create_pattern_from_match(
        self,
        user_id: int,
        payee_id: int,
        description: str,
        pattern_type: str = 'description_contains',
        source: str = 'import_learning'
    ) -> PayeeMatchingPattern:
        """
        Create new matching pattern based on user accepting a match.

        Called when:
        - User accepts a suggested match during import
        - User creates a new payee during import

        Args:
            user_id: User ID
            payee_id: Payee ID to associate pattern with
            description: Original transaction description
            pattern_type: Type of pattern to create
            source: Source of pattern ('import_learning', 'user_created', etc.)

        Returns:
            Created PayeeMatchingPattern
        """
        # Extract core pattern from description
        pattern_value = self._extract_pattern_value(description, pattern_type)

        # Don't create patterns that are too short - they match too broadly
        if (pattern_type == 'description_contains' and
                len(pattern_value) < self.MIN_PATTERN_VALUE_LENGTH):
            # Return None or a minimal pattern object without saving
            # For now, just don't create the pattern
            return None

        # Check if pattern already exists
        existing = self.db.query(PayeeMatchingPattern).filter(
            PayeeMatchingPattern.payee_id == payee_id,
            PayeeMatchingPattern.pattern_type == pattern_type,
            PayeeMatchingPattern.pattern_value == pattern_value
        ).first()

        if existing:
            # Update existing pattern (increment match count, confidence)
            existing.match_count += 1
            existing.confidence_score = min(
                1.0,
                float(existing.confidence_score) + 0.01  # Small confidence boost
            )
            self.db.commit()
            return existing

        # Create new pattern
        pattern = PayeeMatchingPattern(
            payee_id=payee_id,
            user_id=user_id,
            pattern_type=pattern_type,
            pattern_value=pattern_value,
            confidence_score=0.80,  # Starting confidence
            match_count=1,
            source=source
        )

        self.db.add(pattern)
        self.db.commit()
        self.db.refresh(pattern)

        return pattern

    def _extract_pattern_value(self, description: str, pattern_type: str) -> str:
        """
        Extract pattern value from description based on pattern type.

        For 'description_contains': Extract key merchant name
        For 'exact_match': Use full extracted name
        """
        if pattern_type == 'description_contains':
            # Use extraction service to get clean merchant name
            extracted_name, _ = self.extraction_service.extract_payee_name(description)
            # Use uppercase for consistent matching
            return extracted_name.upper()

        elif pattern_type == 'exact_match':
            extracted_name, _ = self.extraction_service.extract_payee_name(description)
            return extracted_name

        else:
            # Default: use description as-is
            return description.strip()
