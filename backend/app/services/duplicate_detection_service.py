from typing import List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.transaction import Transaction
from app.schemas.imports import PotentialDuplicate
import Levenshtein


class DuplicateDetectionService:
    def __init__(self, db: Session):
        self.db = db

    def find_duplicates(
        self,
        user_id: int,
        account_id: int,
        new_transactions: List[Dict[str, Any]]
    ) -> List[PotentialDuplicate]:
        """Find potential duplicates for new transactions"""
        duplicates = []

        for idx, new_txn in enumerate(new_transactions):
            txn_date = datetime.strptime(new_txn['date'], '%Y-%m-%d').date()
            amount = float(new_txn['amount'])

            # Query existing transactions within ±2 days with exact amount match
            existing = self.db.query(Transaction).filter(
                and_(
                    Transaction.user_id == user_id,
                    Transaction.account_id == account_id,
                    Transaction.date >= txn_date - timedelta(days=2),
                    Transaction.date <= txn_date + timedelta(days=2),
                    Transaction.amount == abs(amount)
                )
            ).all()

            # Check for fuzzy description match
            for existing_txn in existing:
                confidence = self._calculate_confidence(new_txn, existing_txn)

                if confidence > 0.7:  # 70% confidence threshold
                    duplicates.append(PotentialDuplicate(
                        existing_transaction_id=existing_txn.id,
                        existing_date=existing_txn.date.isoformat(),
                        existing_amount=str(existing_txn.amount),
                        existing_description=existing_txn.description,
                        new_transaction={'row': new_txn.get('row', idx), **new_txn},
                        confidence_score=round(confidence, 2)
                    ))

        return duplicates

    def _calculate_confidence(self, new_txn: Dict[str, Any], existing_txn: Transaction) -> float:
        """Calculate duplicate confidence score (0.0 to 1.0)"""
        score = 0.0

        # Date match (within range already filtered)
        try:
            date_diff = abs((datetime.strptime(new_txn['date'], '%Y-%m-%d').date() - existing_txn.date).days)
            date_score = 1.0 - (date_diff / 2.0)  # Perfect match = 1.0, 2 days apart = 0.0
            score += date_score * 0.3
        except:
            pass

        # Amount match (exact)
        try:
            if float(new_txn['amount']) == float(existing_txn.amount):
                score += 0.4
        except:
            pass

        # Description fuzzy match
        new_desc = (new_txn.get('description') or new_txn.get('payee') or '').lower().strip()
        existing_desc = (existing_txn.description or '').lower().strip()

        if new_desc and existing_desc:
            try:
                similarity = Levenshtein.ratio(new_desc, existing_desc)
                score += similarity * 0.3
            except:
                pass

        return min(score, 1.0)  # Cap at 1.0

    def check_fitid_duplicate(self, user_id: int, account_id: int, fitid: str) -> bool:
        """Check if a transaction with this FITID (Financial Institution Transaction ID) already exists"""
        if not fitid:
            return False

        # For OFX imports, we can check if description contains the FITID
        # This is a simple implementation - a more robust solution would store FITID separately
        existing = self.db.query(Transaction).filter(
            and_(
                Transaction.user_id == user_id,
                Transaction.account_id == account_id,
                Transaction.notes.contains(f"FITID:{fitid}")
            )
        ).first()

        return existing is not None
