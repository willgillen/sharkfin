from typing import List, Dict, Optional, Set
from collections import defaultdict, Counter
import re
from decimal import Decimal
from app.services.payee_service import PayeeService

class SmartRuleSuggestion:
    """Represents a smart rule suggestion during import."""

    def __init__(
        self,
        suggested_name: str,
        payee_pattern: str,
        payee_match_type: str,
        matching_rows: List[int],
        sample_descriptions: List[str],
        confidence: float,
        detected_merchant: Optional[str] = None
    ):
        self.suggested_name = suggested_name
        self.payee_pattern = payee_pattern
        self.payee_match_type = payee_match_type
        self.matching_rows = matching_rows
        self.sample_descriptions = sample_descriptions
        self.confidence = confidence
        self.detected_merchant = detected_merchant


class SmartRuleSuggestionService:
    """
    Service for analyzing import data and suggesting rules intelligently.

    This service examines transaction data from imports and uses pattern
    recognition and merchant detection to suggest useful categorization rules.
    """

    # Common merchant patterns to detect
    MERCHANT_PATTERNS = [
        # Online retailers
        (r'\bAMAZON\b', 'Amazon', 'online_retail'),
        (r'\bWALMART\b', 'Walmart', 'retail'),
        (r'\bTARGET\b', 'Target', 'retail'),
        (r'\bCOSTCO\b', 'Costco', 'wholesale'),

        # Grocery stores
        (r'\bWHOLE\s*FOODS\b', 'Whole Foods', 'grocery'),
        (r'\bH-E-B\b', 'H-E-B', 'grocery'),
        (r'\bSAFEWAY\b', 'Safeway', 'grocery'),
        (r'\bKROGER\b', 'Kroger', 'grocery'),
        (r'\bPUBLIX\b', 'Publix', 'grocery'),
        (r'\bTRADER\s*JOE', 'Trader Joe\'s', 'grocery'),
        (r'\bRANDALLS\b', 'Randalls', 'grocery'),

        # Gas stations
        (r'\bSHELL\b', 'Shell', 'gas'),
        (r'\bCHEVRON\b', 'Chevron', 'gas'),
        (r'\bEXXON\b', 'Exxon', 'gas'),
        (r'\bMOBIL\b', 'Mobil', 'gas'),
        (r'\bBP\b', 'BP', 'gas'),
        (r'\b76\b', '76', 'gas'),

        # Restaurants & Fast Food
        (r'\bSTARBUCKS\b', 'Starbucks', 'restaurant'),
        (r'\bMCDONALD', 'McDonald\'s', 'fast_food'),
        (r'\bCHIPOTLE\b', 'Chipotle', 'fast_food'),
        (r'\bSUBWAY\b', 'Subway', 'fast_food'),
        (r'\bPANERA\b', 'Panera', 'fast_food'),
        (r'\bTACO\s*BELL\b', 'Taco Bell', 'fast_food'),
        (r'\bTORCHY', 'Torchy\'s', 'restaurant'),
        (r'\bCHUY', 'Chuy\'s', 'restaurant'),

        # Utilities & Telecom
        (r'\bPG&E\b', 'PG&E', 'utilities'),
        (r'\bATT\*?\s*BILL', 'AT&T', 'utilities'),
        (r'\bAT&T\b', 'AT&T', 'utilities'),
        (r'\bVERIZON\b', 'Verizon', 'utilities'),
        (r'\bCOMCAST\b', 'Comcast', 'utilities'),
        (r'\bATMOS\s*ENERGY\b', 'Atmos Energy', 'utilities'),

        # Subscriptions & Tech
        (r'\bNETFLIX\b', 'Netflix', 'subscription'),
        (r'\bSPOTIFY\b', 'Spotify', 'subscription'),
        (r'\bAPPLE\.COM\b', 'Apple', 'subscription'),
        (r'\bGOOGLE\b', 'Google', 'subscription'),
        (r'\bANTHROPIC\b', 'Anthropic', 'subscription'),
        (r'\bCLAUDE\.AI\b', 'Claude AI', 'subscription'),
        (r'AWS\.AMAZON\b', 'AWS', 'subscription'),

        # Transportation
        (r'\bUBER\b', 'Uber', 'transportation'),
        (r'\bLYFT\b', 'Lyft', 'transportation'),
        (r'\bHCTRA\b', 'HCTRA Toll Tag', 'transportation'),
    ]

    def __init__(self):
        pass

    def analyze_import_data(
        self,
        transactions: List[Dict],
        min_occurrences: int = 2,
        min_confidence: float = 0.6
    ) -> List[SmartRuleSuggestion]:
        """
        Analyze import transaction data and suggest rules.

        Args:
            transactions: List of transaction dicts with 'description', 'payee', 'amount'
            min_occurrences: Minimum times a pattern must appear
            min_confidence: Minimum confidence score (0.0 to 1.0)

        Returns:
            List of SmartRuleSuggestion objects
        """
        suggestions = []

        # Step 1: Detect known merchants from descriptions
        merchant_suggestions = self._detect_merchants(transactions, min_occurrences)
        suggestions.extend(merchant_suggestions)

        # Step 2: Find common patterns in descriptions/payees
        pattern_suggestions = self._find_common_patterns(transactions, min_occurrences, min_confidence)

        # Filter out patterns already covered by merchant detection
        # Check if patterns match the same transactions (>80% overlap = duplicate)
        for pattern_suggestion in pattern_suggestions:
            is_duplicate = False
            pattern_rows = set(pattern_suggestion.matching_rows)

            for existing_suggestion in suggestions:
                existing_rows = set(existing_suggestion.matching_rows)

                # Calculate overlap: intersection / smaller set
                if len(pattern_rows) > 0 and len(existing_rows) > 0:
                    intersection = len(pattern_rows & existing_rows)
                    smaller_set_size = min(len(pattern_rows), len(existing_rows))
                    overlap_ratio = intersection / smaller_set_size

                    # If >80% of transactions overlap, consider it a duplicate
                    if overlap_ratio > 0.8:
                        is_duplicate = True
                        break

            if not is_duplicate:
                suggestions.append(pattern_suggestion)

        # Step 3: Sort by confidence and number of matches
        suggestions.sort(key=lambda s: (s.confidence, len(s.matching_rows)), reverse=True)

        return suggestions

    def _detect_merchants(
        self,
        transactions: List[Dict],
        min_occurrences: int
    ) -> List[SmartRuleSuggestion]:
        """
        Detect known merchants from transaction descriptions.
        """
        suggestions = []
        merchant_matches = defaultdict(list)

        # Find all transactions matching each merchant pattern
        for idx, txn in enumerate(transactions):
            description = (txn.get('description') or '').upper()
            payee = (txn.get('payee') or '').upper()

            # Check description and payee against known patterns
            text_to_check = f"{description} {payee}"

            for pattern, merchant_name, category_hint in self.MERCHANT_PATTERNS:
                if re.search(pattern, text_to_check, re.IGNORECASE):
                    merchant_matches[merchant_name].append({
                        'index': idx,
                        'description': txn.get('description', ''),
                        'payee': txn.get('payee', ''),
                        'category_hint': category_hint
                    })

        # Create suggestions for merchants that appear enough times
        for merchant_name, matches in merchant_matches.items():
            if len(matches) >= min_occurrences:
                matching_rows = [m['index'] for m in matches]
                sample_descriptions = [m['description'] or m['payee'] for m in matches[:3]]

                # High confidence for known merchants
                confidence = min(0.95, 0.7 + (len(matches) * 0.05))

                suggestion = SmartRuleSuggestion(
                    suggested_name=f"Auto: {merchant_name}",
                    payee_pattern=merchant_name.upper(),
                    payee_match_type="contains",
                    matching_rows=matching_rows,
                    sample_descriptions=sample_descriptions,
                    confidence=confidence,
                    detected_merchant=merchant_name
                )
                suggestions.append(suggestion)

        return suggestions

    def _find_common_patterns(
        self,
        transactions: List[Dict],
        min_occurrences: int,
        min_confidence: float
    ) -> List[SmartRuleSuggestion]:
        """
        Find common patterns in descriptions and payees.

        This handles cases where merchants aren't in our known list.
        Uses PayeeService normalization to group similar payee variations together.
        """
        suggestions = []

        # Use PayeeService normalization to find recurring payees
        payee_service = PayeeService(db=None)  # We only need the normalization method
        normalized_payees = defaultdict(list)

        for idx, txn in enumerate(transactions):
            description = txn.get('description', '')
            payee = txn.get('payee', '')

            # Use the description as the primary source (that's where payee info is in CSV)
            text_to_normalize = description or payee

            if not text_to_normalize or text_to_normalize.strip() == '':
                continue

            # Normalize using PayeeService (same logic as will be used for actual payees)
            normalized = payee_service._normalize_payee_name(text_to_normalize)

            if normalized and len(normalized) >= 3:  # Minimum 3 chars for a valid payee
                normalized_payees[normalized].append({
                    'index': idx,
                    'description': description,
                    'payee': payee,
                    'original': text_to_normalize
                })

        # Create suggestions for patterns that appear frequently
        for normalized_name, matches in normalized_payees.items():
            if len(matches) >= min_occurrences:
                matching_rows = [m['index'] for m in matches]
                sample_descriptions = [m['original'] for m in matches[:3]]

                # Calculate confidence based on frequency
                # Use a more lenient formula: if it appears 3+ times, it's worth suggesting
                # Confidence scales with frequency up to a maximum of 10 occurrences
                confidence = min(1.0, len(matches) / 10) * 0.7 + 0.3  # Range: 0.3 to 1.0

                if confidence >= min_confidence:
                    suggestion = SmartRuleSuggestion(
                        suggested_name=f"Auto: {normalized_name}",
                        payee_pattern=normalized_name,
                        payee_match_type="contains",
                        matching_rows=matching_rows,
                        sample_descriptions=sample_descriptions,
                        confidence=confidence,
                        detected_merchant=normalized_name
                    )
                    suggestions.append(suggestion)

        return suggestions

    def _extract_merchant_name(self, text: str) -> Optional[str]:
        """
        Extract merchant name from transaction description.

        Common formats:
        - "XX7800 AMAZON INC CHRG SVCS 8/18"
        - "DEBIT CARD PURCHASE - STARBUCKS #12345"
        - "SQ *COFFEE SHOP"
        - "TST* RESTAURANT NAME"
        """
        if not text:
            return None

        text = text.upper().strip()

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
            text = re.sub(prefix_pattern, '', text)

        # Remove common suffixes
        suffixes_to_remove = [
            r'\s+\d{1,2}/\d{1,2}$',  # Date like 8/18
            r'\s+#\d+$',  # Store number
            r'\s+STORE\s*#?\d+$',
            r'\s+\d{10,}$',  # Long number at end
            r'\s+(INC|LLC|CORP|CO|LTD)\.?$',  # Company suffixes
            r'\s+CHRG\s+SVCS$',
        ]

        for suffix_pattern in suffixes_to_remove:
            text = re.sub(suffix_pattern, '', text)

        # Extract the first meaningful word/phrase (2-20 characters)
        # Skip single letters and very short words
        words = text.split()

        # Look for the longest meaningful sequence
        merchant_parts = []
        for word in words:
            # Skip very short words, numbers, and common filler words
            if len(word) < 2 or word.isdigit():
                continue
            if word in ['THE', 'AND', 'OF', 'AT', 'IN', 'ON']:
                continue

            merchant_parts.append(word)

            # Stop if we have 2-3 words (usually enough for merchant name)
            if len(merchant_parts) >= 3:
                break

        if merchant_parts:
            merchant_name = ' '.join(merchant_parts)
            # Only return if it's a reasonable length
            if 2 <= len(merchant_name) <= 30:
                return merchant_name

        return None

    def _calculate_pattern_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two text strings.

        Uses simple word overlap for now.
        """
        if not text1 or not text2:
            return 0.0

        words1 = set(text1.upper().split())
        words2 = set(text2.upper().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union) if union else 0.0
