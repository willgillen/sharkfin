from typing import List, Dict, Optional, Set
from collections import defaultdict, Counter
import re
from decimal import Decimal
from app.services.payee_service import PayeeService
from app.services.payee_extraction_service import PayeeExtractionService

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
        detected_merchant: Optional[str] = None,
        extracted_payee_name: Optional[str] = None,
        extraction_confidence: Optional[float] = None
    ):
        self.suggested_name = suggested_name
        self.payee_pattern = payee_pattern
        self.payee_match_type = payee_match_type
        self.matching_rows = matching_rows
        self.sample_descriptions = sample_descriptions
        self.confidence = confidence
        self.detected_merchant = detected_merchant
        self.extracted_payee_name = extracted_payee_name
        self.extraction_confidence = extraction_confidence


class SmartRuleSuggestionService:
    """
    Service for analyzing import data and suggesting rules intelligently.

    This service examines transaction data from imports and uses pattern
    recognition and merchant detection to suggest useful categorization rules.

    Note: Merchant detection is now handled by PayeeExtractionService using
    the known_merchants.json config file. This service relies on that for
    intelligent payee extraction and merchant recognition.
    """

    def __init__(self, db=None):
        self.extraction_service = PayeeExtractionService(db) if db else None

    def analyze_import_data(
        self,
        transactions: List[Dict],
        min_occurrences: int = 2,
        min_confidence: float = 0.6
    ) -> List[SmartRuleSuggestion]:
        """
        Analyze import transaction data and suggest rules.

        This now relies entirely on PayeeExtractionService for merchant detection
        and payee name extraction. The extraction service handles well-known
        merchants from the known_merchants.json config file.

        Args:
            transactions: List of transaction dicts with 'description', 'payee', 'amount'
            min_occurrences: Minimum times a pattern must appear
            min_confidence: Minimum confidence score (0.0 to 1.0)

        Returns:
            List of SmartRuleSuggestion objects
        """
        # Find common patterns using PayeeExtractionService
        # This handles both well-known merchants and other recurring payees
        suggestions = self._find_common_patterns(transactions, min_occurrences, min_confidence)

        # Sort by confidence and number of matches
        suggestions.sort(key=lambda s: (s.confidence, len(s.matching_rows)), reverse=True)

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
        Uses PayeeExtractionService for intelligent extraction and grouping.
        """
        suggestions = []

        # Use extraction service if available, otherwise fall back to PayeeService normalization
        if self.extraction_service:
            extracted_payees = defaultdict(list)

            for idx, txn in enumerate(transactions):
                description = txn.get('description', '')
                payee = txn.get('payee', '')

                # Use the description as the primary source (that's where payee info is in CSV)
                text_to_extract = description or payee

                if not text_to_extract or text_to_extract.strip() == '':
                    continue

                # Extract payee name with confidence
                extracted_name, extraction_confidence = self.extraction_service.extract_payee_name(text_to_extract)

                if extracted_name and len(extracted_name) >= 3:  # Minimum 3 chars for a valid payee
                    extracted_payees[extracted_name].append({
                        'index': idx,
                        'description': description,
                        'payee': payee,
                        'original': text_to_extract,
                        'extraction_confidence': extraction_confidence
                    })

            # Create suggestions for patterns that appear frequently
            for extracted_name, matches in extracted_payees.items():
                if len(matches) >= min_occurrences:
                    matching_rows = [m['index'] for m in matches]
                    sample_descriptions = [m['original'] for m in matches[:3]]

                    # Calculate base confidence based on frequency
                    # Range: 0.5 to 1.0 (start higher for low-frequency patterns)
                    base_confidence = min(1.0, 0.5 + (len(matches) / 20))

                    # Average extraction confidence across matches
                    extraction_confidences = [m['extraction_confidence'] for m in matches]
                    avg_extraction_confidence = sum(extraction_confidences) / len(extraction_confidences)

                    # Combine base confidence with extraction confidence
                    # Weight: 50% base (frequency) + 50% extraction quality
                    # This gives more weight to extraction quality for well-extracted patterns
                    combined_confidence = (base_confidence * 0.5) + (avg_extraction_confidence * 0.5)

                    if combined_confidence >= min_confidence:
                        suggestion = SmartRuleSuggestion(
                            suggested_name=f"Auto: {extracted_name}",
                            payee_pattern=extracted_name,
                            payee_match_type="contains",
                            matching_rows=matching_rows,
                            sample_descriptions=sample_descriptions,
                            confidence=combined_confidence,
                            detected_merchant=extracted_name,
                            extracted_payee_name=extracted_name,
                            extraction_confidence=avg_extraction_confidence
                        )
                        suggestions.append(suggestion)

        else:
            # Fallback to PayeeService normalization if extraction service not available
            payee_service = PayeeService(db=None)
            normalized_payees = defaultdict(list)

            for idx, txn in enumerate(transactions):
                description = txn.get('description', '')
                payee = txn.get('payee', '')

                text_to_normalize = description or payee

                if not text_to_normalize or text_to_normalize.strip() == '':
                    continue

                normalized = payee_service._normalize_payee_name(text_to_normalize)

                if normalized and len(normalized) >= 3:
                    normalized_payees[normalized].append({
                        'index': idx,
                        'description': description,
                        'payee': payee,
                        'original': text_to_normalize
                    })

            for normalized_name, matches in normalized_payees.items():
                if len(matches) >= min_occurrences:
                    matching_rows = [m['index'] for m in matches]
                    sample_descriptions = [m['original'] for m in matches[:3]]

                    confidence = min(1.0, len(matches) / 10) * 0.7 + 0.3

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
