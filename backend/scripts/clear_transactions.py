#!/usr/bin/env python3
"""
Clear all transactions, imports, payees, and rules from the database.

This is useful for testing and UAT to reset the database to a clean state.
Keeps user accounts and account definitions intact.

Usage:
    docker-compose exec backend python scripts/clear_transactions.py
"""

import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.transaction import Transaction
from app.models.import_history import ImportHistory, ImportedTransaction
from app.models.categorization_rule import CategorizationRule
from app.models.payee import Payee


def main():
    """Clear all transaction data from the database."""
    db = SessionLocal()

    try:
        # Get counts before cleanup
        transaction_count = db.query(Transaction).count()
        import_count = db.query(ImportHistory).count()
        imported_txn_count = db.query(ImportedTransaction).count()
        payee_count = db.query(Payee).count()
        rule_count = db.query(CategorizationRule).count()

        print("=" * 80)
        print("Database Cleanup Utility")
        print("=" * 80)
        print()
        print("Current data:")
        print(f"  Transactions:              {transaction_count:,}")
        print(f"  Import History:            {import_count:,}")
        print(f"  Imported Transaction Links: {imported_txn_count:,}")
        print(f"  Payees:                    {payee_count:,}")
        print(f"  Rules:                     {rule_count:,}")
        print()

        # Confirm deletion
        total_items = (
            transaction_count
            + import_count
            + imported_txn_count
            + payee_count
            + rule_count
        )

        if total_items == 0:
            print("✅ Database is already clean!")
            return

        print(f"⚠️  This will delete {total_items:,} records.")
        print()
        print("Proceeding with cleanup...")
        print()

        # Delete in order to avoid foreign key issues
        print("Deleting imported transaction links...")
        db.query(ImportedTransaction).delete()

        print("Deleting all transactions...")
        db.query(Transaction).delete()

        print("Deleting import history...")
        db.query(ImportHistory).delete()

        print("Deleting user-created rules...")
        db.query(CategorizationRule).delete()

        print("Deleting all payees...")
        db.query(Payee).delete()

        db.commit()

        print()
        print("=" * 80)
        print("✅ Cleanup Complete!")
        print("=" * 80)
        print()
        print("After cleanup:")
        print(f"  Transactions:              {db.query(Transaction).count():,}")
        print(f"  Import History:            {db.query(ImportHistory).count():,}")
        print(
            f"  Imported Transaction Links: {db.query(ImportedTransaction).count():,}"
        )
        print(f"  Payees:                    {db.query(Payee).count():,}")
        print(f"  Rules:                     {db.query(CategorizationRule).count():,}")
        print()
        print("🎉 Database is clean and ready for fresh imports!")
        print()

    except Exception as e:
        db.rollback()
        print()
        print("=" * 80)
        print("❌ Error during cleanup")
        print("=" * 80)
        print(f"Error: {e}")
        print()
        import traceback

        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
