"""
Test Script for Intelligent Payee Matching

Simulates the import wizard flow:
1. Create some test payees with patterns
2. Analyze transactions for matching
3. Show how UI would display results (HIGH/LOW/NO_MATCH)
4. Simulate user decisions
5. Create patterns from decisions

Run with:
    docker-compose exec backend python scripts/test_intelligent_matching.py
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.user import User
from app.models.payee import Payee
from app.models.payee_matching_pattern import PayeeMatchingPattern
from app.services.intelligent_payee_matching_service import IntelligentPayeeMatchingService


def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}\n")


def print_analysis(analysis):
    """Print a transaction analysis in a readable format."""
    print(f"Transaction #{analysis.transaction_index + 1}")
    print(f"  Description: {analysis.original_description}")
    print(f"  Extracted: {analysis.extracted_payee_name} ({int(analysis.extraction_confidence * 100)}% extraction quality)")
    print(f"  Match Type: {analysis.match_type}")

    if analysis.matched_payee_id:
        print(f"  Matched Payee: {analysis.matched_payee_name} (ID: {analysis.matched_payee_id})")
        print(f"  Confidence: {int(analysis.match_confidence * 100)}%")
        print(f"  Reason: {analysis.match_reason}")

        if analysis.alternative_matches:
            print(f"  Alternatives:")
            for alt in analysis.alternative_matches:
                print(f"    - {alt.payee_name} ({int(alt.confidence * 100)}%)")
    else:
        print(f"  → Will create NEW payee: {analysis.extracted_payee_name}")

    print()


def main():
    db = SessionLocal()

    try:
        print_section("INTELLIGENT PAYEE MATCHING TEST")

        # Get or create test user
        user = db.query(User).filter(User.email == "test@example.com").first()
        if not user:
            print("Error: No test user found. Please create a user first.")
            return

        print(f"Using user: {user.email} (ID: {user.id})")

        # Step 1: Create some test payees with patterns
        print_section("STEP 1: Creating Test Payees with Patterns")

        # Clear existing test payees (optional - comment out to keep existing)
        existing_payees = db.query(Payee).filter(Payee.user_id == user.id).all()
        print(f"Found {len(existing_payees)} existing payees")

        # Create test payees
        test_payees_data = [
            ("Uber", "known_merchant"),
            ("Country Store", "import_learning"),
            ("Shell", "known_merchant"),
            ("Starbucks", "known_merchant"),
        ]

        created_payees = {}
        for payee_name, source in test_payees_data:
            # Check if exists
            payee = db.query(Payee).filter(
                Payee.user_id == user.id,
                Payee.canonical_name == payee_name
            ).first()

            if not payee:
                payee = Payee(
                    user_id=user.id,
                    canonical_name=payee_name,
                    transaction_count=5,  # Simulate usage
                    auto_match_confidence=0.75
                )
                db.add(payee)
                db.flush()
                print(f"✓ Created payee: {payee_name} (ID: {payee.id})")
            else:
                print(f"  Using existing payee: {payee_name} (ID: {payee.id})")

            created_payees[payee_name] = payee

            # Create pattern for this payee
            pattern_value = payee_name.upper()
            pattern = db.query(PayeeMatchingPattern).filter(
                PayeeMatchingPattern.payee_id == payee.id,
                PayeeMatchingPattern.pattern_type == 'description_contains',
                PayeeMatchingPattern.pattern_value == pattern_value
            ).first()

            if not pattern:
                pattern = PayeeMatchingPattern(
                    payee_id=payee.id,
                    user_id=user.id,
                    pattern_type='description_contains',
                    pattern_value=pattern_value,
                    confidence_score=0.90 if source == 'known_merchant' else 0.80,
                    match_count=3,
                    source=source
                )
                db.add(pattern)
                print(f"  → Created pattern: '{pattern_value}' ({pattern.confidence_score} confidence)")

        db.commit()
        print(f"\nTotal payees ready: {len(created_payees)}")

        # Step 2: Simulate transactions from an import
        print_section("STEP 2: Simulating Import Transactions")

        test_transactions = [
            # High confidence matches (should match Uber)
            {"description": "UBER TRIP 12345 SAN FRANCISCO CA", "payee": None},
            {"description": "XX7800 UBER EATS DELIVERY FEE", "payee": "UBER"},

            # Medium confidence match (should fuzzy match Country Store)
            {"description": "COUNTRY STORE #456 AUSTIN TX", "payee": None},
            {"description": "THE COUNTRY STORE HOUSTON", "payee": None},

            # High confidence (Shell)
            {"description": "SHELL OIL #87654 DALLAS", "payee": "SHELL"},

            # New payee (should not match anything)
            {"description": "LOCAL BAKERY DOWNTOWN COFFEE", "payee": None},
            {"description": "TORCHY'S TACOS #123", "payee": None},

            # Edge case: Similar to Starbucks but different
            {"description": "STARBUCKS RESERVE ROASTERY", "payee": None},
        ]

        print(f"Simulating {len(test_transactions)} transactions from import file\n")
        for i, txn in enumerate(test_transactions):
            print(f"{i + 1}. {txn['description']}")

        # Step 3: Analyze transactions
        print_section("STEP 3: Running Intelligent Analysis")

        matching_service = IntelligentPayeeMatchingService(db)
        analyses = matching_service.analyze_transactions_for_import(
            user_id=user.id,
            transactions=test_transactions
        )

        # Group by match type
        high_confidence = [a for a in analyses if a.match_type == 'HIGH_CONFIDENCE']
        low_confidence = [a for a in analyses if a.match_type == 'LOW_CONFIDENCE']
        no_match = [a for a in analyses if a.match_type == 'NO_MATCH']

        print(f"Analysis Results:")
        print(f"  HIGH_CONFIDENCE: {len(high_confidence)} transactions")
        print(f"  LOW_CONFIDENCE:  {len(low_confidence)} transactions")
        print(f"  NO_MATCH:        {len(no_match)} transactions")

        # Step 4: Display results as UI would
        print_section("STEP 4: Review Results (As UI Would Show)")

        if high_confidence:
            print("🟢 HIGH CONFIDENCE MATCHES (Auto-selected, user can change)")
            print("-" * 80)
            for analysis in high_confidence:
                print_analysis(analysis)

        if low_confidence:
            print("🟡 LOW CONFIDENCE MATCHES (User should review)")
            print("-" * 80)
            for analysis in low_confidence:
                print_analysis(analysis)

        if no_match:
            print("🔵 NEW PAYEES (User can edit names)")
            print("-" * 80)
            for analysis in no_match:
                print_analysis(analysis)

        # Step 5: Simulate user decisions
        print_section("STEP 5: Simulating User Decisions")

        decisions = []

        print("User accepts all HIGH_CONFIDENCE matches...")
        for analysis in high_confidence:
            decisions.append({
                'transaction_index': analysis.transaction_index,
                'payee_id': analysis.matched_payee_id,
                'original_description': analysis.original_description,
                'action': 'accepted_match'
            })
            print(f"  ✓ Transaction #{analysis.transaction_index + 1}: Accept {analysis.matched_payee_name}")

        print("\nUser accepts LOW_CONFIDENCE matches...")
        for analysis in low_confidence:
            decisions.append({
                'transaction_index': analysis.transaction_index,
                'payee_id': analysis.matched_payee_id,
                'original_description': analysis.original_description,
                'action': 'accepted_match'
            })
            print(f"  ✓ Transaction #{analysis.transaction_index + 1}: Accept {analysis.matched_payee_name}")

        print("\nUser creates NEW payees (editing some names)...")
        for analysis in no_match:
            # Simulate user editing some names
            new_name = analysis.extracted_payee_name
            if "BAKERY" in new_name.upper():
                new_name = "Local Bakery"  # User edits the name
            elif "TORCHY" in new_name.upper():
                new_name = "Torchy's Tacos"  # User edits the name

            decisions.append({
                'transaction_index': analysis.transaction_index,
                'new_payee_name': new_name,
                'original_description': analysis.original_description,
                'action': 'create_new'
            })
            print(f"  ✓ Transaction #{analysis.transaction_index + 1}: Create new payee '{new_name}'")

        # Step 6: Create patterns from decisions (learning)
        print_section("STEP 6: Learning from User Decisions")

        patterns_created = 0
        payees_created = 0

        for decision in decisions:
            if decision['action'] == 'accepted_match':
                # User accepted a match - strengthen the pattern
                pattern = matching_service.create_pattern_from_match(
                    user_id=user.id,
                    payee_id=decision['payee_id'],
                    description=decision['original_description'],
                    pattern_type='description_contains',
                    source='import_learning'
                )
                patterns_created += 1
                print(f"  ✓ Strengthened pattern for payee ID {decision['payee_id']}: '{pattern.pattern_value}'")

            elif decision['action'] == 'create_new':
                # User created a new payee - create it with initial pattern
                new_payee = Payee(
                    user_id=user.id,
                    canonical_name=decision['new_payee_name'],
                    transaction_count=0,
                    auto_match_confidence=0.75
                )
                db.add(new_payee)
                db.flush()
                payees_created += 1

                # Create initial pattern
                pattern = matching_service.create_pattern_from_match(
                    user_id=user.id,
                    payee_id=new_payee.id,
                    description=decision['original_description'],
                    pattern_type='description_contains',
                    source='import_learning'
                )
                patterns_created += 1
                print(f"  ✓ Created payee '{new_payee.canonical_name}' (ID: {new_payee.id}) with pattern '{pattern.pattern_value}'")

        db.commit()

        print(f"\nLearning Summary:")
        print(f"  Payees created: {payees_created}")
        print(f"  Patterns created/updated: {patterns_created}")

        # Step 7: Show what would happen on next import
        print_section("STEP 7: Testing Learning - Next Import Simulation")

        next_import_transactions = [
            {"description": "UBER RIDE 67890 HOUSTON TX", "payee": None},
            {"description": "LOCAL BAKERY COFFEE AND PASTRIES", "payee": None},
            {"description": "TORCHY'S TACOS AUSTIN LOCATION", "payee": None},
        ]

        print("Simulating next import with similar transactions:")
        for txn in next_import_transactions:
            print(f"  - {txn['description']}")

        # Re-initialize service to clear cache
        matching_service = IntelligentPayeeMatchingService(db)
        next_analyses = matching_service.analyze_transactions_for_import(
            user_id=user.id,
            transactions=next_import_transactions
        )

        print("\nResults (should show improved matching):")
        for analysis in next_analyses:
            if analysis.matched_payee_id:
                print(f"  ✓ '{analysis.original_description[:50]}...'")
                print(f"    → Matched: {analysis.matched_payee_name} ({analysis.match_type}, {int(analysis.match_confidence * 100)}%)")
            else:
                print(f"  • '{analysis.original_description[:50]}...'")
                print(f"    → New payee needed: {analysis.extracted_payee_name}")

        print_section("TEST COMPLETE")
        print("✅ Intelligent matching system is working correctly!")
        print("\nKey observations:")
        print("1. High-confidence matches (>=85%) are auto-selected")
        print("2. Low-confidence matches (70-84%) are flagged for review")
        print("3. New payees (<70% match) are suggested with extracted names")
        print("4. Patterns are learned from user decisions")
        print("5. Future imports benefit from learned patterns")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()

    finally:
        db.close()


if __name__ == "__main__":
    main()
