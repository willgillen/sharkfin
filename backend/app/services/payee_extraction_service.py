"""
Payee Extraction Service

Intelligently extracts clean payee names from transaction descriptions
by removing common noise patterns like:
- Store/location numbers (#1234, #456)
- Payment processor prefixes (SQ *, TST*, STRIPE)
- Transaction IDs and confirmation codes
- URL suffixes (.com, .net)
- Location indicators (street addresses, city/state)
"""
import re
import json
import os
from typing import Optional, Tuple, List
from sqlalchemy.orm import Session
from app.models.payee import Payee
from Levenshtein import ratio


class PayeeExtractionService:
    def __init__(self, db: Session):
        self.db = db
        self.known_merchants = self._load_known_merchants()

    def _load_known_merchants(self) -> List[Tuple[str, str]]:
        """
        Load known merchant patterns from JSON config file.

        Returns:
            List of tuples: [(pattern, canonical_name), ...]
        """
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'config',
            'known_merchants.json'
        )

        try:
            with open(config_path, 'r') as f:
                data = json.load(f)
                merchants = []
                for merchant in data.get('merchants', []):
                    pattern = merchant.get('pattern')
                    name = merchant.get('name')
                    if pattern and name:
                        merchants.append((pattern, name))
                return merchants
        except FileNotFoundError:
            # If config file doesn't exist, log warning and return empty list
            print(f"Warning: Known merchants config not found at {config_path}")
            return []
        except json.JSONDecodeError as e:
            # If JSON is invalid, log error and return empty list
            print(f"Error parsing known merchants config: {e}")
            return []
        except Exception as e:
            # Catch any other errors
            print(f"Error loading known merchants config: {e}")
            return []

    def extract_payee_name(self, description: str) -> Tuple[str, float]:
        """
        Extract clean payee name from transaction description.

        Returns:
            Tuple of (cleaned_name, confidence_score)
            confidence_score: 0.0-1.0 indicating extraction quality
        """
        if not description or not description.strip():
            return ("", 0.0)

        original = description.strip()

        # STEP 0: Check for well-known merchants FIRST (highest priority)
        for pattern, merchant_name in self.known_merchants:
            if re.search(pattern, original, re.IGNORECASE):
                # Found a well-known merchant - return immediately with high confidence
                return (merchant_name, 0.95)

        cleaned = original
        confidence = 0.5  # Base confidence

        # Apply extraction patterns in order of specificity

        # 1. Payment processor prefixes
        cleaned, processor_match = self._remove_processor_prefixes(cleaned)
        if processor_match:
            confidence += 0.2

        # 2. Expand abbreviations (BEFORE transaction ID removal to avoid losing important words)
        cleaned = self._expand_abbreviations(cleaned)

        # 3. Remove store/location numbers
        cleaned, number_removed = self._remove_store_numbers(cleaned)
        if number_removed:
            confidence += 0.1

        # 4. Remove transaction IDs and codes
        cleaned, id_removed = self._remove_transaction_ids(cleaned)
        if id_removed:
            confidence += 0.1

        # 4. Remove URL suffixes
        cleaned, url_removed = self._remove_url_suffixes(cleaned)
        if url_removed:
            confidence += 0.05

        # 5. Remove location indicators
        cleaned, location_removed = self._remove_location_indicators(cleaned)
        if location_removed:
            confidence += 0.05

        # 6. Clean up whitespace and standardize
        cleaned = self._normalize_whitespace(cleaned)

        # Adjust confidence based on result quality
        if len(cleaned) < 3:
            confidence *= 0.5  # Very short name, low confidence
        elif len(cleaned) > 50:
            confidence *= 0.7  # Very long name, might need more cleaning

        # Cap confidence at 1.0
        confidence = min(confidence, 1.0)

        return (cleaned, confidence)

    def _remove_processor_prefixes(self, text: str) -> Tuple[str, bool]:
        """
        Remove payment processor prefixes and banking prefixes.

        Patterns:
        - SQ * (Square)
        - TST* (Toast)
        - STRIPE*
        - PAYPAL *
        - VENMO *
        - CASHAPP*
        - ACH DEPOSIT COMPANY ...
        - ACH WITHDRAWAL COMPANY ...
        - PAYMENT TO ...
        - ONLINE PAYMENT TO ...
        """
        patterns = [
            r'^SQ\s*\*\s*',                             # Square: "SQ *" or "SQ*"
            r'^TST\s*\*\s*',                            # Toast: "TST*" or "TST *"
            r'^STRIPE\s*\*\s*',                         # Stripe
            r'^PAYPAL\s*\*\s*',                         # PayPal - must have asterisk
            r'^VENMO\s*\*\s*',                          # Venmo
            r'^CASHAPP\s*\*\s*',                        # CashApp
            r'^ZELLE\s*\*\s*',                          # Zelle
            r'^ACH\s+DEPOSIT\s+COMPANY\s+',             # ACH deposits
            r'^ACH\s+WITHDRAWAL\s+COMPANY\s+',          # ACH withdrawals
            r'^ACH\s+DEBIT\s+',                         # ACH debits
            r'^ACH\s+CREDIT\s+',                        # ACH credits
            r'^ONLINE\s+PAYMENT\s+TO\s+',               # Online payments
            r'^PAYMENT\s+TO\s+',                        # Payments
            r'^DEBIT\s+CARD\s+PURCHASE\s*-?\s*',        # Debit card
            r'^CREDIT\s+CARD\s+PURCHASE\s*-?\s*',       # Credit card
            r'^POS\s+PURCHASE\s*-?\s*',                 # POS purchases
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                cleaned = re.sub(pattern, '', text, flags=re.IGNORECASE).strip()
                return (cleaned, True)

        return (text, False)

    def _remove_store_numbers(self, text: str) -> Tuple[str, bool]:
        """
        Remove store/location numbers.

        Patterns:
        - #1234
        - # 1234
        - STORE 1234
        - LOCATION 456
        - Trailing numbers like "WALMART 01234"
        """
        patterns = [
            r'\s*#\s*\d+\s*$',                    # "#1234" at end
            r'\s+STORE\s+\d+\s*$',                # "STORE 1234" at end
            r'\s+LOCATION\s+\d+\s*$',             # "LOCATION 456" at end
            r'\s+LOC\s+\d+\s*$',                  # "LOC 789" at end
            r'\s+\d{4,}\s*$',                     # 4+ digits at end (store IDs)
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                cleaned = re.sub(pattern, '', text, flags=re.IGNORECASE).strip()
                return (cleaned, True)

        return (text, False)

    def _remove_transaction_ids(self, text: str) -> Tuple[str, bool]:
        """
        Remove transaction IDs and confirmation codes.

        Patterns:
        - Long alphanumeric strings (8+ chars)
        - Codes with asterisks: *ABC123
        - Codes in various formats
        - Long numeric transaction IDs (10+ digits)
        - ACH entry descriptors (ENTRY PAYROLL, ENTRY DESC, etc.)
        """
        patterns = [
            r'\*[A-Z0-9]{6,}',                    # "*ABC123DEF"
            r'\s+[A-Z0-9]{8,}\s*$',               # Long alphanumeric at end
            r'\s+-\s+[A-Z0-9]{6,}\s*$',           # "- ABC123XYZ" at end
            r'\s+ENTRY\s+(PAYROLL|DESC|DESCRIPTION|ID)(\s+\d+)?',  # ACH entry descriptors with optional ID
            r'\s+\d{10,}',                        # Long numeric IDs (10+ digits) anywhere
        ]

        any_match = False
        cleaned = text

        for pattern in patterns:
            if re.search(pattern, cleaned, re.IGNORECASE):
                cleaned = re.sub(pattern, ' ', cleaned, flags=re.IGNORECASE).strip()
                any_match = True

        return (cleaned, any_match)

    def _remove_url_suffixes(self, text: str) -> Tuple[str, bool]:
        """
        Remove common URL suffixes.

        Patterns:
        - .COM
        - .NET
        - .ORG
        - WWW.
        """
        patterns = [
            r'^WWW\.',                             # "WWW." at start (do this first)
            r'^HTTPS?://',                         # "HTTP://" or "HTTPS://"
            r'\.(COM|NET|ORG|IO|CO)\s*$',         # URL suffixes at end
        ]

        any_match = False
        cleaned = text

        for pattern in patterns:
            if re.search(pattern, cleaned, re.IGNORECASE):
                cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE).strip()
                any_match = True

        return (cleaned, any_match)

    def _remove_location_indicators(self, text: str) -> Tuple[str, bool]:
        """
        Remove location indicators and addresses.

        Patterns:
        - City, State abbreviations
        - Street addresses
        - Common location words
        - Alphanumeric location codes (XX1801, 5812)
        - Person names at end (for ACH payroll: "WILLIAM GILLEN" or "William Gillen")
          Matches exactly 2 words that look like names (3-15 letters each)
        """
        patterns = [
            r'\s+\d+\s+(ST|AVE|BLVD|RD|LN|DR|CT|WAY)\s*$',  # Street addresses at end
            r'\s+[A-Z]{2}\s+\d{5}\s*$',                      # "CA 12345" (state + zip)
            r'\s+\d{5}\s*$',                                 # Zip code at end
            r'\s+\d{4,}\s+[A-Z]{2,4}\s*$',                   # "5812 CEDA" (number + city abbrev)
            r'\s+[A-Z]{2}\d{4,}\s+[A-Z]{2}\s*$',            # "XX1801 TX" (alphanumeric + state)
            r'\s+\d{4,}\s*$',                                # Generic 4+ digit codes at end (like 5812)
            r'\s+[A-Z][A-Za-z]{2,14}\s+[A-Z][A-Za-z]{2,14}\s*$',  # Person names: "WILLIAM GILLEN" or "William Gillen" (3-15 letters each)
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                cleaned = re.sub(pattern, '', text).strip()
                return (cleaned, True)

        return (text, False)

    def _expand_abbreviations(self, text: str) -> str:
        """
        Expand common abbreviations to full names.

        This helps consolidate variations like "SCHW" → "Schwab"
        """
        # Common company/institution abbreviations (case-insensitive)
        abbreviations = {
            # Financial institutions
            r'\bSCHW\b': 'Schwab',
            r'\bSCHWAB\s*BA\b': 'Schwab Bank',
            r'\bCHARLES\s+SCHW\b': 'Charles Schwab',
            r'\bMERCEDESBENZ\s*FINANCIA?\b': 'Mercedes-Benz Financial',
            r'\bAMERICAN\s+EXPRESS\b': 'American Express',
            r'\bAMEX\b': 'American Express',

            # Government/Utilities
            r'\bDEPT\s+EDUC\b': 'Department of Education',
            r'\bPEDERNALE?S?\b': 'Pedernales Electric',
            r'\bPED\s+ELEC\b': 'Pedernales Electric',

            # Common business abbreviations
            r'\bFREEDOM\s+E\b': 'Freedom',  # Truncated company name

            # Transaction types to clean
            r'\bDIVIDEND\s+DEPOSIT\b': 'Investment Dividend',
        }

        for pattern, replacement in abbreviations.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

        return text

    def _normalize_whitespace(self, text: str) -> str:
        """
        Normalize whitespace and clean up formatting.
        - Remove multiple spaces
        - Trim whitespace
        - Title case for consistency
        """
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)

        # Trim
        text = text.strip()

        # Remove trailing punctuation
        text = re.sub(r'[,.\-_]+$', '', text).strip()

        # Title case (capitalize each word)
        text = text.title()

        return text

    def match_to_existing_payee(
        self,
        user_id: int,
        extracted_name: str,
        threshold: float = 0.80
    ) -> Optional[Payee]:
        """
        Find matching Payee entity using fuzzy string matching.

        Args:
            user_id: User ID to search within
            extracted_name: Cleaned payee name from extraction
            threshold: Similarity threshold (0.0-1.0), default 0.80 (80%)

        Returns:
            Matching Payee entity if found, None otherwise
        """
        if not extracted_name or len(extracted_name) < 2:
            return None

        # Get all user's payees
        payees = self.db.query(Payee).filter(
            Payee.user_id == user_id
        ).all()

        best_match = None
        best_score = 0.0

        for payee in payees:
            # Calculate Levenshtein similarity ratio
            similarity = ratio(
                extracted_name.lower(),
                payee.canonical_name.lower()
            )

            if similarity > best_score:
                best_score = similarity
                best_match = payee

        # Return match only if above threshold
        if best_score >= threshold:
            return best_match

        return None

    def extract_and_match(
        self,
        user_id: int,
        description: str,
        match_threshold: float = 0.80
    ) -> Tuple[str, Optional[Payee], float, float]:
        """
        Complete extraction and matching pipeline.

        Returns:
            Tuple of (extracted_name, matched_payee, extraction_confidence, match_score)
        """
        # Extract clean name
        extracted_name, extraction_confidence = self.extract_payee_name(description)

        # Try to match to existing payee
        matched_payee = None
        match_score = 0.0

        if extracted_name:
            matched_payee = self.match_to_existing_payee(
                user_id,
                extracted_name,
                match_threshold
            )

            if matched_payee:
                # Calculate actual match score for reporting
                match_score = ratio(
                    extracted_name.lower(),
                    matched_payee.canonical_name.lower()
                )

        return (extracted_name, matched_payee, extraction_confidence, match_score)
