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

        # 1. Payment processor prefixes (includes ACH COMPANY, ENTRY descriptors)
        cleaned, processor_match = self._remove_processor_prefixes(cleaned)
        if processor_match:
            confidence += 0.2

        # 2. Expand abbreviations (BEFORE transaction ID removal to avoid losing important words)
        cleaned = self._expand_abbreviations(cleaned)

        # 3. Remove phone numbers (before removing other numbers)
        cleaned, phone_removed = self._remove_phone_numbers(cleaned)
        if phone_removed:
            confidence += 0.05

        # 4. Remove MCC codes and store numbers
        cleaned, number_removed = self._remove_store_numbers(cleaned)
        if number_removed:
            confidence += 0.1

        # 5. Remove transaction IDs and codes
        cleaned, id_removed = self._remove_transaction_ids(cleaned)
        if id_removed:
            confidence += 0.1

        # 6. Remove URL suffixes
        cleaned, url_removed = self._remove_url_suffixes(cleaned)
        if url_removed:
            confidence += 0.05

        # 7. Remove location indicators (cities, states, addresses)
        cleaned, location_removed = self._remove_location_indicators(cleaned)
        if location_removed:
            confidence += 0.05

        # 8. Remove person names at end (for ACH transactions)
        cleaned, person_removed = self._remove_person_names(cleaned)
        if person_removed:
            confidence += 0.05

        # 9. Clean up whitespace and standardize
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
        - Bill payment/Dividend Deposit prefixes
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
            r'^BILL\s+PAYMENT\s+(WITHDRAWAL\s+)?',      # Bill payments
            r'^DEBIT\s+CARD\s+PURCHASE\s*(RETURN\s+)?(\s*ADJUSTMENT\s*)?(\s*-?\s*)?',  # Debit card (including returns)
            r'^CREDIT\s+CARD\s+PURCHASE\s*-?\s*',       # Credit card
            r'^POS\s+PURCHASE\s*-?\s*',                 # POS purchases
            r'^DIVIDEND\s+DEPOSIT\s*',                  # Dividend deposits
            r'^RETURN\s+ADJUSTMENT\s+',                 # Return adjustments
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                cleaned = re.sub(pattern, '', text, flags=re.IGNORECASE).strip()
                return (cleaned, True)

        return (text, False)

    def _remove_store_numbers(self, text: str) -> Tuple[str, bool]:
        """
        Remove store/location numbers and MCC codes.

        Patterns:
        - #1234
        - # 1234
        - STORE 1234
        - LOCATION 456
        - MCC codes like "5812", "5999", "5921" (4-digit merchant category codes)
        - Trailing numbers like "WALMART 01234"
        """
        patterns = [
            r'\s*#\s*\d+',                        # "#1234" anywhere (not just end)
            r'\s+STORE\s+\d+\s*$',                # "STORE 1234" at end
            r'\s+LOCATION\s+\d+\s*$',             # "LOCATION 456" at end
            r'\s+LOC\s+\d+\s*$',                  # "LOC 789" at end
            r'\s+\d{4}\s+\d{4,}',                 # Two groups of numbers: "5812 CEDAR" -> removes "5812"
            r'\s+\d{4}\s+[A-Z]{2}\s*$',           # MCC code + state: "5921 TX" at end
            r'\s+[A-Z]{2,15}\s+\d{4,}\s*$',       # Word + digits: "AUSTINLKLNE 5311", "MTG PYMTS 0607"
            r'\s+\d{4,}\s*$',                     # 4+ digits at end (store IDs/MCC codes)
        ]

        any_match = False
        cleaned = text

        # Apply ALL patterns (not just first match)
        for pattern in patterns:
            if re.search(pattern, cleaned, re.IGNORECASE):
                cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE).strip()
                any_match = True

        return (cleaned, any_match)

    def _remove_transaction_ids(self, text: str) -> Tuple[str, bool]:
        """
        Remove transaction IDs and confirmation codes.

        Patterns:
        - Long alphanumeric strings (8+ chars)
        - Codes with asterisks: *ABC123
        - Codes in various formats
        - Long numeric transaction IDs (10+ digits)
        - ACH entry descriptors (ENTRY PAYROLL, ENTRY TRANSFER, ENTRY ELECBILL, etc.)
        """
        # Common ACH ENTRY descriptors to remove
        entry_descriptors = r'(PAYROLL|TRANSFER|AUTO\s+PAY|ELECBILL|MTG\s+PYMTS|' \
                           r'STUDENT\s+LN|SYF\s+PAYMNT|ACH\s+PMT|UTILITY\s+BILL)'

        patterns = [
            r'\*[A-Z0-9]{6,}',                    # "*ABC123DEF"
            r'\s+[A-Z]*\d+[A-Z0-9]{6,}\s*$',      # Long alphanumeric at end (must contain digits)
            r'\s+-\s+[A-Z0-9]{6,}\s*$',           # "- ABC123XYZ" at end
            r'\s+ENTRY\s+' + entry_descriptors,   # ACH entry descriptors (specific types only)
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
        # Common US city names to remove (case-insensitive)
        common_cities = r'(HOUSTON|DALLAS|AUSTIN|ATLANTA|SEATTLE|DENVER|PHOENIX|' \
                       r'CHICAGO|BOSTON|PORTLAND|MIAMI|ORLANDO|DETROIT|CLEVELAND|' \
                       r'LEANDER|LEAND|CEDAR|ROCKEFELLER)'  # Include abbreviated/truncated cities

        # Street/location patterns
        street_suffixes = r'(ST|AVE|BLVD|RD|LN|DR|CT|WAY|PARK|PLAZA|STREET|AVENUE)'

        patterns = [
            r'\s+\d+\s+' + street_suffixes + r'\s*$',        # Street addresses at end
            r'\s+[A-Z]{2}\s+\d{5}\s*$',                      # "CA 12345" (state + zip)
            r'\s+\d{5}\s*$',                                 # Zip code at end
            r'\s+\d{4,}\s+' + street_suffixes + r'(\s+[A-Z]+)?',  # "4899 ROCKEFELLER PLAZA"
            r'\s+\d{4,}\s+[A-Z]{2,10}\s*$',                   # "5812 CEDAR" (number + city abbrev)
            r'\s+[A-Z]{2}\d{4,}\s+[A-Z]{2}\s*$',            # "XX1801 TX" (alphanumeric + state)
            r'\s+\d{4,}\s*$',                                # Generic 4+ digit codes at end (like 5812)
            r'\s+[A-Z][A-Za-z]{2,14}\s+[A-Z]{2}\s*$',       # "AUSTIN TX" or "Houston Tx" (city + state)
            r'\s+' + common_cities + r'\s*$',                 # Common city names at end
            r'\s+[A-Z]{2}\s*$',                              # State abbreviation alone at end (PA, TX, NY, CA)
        ]

        any_match = False
        cleaned = text

        # Apply ALL patterns (not just first match)
        for pattern in patterns:
            if re.search(pattern, cleaned, re.IGNORECASE):
                cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE).strip()
                any_match = True

        return (cleaned, any_match)

    def _remove_phone_numbers(self, text: str) -> Tuple[str, bool]:
        """
        Remove phone numbers in various formats.

        Patterns:
        - 8099 8553894043 (space-separated)
        - 18669321801 (11 digits starting with 1)
        - 8553894043 (10 digits)
        - 555-1234 or 555.1234
        """
        patterns = [
            r'\s+\d{4}\s+\d{10,11}',              # "8099 8553894043" or "5921 18669321801"
            r'\s+\d{11}\s*',                       # "18669321801" (11 digits)
            r'\s+\d{10}\s*',                       # "8553894043" (10 digits)
            r'\s+\d{3}[-\.]\d{4}',                # "555-1234" or "555.1234"
        ]

        any_match = False
        cleaned = text

        for pattern in patterns:
            if re.search(pattern, cleaned):
                cleaned = re.sub(pattern, ' ', cleaned).strip()
                any_match = True

        return (cleaned, any_match)

    def _remove_person_names(self, text: str) -> Tuple[str, bool]:
        """
        Remove person names at end of ACH transactions.

        Patterns:
        - "WILLIAM GILLEN" (two capitalized words)
        - "GILLEN WILLIAM A" (last name first + middle initial)
        - "William Gillen" (title case)

        Only matches at the END of the string to avoid removing merchant names.
        Uses negative lookahead to protect common business words.
        """
        # Words that indicate a business name, not a person name
        business_words = (
            'ENTRY|COMPANY|PAYMENT|WITHDRAWAL|DEPOSIT|'
            'STORE|SHOP|MARKET|RESTAURANT|CAFE|COFFEE|BAKERY|'
            'FOODS|FOOD|DELI|GRILL|BAR|PUB|TAVERN|'
            'BANK|CREDIT|UNION|FINANCIAL|INSURANCE|'
            'ELECTRIC|ENERGY|POWER|GAS|WATER|UTILITY|'
            'MEDICAL|HEALTH|DENTAL|PHARMACY|CLINIC|HOSPITAL|'
            'AUTO|AUTOMOTIVE|MOTORS|SERVICE|SERVICES|'
            'SUPPLY|SUPPLIES|HARDWARE|LUMBER|'
            'HOTEL|MOTEL|INN|RESORT|'
            'LIQUOR|WINE|SPIRITS|BEER|'
            'EXPRESS|SHIPPING|FREIGHT|DELIVERY|'
            'RENTALS|RENTAL|LEASING|'
            'CENTER|CENTRE|PLAZA|MALL|'
            'CORP|CORPORATION|INC|LLC|LTD|'
            'STUDIO|SALON|SPA|FITNESS|GYM'
        )

        patterns = [
            # Two or three capitalized words at end (3-15 letters each)
            # But NOT common business words
            rf'\s+(?!{business_words})[A-Z][A-Za-z]{{2,14}}\s+(?!{business_words})[A-Z][A-Za-z]{{2,14}}(\s+[A-Z])?(\s+ACH\s+TRANSACTION)?\s*$',
        ]

        any_match = False
        cleaned = text

        for pattern in patterns:
            if re.search(pattern, cleaned, re.IGNORECASE):
                cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE).strip()
                any_match = True

        return (cleaned, any_match)

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
            r'\bSCHWAB\s+BANK\b': 'Schwab Bank',
            r'\bCHARLES\s+SCHW\b': 'Charles Schwab',
            r'\bMERCEDESBENZ\s*FINANCIA?\b': 'Mercedes-Benz Financial',
            r'\bMBFSCOM\b': 'Mercedes-Benz Financial',
            r'\bAMERICAN\s+EXPRESS\b': 'American Express',
            r'\bAMEX\b': 'American Express',

            # Government/Utilities
            r'\bDEPT\s+EDUC(ATION)?\b': 'Department of Education',
            r'\bDEPT\s+EDUCATION\b': 'Department of Education',
            r'\bPEDERNALE?S?ELEC\b': 'Pedernales Electric',
            r'\bPED\s+ELEC\b': 'Pedernales Electric',

            # Retailers
            r'\bGOODWILL\s+\d+\b': 'Goodwill',  # "GOODWILL 1260" -> "Goodwill"

            # Common business abbreviations
            r'\bFREEDOM\s+E\b': 'Freedom',  # Truncated company name

            # Transaction types to clean
            r'\bDIVIDEND\s+DEPOSIT\b': 'Investment',
        }

        for pattern, replacement in abbreviations.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

        return text

    def _normalize_whitespace(self, text: str) -> str:
        """
        Normalize whitespace and clean up formatting.
        - Remove multiple spaces
        - Trim whitespace
        - Remove common trailing payment/ACH terms
        - Remove all periods and standalone numbers
        - Title case for consistency
        """
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)

        # Trim
        text = text.strip()

        # Remove common payment/ACH suffixes that might remain
        trailing_terms = r'\s+(EPAYMENT|ER\s+AM|GILLENSTEPHANIE|ACH\s+TRANSACTION)\s*$'
        text = re.sub(trailing_terms, '', text, flags=re.IGNORECASE).strip()

        # Remove all periods (usually URL remnants or abbreviation artifacts)
        text = text.replace('.', '')

        # Remove standalone number groups (space-separated or at start/end)
        # This removes "321801", "96", "051", etc. but preserves "7-ELEVEN"
        text = re.sub(r'^\d+\s+', '', text)          # Numbers at start
        text = re.sub(r'\s+\d+$', '', text)          # Numbers at end
        text = re.sub(r'\s+\d+\s+', ' ', text)       # Numbers in middle

        # Clean up any resulting multiple spaces or leading/trailing spaces
        text = re.sub(r'\s+', ' ', text).strip()

        # Remove leading/trailing punctuation (hyphens, underscores, etc.)
        text = re.sub(r'^[\-_,.\s]+', '', text)
        text = re.sub(r'[\-_,.\s]+$', '', text)

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
