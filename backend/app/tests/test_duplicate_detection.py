"""
Integration tests for duplicate detection service.

Tests FITID exact matching, fuzzy date+amount+description matching,
and confidence-based categorization.
"""
import pytest
from datetime import datetime, timedelta
from app.services.duplicate_detection_service import DuplicateDetectionService
from app.models.transaction import Transaction, TransactionType
from app.models.user import User
from app.models.account import Account, AccountType
from sqlalchemy.orm import Session


@pytest.fixture
def test_user(db_session: Session):
    """Create a test user"""
    user = User(
        email="duplicate@test.com",
        full_name="Duplicate Test User",
        hashed_password="hashedpassword"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_account(db_session: Session, test_user: User):
    """Create a test account"""
    account = Account(
        user_id=test_user.id,
        name="Test Checking",
        type=AccountType.CHECKING,
        current_balance=1000.00
    )
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)
    return account


@pytest.fixture
def duplicate_service(db_session: Session):
    """Create duplicate detection service"""
    return DuplicateDetectionService(db_session)


class TestFITIDExactMatching:
    """Test FITID exact duplicate detection (100% confidence)"""

    def test_fitid_exact_match(self, db_session: Session, test_user: User, test_account: Account, duplicate_service: DuplicateDetectionService):
        """FITID exact match should return 100% confidence duplicate"""
        # Create existing transaction with FITID
        existing = Transaction(
            user_id=test_user.id,
            account_id=test_account.id,
            amount=50.00,
            type=TransactionType.DEBIT,
            date=datetime(2026, 1, 15).date(),
            description="Amazon Purchase",
            fitid="FITID12345"
        )
        db_session.add(existing)
        db_session.commit()

        # New transaction with same FITID
        new_transactions = [{
            'date': '2026-01-15',
            'amount': 50.00,
            'type': 'DEBIT',
            'description': 'Amazon Purchase',
            'fitid': 'FITID12345'
        }]

        duplicates = duplicate_service.find_duplicates(
            test_user.id,
            test_account.id,
            new_transactions
        )

        assert len(duplicates) == 1
        assert duplicates[0].confidence_score == 1.00
        assert duplicates[0].existing_transaction_id == existing.id

    def test_fitid_no_match(self, db_session: Session, test_user: User, test_account: Account, duplicate_service: DuplicateDetectionService):
        """Different FITID means different transaction, even with same amount and date"""
        # Create existing transaction
        existing = Transaction(
            user_id=test_user.id,
            account_id=test_account.id,
            amount=50.00,
            type=TransactionType.DEBIT,
            date=datetime(2026, 1, 15).date(),
            description="Amazon Purchase #1",
            fitid="FITID12345"
        )
        db_session.add(existing)
        db_session.commit()

        # New transaction with different FITID (legitimate duplicate purchase)
        new_transactions = [{
            'date': '2026-01-15',
            'amount': 50.00,
            'type': 'DEBIT',
            'description': 'Amazon Purchase #2',  # Slightly different description
            'fitid': 'FITID67890'  # Different FITID = different transaction
        }]

        duplicates = duplicate_service.find_duplicates(
            test_user.id,
            test_account.id,
            new_transactions
        )

        # Different FITIDs mean these are genuinely different transactions
        # Should find fuzzy match due to date/amount/similar description
        # But confidence should be less than 100% (not FITID match)
        if duplicates:
            assert duplicates[0].confidence_score < 1.00

    def test_fitid_match_across_accounts(self, db_session: Session, test_user: User, duplicate_service: DuplicateDetectionService):
        """FITID should be unique per account (same FITID in different accounts is OK)"""
        # Create two accounts
        account1 = Account(
            user_id=test_user.id,
            name="Checking 1",
            type=AccountType.CHECKING,
            current_balance=1000.00
        )
        account2 = Account(
            user_id=test_user.id,
            name="Checking 2",
            type=AccountType.CHECKING,
            current_balance=2000.00
        )
        db_session.add_all([account1, account2])
        db_session.commit()

        # Create transaction in account1 with FITID
        existing = Transaction(
            user_id=test_user.id,
            account_id=account1.id,
            amount=50.00,
            type=TransactionType.DEBIT,
            date=datetime(2026, 1, 15).date(),
            description="Amazon Purchase",
            fitid="FITID12345"
        )
        db_session.add(existing)
        db_session.commit()

        # Try to import same FITID to account2 - should NOT be duplicate
        new_transactions = [{
            'date': '2026-01-15',
            'amount': 50.00,
            'type': 'DEBIT',
            'description': 'Amazon Purchase',
            'fitid': 'FITID12345'
        }]

        duplicates = duplicate_service.find_duplicates(
            test_user.id,
            account2.id,  # Different account
            new_transactions
        )

        # Should find no FITID duplicates (different account)
        fitid_duplicates = [d for d in duplicates if d.confidence_score == 1.00]
        assert len(fitid_duplicates) == 0


class TestFuzzyMatching:
    """Test date + amount + description fuzzy matching"""

    def test_exact_match_same_day(self, db_session: Session, test_user: User, test_account: Account, duplicate_service: DuplicateDetectionService):
        """Same date, amount, and description should be very high confidence"""
        existing = Transaction(
            user_id=test_user.id,
            account_id=test_account.id,
            amount=75.50,
            type=TransactionType.DEBIT,
            date=datetime(2026, 1, 15).date(),
            description="STARBUCKS STORE #12345"
        )
        db_session.add(existing)
        db_session.commit()

        new_transactions = [{
            'date': '2026-01-15',
            'amount': 75.50,
            'type': 'DEBIT',
            'description': 'STARBUCKS STORE #12345'
        }]

        duplicates = duplicate_service.find_duplicates(
            test_user.id,
            test_account.id,
            new_transactions
        )

        assert len(duplicates) == 1
        # Should be very high confidence (>=0.95)
        assert duplicates[0].confidence_score >= 0.95

    def test_similar_description_same_day(self, db_session: Session, test_user: User, test_account: Account, duplicate_service: DuplicateDetectionService):
        """Similar description, same date and amount should be high confidence"""
        existing = Transaction(
            user_id=test_user.id,
            account_id=test_account.id,
            amount=75.50,
            type=TransactionType.DEBIT,
            date=datetime(2026, 1, 15).date(),
            description="STARBUCKS STORE #12345"
        )
        db_session.add(existing)
        db_session.commit()

        new_transactions = [{
            'date': '2026-01-15',
            'amount': 75.50,
            'type': 'DEBIT',
            'description': 'STARBUCKS STORE #67890'  # Different store number
        }]

        duplicates = duplicate_service.find_duplicates(
            test_user.id,
            test_account.id,
            new_transactions
        )

        assert len(duplicates) == 1
        # Should still be high confidence (>=0.85)
        assert duplicates[0].confidence_score >= 0.85

    def test_one_day_apart(self, db_session: Session, test_user: User, test_account: Account, duplicate_service: DuplicateDetectionService):
        """1 day apart with exact amount should be high confidence"""
        existing = Transaction(
            user_id=test_user.id,
            account_id=test_account.id,
            amount=100.00,
            type=TransactionType.DEBIT,
            date=datetime(2026, 1, 15).date(),
            description="TARGET STORE"
        )
        db_session.add(existing)
        db_session.commit()

        new_transactions = [{
            'date': '2026-01-16',  # 1 day later
            'amount': 100.00,
            'type': 'DEBIT',
            'description': 'TARGET STORE'
        }]

        duplicates = duplicate_service.find_duplicates(
            test_user.id,
            test_account.id,
            new_transactions
        )

        assert len(duplicates) == 1
        # Should be high confidence (0.85-0.95)
        assert 0.85 <= duplicates[0].confidence_score < 0.95

    def test_two_days_apart(self, db_session: Session, test_user: User, test_account: Account, duplicate_service: DuplicateDetectionService):
        """2 days apart with exact amount should be medium confidence"""
        existing = Transaction(
            user_id=test_user.id,
            account_id=test_account.id,
            amount=45.00,
            type=TransactionType.DEBIT,
            date=datetime(2026, 1, 15).date(),
            description="SHELL GAS STATION"
        )
        db_session.add(existing)
        db_session.commit()

        new_transactions = [{
            'date': '2026-01-17',  # 2 days later
            'amount': 45.00,
            'type': 'DEBIT',
            'description': 'SHELL GAS STATION'
        }]

        duplicates = duplicate_service.find_duplicates(
            test_user.id,
            test_account.id,
            new_transactions
        )

        assert len(duplicates) == 1
        # Should be medium confidence (0.70-0.85)
        assert 0.70 <= duplicates[0].confidence_score < 0.85

    def test_three_days_apart_no_match(self, db_session: Session, test_user: User, test_account: Account, duplicate_service: DuplicateDetectionService):
        """3+ days apart should not be detected as duplicate"""
        existing = Transaction(
            user_id=test_user.id,
            account_id=test_account.id,
            amount=45.00,
            type=TransactionType.DEBIT,
            date=datetime(2026, 1, 15).date(),
            description="SHELL GAS STATION"
        )
        db_session.add(existing)
        db_session.commit()

        new_transactions = [{
            'date': '2026-01-18',  # 3 days later
            'amount': 45.00,
            'type': 'DEBIT',
            'description': 'SHELL GAS STATION'
        }]

        duplicates = duplicate_service.find_duplicates(
            test_user.id,
            test_account.id,
            new_transactions
        )

        # Should find no duplicates (outside 2-day window)
        assert len(duplicates) == 0

    def test_different_amount_no_match(self, db_session: Session, test_user: User, test_account: Account, duplicate_service: DuplicateDetectionService):
        """Different amount should not match even with same date and description"""
        existing = Transaction(
            user_id=test_user.id,
            account_id=test_account.id,
            amount=50.00,
            type=TransactionType.DEBIT,
            date=datetime(2026, 1, 15).date(),
            description="AMAZON PURCHASE"
        )
        db_session.add(existing)
        db_session.commit()

        new_transactions = [{
            'date': '2026-01-15',
            'amount': 75.00,  # Different amount
            'type': 'DEBIT',
            'description': 'AMAZON PURCHASE'
        }]

        duplicates = duplicate_service.find_duplicates(
            test_user.id,
            test_account.id,
            new_transactions
        )

        # Should find no duplicates (different amount)
        assert len(duplicates) == 0


class TestConfidenceScoring:
    """Test confidence score calculations"""

    def test_confidence_score_components(self, db_session: Session, test_user: User, test_account: Account, duplicate_service: DuplicateDetectionService):
        """Verify confidence score is calculated from date + amount + description"""
        existing = Transaction(
            user_id=test_user.id,
            account_id=test_account.id,
            amount=100.00,
            type=TransactionType.DEBIT,
            date=datetime(2026, 1, 15).date(),
            description="TEST MERCHANT"
        )
        db_session.add(existing)
        db_session.commit()

        # Test same day match
        new_txn = {
            'date': '2026-01-15',
            'amount': 100.00,
            'description': 'TEST MERCHANT'
        }

        confidence = duplicate_service._calculate_confidence(new_txn, existing)

        # Should be close to 1.0 (date match 0.3 + amount match 0.4 + description match 0.3)
        assert confidence >= 0.95

    def test_partial_description_match(self, db_session: Session, test_user: User, test_account: Account, duplicate_service: DuplicateDetectionService):
        """Partial description match should reduce confidence"""
        existing = Transaction(
            user_id=test_user.id,
            account_id=test_account.id,
            amount=100.00,
            type=TransactionType.DEBIT,
            date=datetime(2026, 1, 15).date(),
            description="WALMART SUPERCENTER #1234"
        )
        db_session.add(existing)
        db_session.commit()

        new_txn = {
            'date': '2026-01-15',
            'amount': 100.00,
            'description': 'WALMART STORE #5678'  # Partial match
        }

        confidence = duplicate_service._calculate_confidence(new_txn, existing)

        # Should be less than exact match but still reasonably high
        assert 0.70 <= confidence < 0.95


class TestMultipleTransactions:
    """Test duplicate detection with multiple existing transactions"""

    def test_multiple_duplicates_found(self, db_session: Session, test_user: User, test_account: Account, duplicate_service: DuplicateDetectionService):
        """Should find all duplicates in batch import"""
        # Create existing transactions
        existing1 = Transaction(
            user_id=test_user.id,
            account_id=test_account.id,
            amount=50.00,
            type=TransactionType.DEBIT,
            date=datetime(2026, 1, 15).date(),
            description="STARBUCKS",
            fitid="FITID001"
        )
        existing2 = Transaction(
            user_id=test_user.id,
            account_id=test_account.id,
            amount=100.00,
            type=TransactionType.DEBIT,
            date=datetime(2026, 1, 16).date(),
            description="TARGET"
        )
        db_session.add_all([existing1, existing2])
        db_session.commit()

        # Try to import 3 transactions: 2 duplicates, 1 new
        new_transactions = [
            {
                'date': '2026-01-15',
                'amount': 50.00,
                'description': 'STARBUCKS',
                'fitid': 'FITID001'  # Duplicate FITID
            },
            {
                'date': '2026-01-16',
                'amount': 100.00,
                'description': 'TARGET'  # Duplicate fuzzy
            },
            {
                'date': '2026-01-17',
                'amount': 75.00,
                'description': 'NEW MERCHANT'  # Not a duplicate
            }
        ]

        duplicates = duplicate_service.find_duplicates(
            test_user.id,
            test_account.id,
            new_transactions
        )

        assert len(duplicates) == 2

    def test_checks_all_existing_transactions(self, db_session: Session, test_user: User, test_account: Account, duplicate_service: DuplicateDetectionService):
        """Should check against ALL existing transactions, not just recent imports"""
        # Create old transaction (from 6 months ago in different import)
        old_transaction = Transaction(
            user_id=test_user.id,
            account_id=test_account.id,
            amount=99.99,
            type=TransactionType.DEBIT,
            date=datetime(2026, 1, 15).date(),
            description="NETFLIX SUBSCRIPTION",
            fitid="NETFLIX_OLD"
        )
        db_session.add(old_transaction)
        db_session.commit()

        # Try to import similar transaction today
        new_transactions = [{
            'date': '2026-01-15',  # Same date (within 2 days)
            'amount': 99.99,
            'description': 'NETFLIX SUBSCRIPTION',
            'fitid': 'NETFLIX_NEW'  # Different FITID but fuzzy match
        }]

        duplicates = duplicate_service.find_duplicates(
            test_user.id,
            test_account.id,
            new_transactions
        )

        # Should find the old transaction as a duplicate
        assert len(duplicates) == 1


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_no_description(self, db_session: Session, test_user: User, test_account: Account, duplicate_service: DuplicateDetectionService):
        """Handle transactions with no description"""
        existing = Transaction(
            user_id=test_user.id,
            account_id=test_account.id,
            amount=50.00,
            type=TransactionType.DEBIT,
            date=datetime(2026, 1, 15).date(),
            description=None
        )
        db_session.add(existing)
        db_session.commit()

        new_transactions = [{
            'date': '2026-01-15',
            'amount': 50.00,
            'type': 'DEBIT',
            'description': None
        }]

        # Should not crash, may or may not find duplicate
        duplicates = duplicate_service.find_duplicates(
            test_user.id,
            test_account.id,
            new_transactions
        )

        # Should handle gracefully (might find duplicate based on date + amount only)
        assert isinstance(duplicates, list)

    def test_no_fitid(self, db_session: Session, test_user: User, test_account: Account, duplicate_service: DuplicateDetectionService):
        """Handle transactions without FITID (CSV imports)"""
        existing = Transaction(
            user_id=test_user.id,
            account_id=test_account.id,
            amount=50.00,
            type=TransactionType.DEBIT,
            date=datetime(2026, 1, 15).date(),
            description="CASH WITHDRAWAL",
            fitid=None
        )
        db_session.add(existing)
        db_session.commit()

        new_transactions = [{
            'date': '2026-01-15',
            'amount': 50.00,
            'description': 'CASH WITHDRAWAL'
            # No fitid field
        }]

        duplicates = duplicate_service.find_duplicates(
            test_user.id,
            test_account.id,
            new_transactions
        )

        # Should find fuzzy match
        assert len(duplicates) >= 1

    def test_case_insensitive_description_match(self, db_session: Session, test_user: User, test_account: Account, duplicate_service: DuplicateDetectionService):
        """Description matching should be case-insensitive"""
        existing = Transaction(
            user_id=test_user.id,
            account_id=test_account.id,
            amount=25.00,
            type=TransactionType.DEBIT,
            date=datetime(2026, 1, 15).date(),
            description="McDonald's Restaurant"
        )
        db_session.add(existing)
        db_session.commit()

        new_transactions = [{
            'date': '2026-01-15',
            'amount': 25.00,
            'description': "MCDONALD'S RESTAURANT"  # Different case
        }]

        duplicates = duplicate_service.find_duplicates(
            test_user.id,
            test_account.id,
            new_transactions
        )

        assert len(duplicates) == 1
        assert duplicates[0].confidence_score >= 0.95  # Should match well
