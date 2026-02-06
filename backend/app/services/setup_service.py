"""Setup service for initial instance configuration."""
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.account import Account, AccountType
from app.models.category import Category, CategoryType
from app.models.transaction import Transaction, TransactionType
from app.models.budget import Budget, BudgetPeriod
from app.core.security import get_password_hash
from app.db.category_templates import get_categories_for_preset


class SetupService:
    """Service for handling initial setup operations."""

    @staticmethod
    def create_admin_user(
        db: Session,
        email: str,
        password: str,
        full_name: str
    ) -> User:
        """
        Create the first user with admin privileges.

        Args:
            db: Database session
            email: Admin user email
            password: Admin user password (will be hashed)
            full_name: Admin user full name

        Returns:
            Created User object with is_superuser=True
        """
        hashed_password = get_password_hash(password)
        admin_user = User(
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            is_active=True,
            is_superuser=True  # First user is always admin
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        return admin_user

    @staticmethod
    def seed_categories(
        db: Session,
        user_id: int,
        preset: str = "standard"
    ) -> int:
        """
        Seed categories based on selected preset.

        Args:
            db: Database session
            user_id: User ID to associate categories with
            preset: Category preset ("minimal", "standard", "comprehensive", "empty")

        Returns:
            Number of categories created
        """
        category_templates = get_categories_for_preset(preset)

        if not category_templates:
            return 0

        # Create a mapping of category names to IDs for parent relationships
        category_map: Dict[str, int] = {}

        # First pass: Create all parent categories (no parent field)
        parent_categories = [cat for cat in category_templates if not cat.get("parent")]
        for template in parent_categories:
            category = Category(
                user_id=user_id,
                name=template["name"],
                type=CategoryType[template["type"].upper()],
                color=template["color"],
                icon=template["icon"],
                parent_id=None
            )
            db.add(category)
            db.flush()  # Flush to get the ID without committing
            category_map[template["name"]] = category.id

        # Second pass: Create all subcategories (with parent field)
        subcategories = [cat for cat in category_templates if cat.get("parent")]
        for template in subcategories:
            parent_name = template["parent"]
            parent_id = category_map.get(parent_name)

            if parent_id:
                category = Category(
                    user_id=user_id,
                    name=template["name"],
                    type=CategoryType[template["type"].upper()],
                    color=template["color"],
                    icon=template["icon"],
                    parent_id=parent_id
                )
                db.add(category)

        db.commit()
        return len(category_templates)

    @staticmethod
    def seed_sample_data(db: Session, user_id: int) -> bool:
        """
        Create sample accounts, transactions, and budgets for demo purposes.

        Args:
            db: Database session
            user_id: User ID to associate data with

        Returns:
            True if sample data was created successfully
        """
        # Get user's categories (must exist first)
        categories = db.query(Category).filter(Category.user_id == user_id).all()
        if not categories:
            return False

        # Create category lookup by name
        category_lookup = {cat.name: cat for cat in categories}

        # Create sample accounts
        checking = Account(
            user_id=user_id,
            name="Main Checking",
            type=AccountType.CHECKING,
            currency="USD",
            opening_balance=Decimal("2450.75"),
            notes="Primary checking account (sample)"
        )

        savings = Account(
            user_id=user_id,
            name="Emergency Savings",
            type=AccountType.SAVINGS,
            currency="USD",
            opening_balance=Decimal("10000.00"),
            notes="Emergency fund (sample)"
        )

        credit_card = Account(
            user_id=user_id,
            name="Credit Card",
            type=AccountType.CREDIT_CARD,
            currency="USD",
            opening_balance=Decimal("-850.25"),
            notes="Rewards card (sample)"
        )

        db.add_all([checking, savings, credit_card])
        db.commit()
        db.refresh(checking)
        db.refresh(savings)
        db.refresh(credit_card)

        # Create sample transactions for the past 30 days
        transactions = []
        today = date.today()

        # Salary (if category exists)
        if "Salary" in category_lookup:
            transactions.append(Transaction(
                user_id=user_id,
                account_id=checking.id,
                category_id=category_lookup["Salary"].id,
                type=TransactionType.CREDIT,
                amount=Decimal("4500.00"),
                date=date(today.year, today.month, 1),
                payee="Acme Corp",
                description="Monthly salary (sample)"
            ))

        # Groceries (weekly)
        groceries_cat = category_lookup.get("Groceries") or category_lookup.get("Food")
        if groceries_cat:
            for week in range(4):
                transaction_date = today - timedelta(days=(3 - week) * 7 + 2)
                if transaction_date.month == today.month:
                    transactions.append(Transaction(
                        user_id=user_id,
                        account_id=checking.id,
                        category_id=groceries_cat.id,
                        type=TransactionType.DEBIT,
                        amount=Decimal(f"{85 + week * 10}.50"),
                        date=transaction_date,
                        payee="Grocery Store",
                        description="Weekly grocery shopping (sample)"
                    ))

        # Restaurants
        restaurants_cat = category_lookup.get("Restaurants") or category_lookup.get("Food")
        if restaurants_cat:
            for day_offset in [7, 14, 21]:
                transaction_date = today - timedelta(days=today.day - day_offset if day_offset <= today.day else 0)
                if transaction_date.month == today.month and transaction_date <= today:
                    transactions.append(Transaction(
                        user_id=user_id,
                        account_id=credit_card.id,
                        category_id=restaurants_cat.id,
                        type=TransactionType.DEBIT,
                        amount=Decimal("45.75"),
                        date=transaction_date,
                        payee="Restaurant",
                        description="Dining out (sample)"
                    ))

        # Coffee shops
        coffee_cat = category_lookup.get("Coffee Shops") or category_lookup.get("Food")
        if coffee_cat:
            for day_offset in [2, 5, 8, 12, 15]:
                transaction_date = today - timedelta(days=today.day - day_offset if day_offset <= today.day else 0)
                if transaction_date.month == today.month and transaction_date <= today:
                    transactions.append(Transaction(
                        user_id=user_id,
                        account_id=credit_card.id,
                        category_id=coffee_cat.id,
                        type=TransactionType.DEBIT,
                        amount=Decimal("6.50"),
                        date=transaction_date,
                        payee="Coffee Shop",
                        description="Morning coffee (sample)"
                    ))

        # Gas & Fuel
        gas_cat = category_lookup.get("Gas & Fuel") or category_lookup.get("Transportation")
        if gas_cat:
            for week in [1, 3]:
                transaction_date = today - timedelta(days=(3 - week) * 7 + 4)
                if transaction_date.month == today.month:
                    transactions.append(Transaction(
                        user_id=user_id,
                        account_id=checking.id,
                        category_id=gas_cat.id,
                        type=TransactionType.DEBIT,
                        amount=Decimal("45.00"),
                        date=transaction_date,
                        payee="Gas Station",
                        description="Gas fill-up (sample)"
                    ))

        # Rent/Mortgage or Bills
        rent_cat = category_lookup.get("Rent/Mortgage") or category_lookup.get("Housing") or category_lookup.get("Bills")
        if rent_cat and today.day >= 1:
            transactions.append(Transaction(
                user_id=user_id,
                account_id=checking.id,
                category_id=rent_cat.id,
                type=TransactionType.DEBIT,
                amount=Decimal("1500.00"),
                date=date(today.year, today.month, 1),
                payee="Landlord",
                description="Monthly rent (sample)"
            ))

        # Utilities or Bills
        utilities_cat = category_lookup.get("Utilities") or category_lookup.get("Bills")
        if utilities_cat and today.day >= 5:
            transactions.append(Transaction(
                user_id=user_id,
                account_id=checking.id,
                category_id=utilities_cat.id,
                type=TransactionType.DEBIT,
                amount=Decimal("125.50"),
                date=date(today.year, today.month, 5),
                payee="Utility Company",
                description="Electric and gas (sample)"
            ))

        # Entertainment
        entertainment_cat = category_lookup.get("Entertainment")
        if entertainment_cat and today.day >= 10:
            transactions.append(Transaction(
                user_id=user_id,
                account_id=credit_card.id,
                category_id=entertainment_cat.id,
                type=TransactionType.DEBIT,
                amount=Decimal("14.99"),
                date=date(today.year, today.month, 10),
                payee="Streaming Service",
                description="Monthly subscription (sample)"
            ))

        # Transfer category for savings transfer
        transfer_cat = category_lookup.get("Transfer")
        if transfer_cat and today.day >= 10:
            transactions.append(Transaction(
                user_id=user_id,
                account_id=checking.id,
                category_id=transfer_cat.id,
                type=TransactionType.TRANSFER,
                amount=Decimal("500.00"),
                date=date(today.year, today.month, 10),
                transfer_account_id=savings.id,
                description="Monthly savings (sample)"
            ))

        db.add_all(transactions)
        db.commit()

        return True
