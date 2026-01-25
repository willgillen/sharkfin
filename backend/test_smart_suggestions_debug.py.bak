#!/usr/bin/env python3
"""
Debug script to understand why some payees aren't showing in suggestions.
"""
from app.services.smart_rule_suggestion_service import SmartRuleSuggestionService

# Sample transactions from real CSV (just descriptions since that's what matters)
sample_descriptions = [
    "CS AUSTIN CAFE AUSTIN",
    "CS AUSTIN CAFE AUSTIN",
    "CS AUSTIN CAFE AUSTIN",
    "CS AUSTIN CAFE AUSTIN",
    "CS AUSTIN CAFE AUSTIN",
    "HCTRA EZ TAG REBILL HOUSTON, TX, US",
    "HCTRA EZ TAG REBILL 281-875-3279",
    "HCTRA EZ TAG REBILL 281-875-3279",
    "HCTRA EZ TAG REBILL 281-875-3279",
    "HCTRA EZ TAG REBILL 281-875-3279",
    "ATT*BILL PAYMENT 800-288-2020",
    "ATT* BILL PAYMENT KH4589@ATT.CO",
    "ATT*BILL PAYMENT 800-288-2020",
    "ATT* BILL PAYMENT 800-331-0500",
    "MAIDS AND MOORE MAIDSANDMOORE",
    "MAIDS AND MOORE MAIDSANDMOORE",
    "MAIDS AND MOORE MAIDSANDMOORE",
    "MAIDS AND MOORE HTTPS:/ AUSTIN",
    "ANTHROPIC ANTHROPIC.COM",
    "ANTHROPIC ANTHROPIC.COM",
    "ANTHROPIC ANTHROPIC.COM",
    "ANTHROPIC ANTHROPIC.COM",
    "NETFLIX.COM NETFLIX.COM",
    "Netflix.com netflix.com",
    "NETFLIX COM LOS GATOS",
    "...133 TORCHYS RONALD REAG GEORGETOWN",
    "...133 TORCHYS RONALD REAG GEORGETOWN",
    "...133 TORCHYS RONALD REAG GEORGETOWN",
    "...133 TORCHYS RONALD REAG GEORGETOWN",
    "Amazon web services aws.amazon.co",
    "Amazon web services aws.amazon.co",
    "Amazon web services aws.amazon.co",
    "DANNYS BARBER SHOP ...652995",
    "DANNYS BARBER SHOP ...652995",
    "DANNYS BARBER SHOP ...652995",
    "SQ *ALL WAYS GROOMING gosq.com",
    "SQ *ALL WAYS GROOMING gosq.com",
    "SQ *ALL WAYS GROOMING gosq.com",
    "SQ *ALL WAYS GROOMING gosq.com",
    "ATMOS ENERGY 888-286-6700",
    "ATMOS ENERGY 888-286-6700",
    "ATMOS ENERGY 888-286-6700",
]

transactions = [{'description': desc, 'payee': '', 'amount': '10.00'} for desc in sample_descriptions]

print(f"Loaded {len(transactions)} sample transactions")
print()

# Run smart rule suggestions
service = SmartRuleSuggestionService()

# Step 1: Merchant detection
merchant_suggestions = service._detect_merchants(transactions, min_occurrences=3)
print(f"Step 1: Merchant detection found {len(merchant_suggestions)} suggestions:")
for s in merchant_suggestions:
    print(f"  - {s.suggested_name}: pattern='{s.payee_pattern}'")

# Step 2: Pattern detection
pattern_suggestions = service._find_common_patterns(transactions, min_occurrences=3, min_confidence=0.3)
print(f"\nStep 2: Pattern detection found {len(pattern_suggestions)} suggestions:")
for s in pattern_suggestions:
    print(f"  - {s.suggested_name}: pattern='{s.payee_pattern}', confidence={s.confidence:.2%}, matches={len(s.matching_rows)}")

# Step 3: Deduplication
existing_patterns = {s.payee_pattern.upper() for s in merchant_suggestions}
print(f"\nStep 3: Existing patterns from merchant detection: {existing_patterns}")

filtered_patterns = []
for pattern_suggestion in pattern_suggestions:
    if pattern_suggestion.payee_pattern.upper() not in existing_patterns:
        filtered_patterns.append(pattern_suggestion)
    else:
        print(f"  FILTERED OUT: {pattern_suggestion.suggested_name} (matches existing pattern)")

print(f"\nAfter deduplication: {len(filtered_patterns)} pattern suggestions remain")

# Final output
final_suggestions = merchant_suggestions + filtered_patterns
final_suggestions.sort(key=lambda s: (s.confidence, len(s.matching_rows)), reverse=True)

print(f"\n{'='*80}")
print(f"FINAL: {len(final_suggestions)} total suggestions")
print(f"{'='*80}")
for i, suggestion in enumerate(final_suggestions, 1):
    print(f"\n{i}. {suggestion.suggested_name}")
    print(f"   Pattern: '{suggestion.payee_pattern}'")
    print(f"   Confidence: {suggestion.confidence:.2%}")
    print(f"   Matches: {len(suggestion.matching_rows)} transactions")
