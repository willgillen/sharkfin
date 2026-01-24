#!/usr/bin/env python3
"""
Debug payee icon assignment during import.

This script checks what payees were created and whether they got icons.
"""

import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.payee import Payee
from app.services.payee_icon_service import payee_icon_service


def main():
    """Check payee icons and test suggestions."""
    db = SessionLocal()

    try:
        # Get all payees
        payees = db.query(Payee).all()
        print(f"Total payees created: {len(payees)}")
        print()
        print(f"{'Canonical Name':50} {'Logo URL':80}")
        print("=" * 130)
        for p in payees:
            logo = p.logo_url if p.logo_url else "None"
            print(f"{p.canonical_name:50} {logo:80}")

        print()
        print("=" * 130)
        print()
        print("Testing icon suggestions for payees that did NOT get logos:")
        print()

        # Test suggestions for payees without logos
        for p in payees:
            if not p.logo_url:
                suggestion = payee_icon_service.suggest_icon(p.canonical_name)
                matched_term = suggestion.get("matched_term", "None")
                print(
                    f'{p.canonical_name:40} -> {suggestion["icon_type"]:8} '
                    f'confidence={suggestion["confidence"]:.2f} '
                    f'matched="{matched_term}"'
                )

    finally:
        db.close()


if __name__ == "__main__":
    main()
