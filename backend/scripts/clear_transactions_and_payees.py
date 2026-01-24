#!/usr/bin/env python3
"""
Clear all transactions, payees, and related data for testing.

This script will:
- Delete all transactions
- Delete all payees
- Delete all payee matching patterns
- Delete all import history records
- Reset sequences

This allows you to re-import data and test payee icon auto-suggestion.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import SessionLocal
from app.models.transaction import Transaction
from app.models.payee import Payee
from app.models.payee_matching_pattern import PayeeMatchingPattern
from app.models.import_history import ImportHistory
from sqlalchemy import text


def clear_data():
    """Clear all transaction and payee data."""
    db = SessionLocal()

    try:
        print("🗑️  Clearing database data...")

        # Delete in correct order to respect foreign key constraints

        # 1. Delete import history
        import_count = db.query(ImportHistory).count()
        db.query(ImportHistory).delete()
        print(f"   ✓ Deleted {import_count} import history records")

        # 2. Delete transactions
        transaction_count = db.query(Transaction).count()
        db.query(Transaction).delete()
        print(f"   ✓ Deleted {transaction_count} transactions")

        # 3. Delete payee matching patterns
        pattern_count = db.query(PayeeMatchingPattern).count()
        db.query(PayeeMatchingPattern).delete()
        print(f"   ✓ Deleted {pattern_count} payee matching patterns")

        # 4. Delete payees
        payee_count = db.query(Payee).count()
        db.query(Payee).delete()
        print(f"   ✓ Deleted {payee_count} payees")

        # Commit all deletions
        db.commit()

        # Reset sequences (PostgreSQL)
        print("\n🔄 Resetting sequences...")
        try:
            db.execute(text("ALTER SEQUENCE transactions_id_seq RESTART WITH 1"))
            db.execute(text("ALTER SEQUENCE payees_id_seq RESTART WITH 1"))
            db.execute(text("ALTER SEQUENCE payee_matching_patterns_id_seq RESTART WITH 1"))
            db.execute(text("ALTER SEQUENCE import_history_id_seq RESTART WITH 1"))
            db.commit()
            print("   ✓ Sequences reset")
        except Exception as e:
            print(f"   ⚠️  Could not reset sequences: {e}")

        print("\n✅ Database cleared successfully!")
        print("\nYou can now re-import your transactions.")
        print("Payees will be automatically created with brand logos and emoji icons!")

    except Exception as e:
        print(f"\n❌ Error clearing database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    confirm = input("⚠️  This will DELETE all transactions, payees, and import history. Continue? (yes/no): ")

    if confirm.lower() in ["yes", "y"]:
        clear_data()
    else:
        print("Cancelled.")
