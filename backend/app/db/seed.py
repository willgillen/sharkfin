"""Seed data for development and testing."""
from datetime import date, datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.account import Account, AccountType
from app.models.category import Category, CategoryType
from app.models.transaction import Transaction, TransactionType
from app.models.budget import Budget, BudgetPeriod
from app.core.security import get_password_hash


def seed_database(db: Session):
    """Seed the database with sample data for development."""

    # Check if database is already seeded
    if db.query(User).filter(User.email == "demo@sharkfin.com").first():
        print("Database already seeded. Skipping...")
        return

    print("Seeding database...")

    # Create demo user
    demo_user = User(
        email="demo@sharkfin.com",
        hashed_password=get_password_hash("demo123"),
        full_name="Demo User",
        is_active=True
    )
    db.add(demo_user)
    db.commit()
    db.refresh(demo_user)
    print(f"Created demo user: {demo_user.email}")

    # Create accounts
    checking = Account(
        user_id=demo_user.id,
        name="Main Checking",
        type=AccountType.CHECKING,
        currency="USD",
        current_balance=Decimal("2450.75"),
        notes="Primary checking account"
    )

    savings = Account(
        user_id=demo_user.id,
        name="Emergency Savings",
        type=AccountType.SAVINGS,
        currency="USD",
        current_balance=Decimal("10000.00"),
        notes="Emergency fund"
    )

    credit_card = Account(
        user_id=demo_user.id,
        name="Chase Sapphire",
        type=AccountType.CREDIT_CARD,
        currency="USD",
        current_balance=Decimal("-850.25"),
        notes="Travel rewards card"
    )

    db.add_all([checking, savings, credit_card])
    db.commit()
    db.refresh(checking)
    db.refresh(savings)
    db.refresh(credit_card)
    print(f"Created {3} accounts")

    # Create categories

    # Income categories
    income_salary = Category(
        user_id=demo_user.id,
        name="Salary",
        type=CategoryType.INCOME,
        color="#10B981",
        icon="💰"
    )

    income_freelance = Category(
        user_id=demo_user.id,
        name="Freelance",
        type=CategoryType.INCOME,
        color="#34D399",
        icon="💼"
    )

    income_investments = Category(
        user_id=demo_user.id,
        name="Investments",
        type=CategoryType.INCOME,
        color="#6EE7B7",
        icon="📈"
    )

    # Expense categories - Parent categories
    expense_food = Category(
        user_id=demo_user.id,
        name="Food & Dining",
        type=CategoryType.EXPENSE,
        color="#EF4444",
        icon="🍽️"
    )

    expense_transportation = Category(
        user_id=demo_user.id,
        name="Transportation",
        type=CategoryType.EXPENSE,
        color="#F97316",
        icon="🚗"
    )

    expense_housing = Category(
        user_id=demo_user.id,
        name="Housing",
        type=CategoryType.EXPENSE,
        color="#DC2626",
        icon="🏠"
    )

    expense_utilities = Category(
        user_id=demo_user.id,
        name="Utilities",
        type=CategoryType.EXPENSE,
        color="#B91C1C",
        icon="💡"
    )

    expense_entertainment = Category(
        user_id=demo_user.id,
        name="Entertainment",
        type=CategoryType.EXPENSE,
        color="#8B5CF6",
        icon="🎬"
    )

    expense_shopping = Category(
        user_id=demo_user.id,
        name="Shopping",
        type=CategoryType.EXPENSE,
        color="#EC4899",
        icon="🛍️"
    )

    expense_health = Category(
        user_id=demo_user.id,
        name="Healthcare",
        type=CategoryType.EXPENSE,
        color="#06B6D4",
        icon="🏥"
    )

    # Transfer category
    transfer = Category(
        user_id=demo_user.id,
        name="Transfer",
        type=CategoryType.TRANSFER,
        color="#6B7280",
        icon="🔄"
    )

    db.add_all([
        income_salary, income_freelance, income_investments,
        expense_food, expense_transportation, expense_housing,
        expense_utilities, expense_entertainment, expense_shopping,
        expense_health, transfer
    ])
    db.commit()

    # Refresh parent categories so we can create subcategories
    db.refresh(expense_food)
    db.refresh(expense_transportation)
    db.refresh(expense_housing)

    # Subcategories
    food_groceries = Category(
        user_id=demo_user.id,
        name="Groceries",
        type=CategoryType.EXPENSE,
        parent_id=expense_food.id,
        color="#F87171",
        icon="🛒"
    )

    food_restaurants = Category(
        user_id=demo_user.id,
        name="Restaurants",
        type=CategoryType.EXPENSE,
        parent_id=expense_food.id,
        color="#FCA5A5",
        icon="🍴"
    )

    food_coffee = Category(
        user_id=demo_user.id,
        name="Coffee Shops",
        type=CategoryType.EXPENSE,
        parent_id=expense_food.id,
        color="#FECACA",
        icon="☕"
    )

    transport_gas = Category(
        user_id=demo_user.id,
        name="Gas & Fuel",
        type=CategoryType.EXPENSE,
        parent_id=expense_transportation.id,
        color="#FB923C",
        icon="⛽"
    )

    transport_parking = Category(
        user_id=demo_user.id,
        name="Parking",
        type=CategoryType.EXPENSE,
        parent_id=expense_transportation.id,
        color="#FDBA74",
        icon="🅿️"
    )

    housing_rent = Category(
        user_id=demo_user.id,
        name="Rent/Mortgage",
        type=CategoryType.EXPENSE,
        parent_id=expense_housing.id,
        color="#F87171",
        icon="🏘️"
    )

    housing_maintenance = Category(
        user_id=demo_user.id,
        name="Maintenance",
        type=CategoryType.EXPENSE,
        parent_id=expense_housing.id,
        color="#FCA5A5",
        icon="🔧"
    )

    db.add_all([
        food_groceries, food_restaurants, food_coffee,
        transport_gas, transport_parking,
        housing_rent, housing_maintenance
    ])
    db.commit()

    # Refresh all categories to get their IDs
    db.refresh(food_groceries)
    db.refresh(food_restaurants)
    db.refresh(food_coffee)
    db.refresh(transport_gas)
    db.refresh(income_salary)
    db.refresh(income_freelance)
    db.refresh(expense_entertainment)
    db.refresh(expense_utilities)
    db.refresh(housing_rent)
    db.refresh(transfer)

    print(f"Created {18} categories (11 parent, 7 subcategories)")

    # Create transactions for the last 30 days
    transactions = []
    today = date.today()

    # Monthly salary (1st of month)
    if today.day >= 1:
        transactions.append(Transaction(
            user_id=demo_user.id,
            account_id=checking.id,
            category_id=income_salary.id,
            type=TransactionType.CREDIT,
            amount=Decimal("4500.00"),
            date=date(today.year, today.month, 1),
            payee="Acme Corp",
            description="Monthly salary"
        ))

    # Freelance income (15th of month)
    if today.day >= 15:
        transactions.append(Transaction(
            user_id=demo_user.id,
            account_id=checking.id,
            category_id=income_freelance.id,
            type=TransactionType.CREDIT,
            amount=Decimal("750.00"),
            date=date(today.year, today.month, 15),
            payee="Client XYZ",
            description="Website development project"
        ))

    # Rent payment (1st of month)
    if today.day >= 1:
        transactions.append(Transaction(
            user_id=demo_user.id,
            account_id=checking.id,
            category_id=housing_rent.id,
            type=TransactionType.DEBIT,
            amount=Decimal("1500.00"),
            date=date(today.year, today.month, 1),
            payee="Property Management Co",
            description="Monthly rent"
        ))

    # Utilities (5th of month)
    if today.day >= 5:
        transactions.append(Transaction(
            user_id=demo_user.id,
            account_id=checking.id,
            category_id=expense_utilities.id,
            type=TransactionType.DEBIT,
            amount=Decimal("125.50"),
            date=date(today.year, today.month, 5),
            payee="City Electric & Gas",
            description="Electric and gas bill"
        ))

    # Grocery shopping (weekly)
    for week in range(4):
        transaction_date = today - timedelta(days=(3 - week) * 7 + 2)  # Tuesdays
        if transaction_date.month == today.month:
            transactions.append(Transaction(
                user_id=demo_user.id,
                account_id=checking.id,
                category_id=food_groceries.id,
                type=TransactionType.DEBIT,
                amount=Decimal(f"{85 + week * 10}.{50 + week * 5}"),
                date=transaction_date,
                payee="Whole Foods Market",
                description="Weekly grocery shopping"
            ))

    # Coffee shops (frequent)
    for day_offset in [2, 5, 8, 12, 15, 19, 22, 26]:
        transaction_date = today - timedelta(days=today.day - day_offset if day_offset <= today.day else 0)
        if transaction_date.month == today.month and transaction_date <= today:
            transactions.append(Transaction(
                user_id=demo_user.id,
                account_id=credit_card.id,
                category_id=food_coffee.id,
                type=TransactionType.DEBIT,
                amount=Decimal("6.50"),
                date=transaction_date,
                payee="Starbucks",
                description="Morning coffee"
            ))

    # Restaurant meals
    for day_offset in [7, 14, 21]:
        transaction_date = today - timedelta(days=today.day - day_offset if day_offset <= today.day else 0)
        if transaction_date.month == today.month and transaction_date <= today:
            transactions.append(Transaction(
                user_id=demo_user.id,
                account_id=credit_card.id,
                category_id=food_restaurants.id,
                type=TransactionType.DEBIT,
                amount=Decimal(f"{45 + (day_offset % 10) * 5}.{75}"),
                date=transaction_date,
                payee="Various Restaurants",
                description="Dining out"
            ))

    # Gas fill-ups (bi-weekly)
    for week in [1, 3]:
        transaction_date = today - timedelta(days=(3 - week) * 7 + 4)  # Fridays
        if transaction_date.month == today.month:
            transactions.append(Transaction(
                user_id=demo_user.id,
                account_id=checking.id,
                category_id=transport_gas.id,
                type=TransactionType.DEBIT,
                amount=Decimal("45.00"),
                date=transaction_date,
                payee="Shell Gas Station",
                description="Gas fill-up"
            ))

    # Entertainment
    if today.day >= 10:
        transactions.append(Transaction(
            user_id=demo_user.id,
            account_id=credit_card.id,
            category_id=expense_entertainment.id,
            type=TransactionType.DEBIT,
            amount=Decimal("14.99"),
            date=date(today.year, today.month, 10),
            payee="Netflix",
            description="Monthly subscription"
        ))

    if today.day >= 18:
        transactions.append(Transaction(
            user_id=demo_user.id,
            account_id=credit_card.id,
            category_id=expense_entertainment.id,
            type=TransactionType.DEBIT,
            amount=Decimal("32.50"),
            date=date(today.year, today.month, 18),
            payee="AMC Theaters",
            description="Movie night"
        ))

    # Transfer from checking to savings (10th of month)
    if today.day >= 10:
        transactions.append(Transaction(
            user_id=demo_user.id,
            account_id=checking.id,
            category_id=transfer.id,
            type=TransactionType.TRANSFER,
            amount=Decimal("500.00"),
            date=date(today.year, today.month, 10),
            transfer_account_id=savings.id,
            description="Monthly savings transfer"
        ))

    db.add_all(transactions)
    db.commit()
    print(f"Created {len(transactions)} transactions")

    # Create budgets for current month
    from app.models.budget import Budget, BudgetPeriod

    budgets = []

    # Grocery budget
    budgets.append(Budget(
        user_id=demo_user.id,
        category_id=food_groceries.id,
        name="Monthly Grocery Budget",
        amount=Decimal("400.00"),
        period=BudgetPeriod.MONTHLY,
        start_date=date(today.year, today.month, 1),
        rollover=False,
        alert_enabled=True,
        alert_threshold=Decimal("85.0"),
        notes="Budget for grocery shopping"
    ))

    # Restaurant budget
    budgets.append(Budget(
        user_id=demo_user.id,
        category_id=food_restaurants.id,
        name="Dining Out Budget",
        amount=Decimal("200.00"),
        period=BudgetPeriod.MONTHLY,
        start_date=date(today.year, today.month, 1),
        alert_enabled=True,
        alert_threshold=Decimal("90.0")
    ))

    # Coffee budget
    budgets.append(Budget(
        user_id=demo_user.id,
        category_id=food_coffee.id,
        name="Coffee & Cafes",
        amount=Decimal("75.00"),
        period=BudgetPeriod.MONTHLY,
        start_date=date(today.year, today.month, 1),
        alert_enabled=True,
        alert_threshold=Decimal("80.0")
    ))

    # Gas budget
    budgets.append(Budget(
        user_id=demo_user.id,
        category_id=transport_gas.id,
        name="Gas & Fuel Budget",
        amount=Decimal("150.00"),
        period=BudgetPeriod.MONTHLY,
        start_date=date(today.year, today.month, 1),
        alert_enabled=True,
        alert_threshold=Decimal("90.0")
    ))

    # Entertainment budget
    budgets.append(Budget(
        user_id=demo_user.id,
        category_id=expense_entertainment.id,
        name="Entertainment Budget",
        amount=Decimal("100.00"),
        period=BudgetPeriod.MONTHLY,
        start_date=date(today.year, today.month, 1),
        rollover=True,  # Allow unused amount to carry forward
        alert_enabled=True,
        alert_threshold=Decimal("85.0"),
        notes="Movies, streaming services, etc."
    ))

    # Utilities budget
    budgets.append(Budget(
        user_id=demo_user.id,
        category_id=expense_utilities.id,
        name="Utilities Budget",
        amount=Decimal("150.00"),
        period=BudgetPeriod.MONTHLY,
        start_date=date(today.year, today.month, 1),
        alert_enabled=True,
        alert_threshold=Decimal("75.0")
    ))

    db.add_all(budgets)
    db.commit()
    print(f"Created {len(budgets)} budgets")

    print("✅ Database seeded successfully!")
    print(f"\nDemo user credentials:")
    print(f"  Email: demo@sharkfin.com")
    print(f"  Password: demo123")


if __name__ == "__main__":
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
