#!/usr/bin/env python3
"""
Test script to validate smart rule suggestions with real CSV data.
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
suggestions = service.analyze_import_data(
    transactions,
    min_occurrences=3,  # Lower threshold for testing
    min_confidence=0.3  # Lower confidence for testing
)

print(f"Found {len(suggestions)} rule suggestions:")
print("=" * 80)

for i, suggestion in enumerate(suggestions, 1):
    print(f"\n{i}. {suggestion.suggested_name}")
    print(f"   Pattern: '{suggestion.payee_pattern}' (match type: {suggestion.payee_match_type})")
    print(f"   Confidence: {suggestion.confidence:.2%}")
    print(f"   Matches: {len(suggestion.matching_rows)} transactions")
    print(f"   Samples:")
    for sample in suggestion.sample_descriptions[:3]:
        print(f"      - {sample}")

print("\n" + "=" * 80)
print(f"\nTotal suggestions: {len(suggestions)}")
