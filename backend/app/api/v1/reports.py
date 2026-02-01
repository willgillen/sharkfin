from typing import Optional
from decimal import Decimal
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User as UserModel
from app.models.account import Account as AccountModel, AccountType
from app.models.transaction import Transaction as TransactionModel, TransactionType
from app.models.category import Category as CategoryModel, CategoryType
from app.models.budget import Budget as BudgetModel
from app.schemas.dashboard import (
    DashboardSummary,
    AccountSummary,
    IncomeVsExpenses,
    IncomeVsExpensesResponse,
    MonthlyTrend,
    SpendingByCategoryResponse,
    CategorySpending,
    BudgetStatus,
    NetWorthDataPoint,
    AccountBalance,
    NetWorthHistoryResponse,
    CategoryMonthlySpending,
    CategoryTrend,
    SpendingTrendsResponse,
    IncomeSource,
    MonthlyIncomeExpense,
    IncomeExpenseDetailResponse
)

router = APIRouter()


@router.get("/dashboard", response_model=DashboardSummary)
def get_dashboard_summary(
    start_date: Optional[date] = Query(None, description="Start date for period (defaults to current month)"),
    end_date: Optional[date] = Query(None, description="End date for period (defaults to today)"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """Get complete dashboard summary with all key metrics."""

    # Default to current month if dates not provided
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = date(end_date.year, end_date.month, 1)

    # Account Summary
    accounts = db.query(AccountModel).filter(AccountModel.user_id == current_user.id).all()

    total_assets = Decimal("0.00")
    total_liabilities = Decimal("0.00")

    for account in accounts:
        # Calculate balance on-the-fly from opening_balance + transactions
        balance = account.calculate_balance(db)
        if account.type in [AccountType.CHECKING, AccountType.SAVINGS, AccountType.INVESTMENT, AccountType.CASH]:
            total_assets += balance
        elif account.type in [AccountType.CREDIT_CARD, AccountType.LOAN]:
            total_liabilities += abs(balance)

    net_worth = total_assets - total_liabilities

    account_summary = AccountSummary(
        total_assets=total_assets,
        total_liabilities=total_liabilities,
        net_worth=net_worth
    )

    # Income vs Expenses for current period
    income_query = db.query(func.sum(TransactionModel.amount)).filter(
        TransactionModel.user_id == current_user.id,
        TransactionModel.type == TransactionType.CREDIT,
        TransactionModel.date >= start_date,
        TransactionModel.date <= end_date
    )
    total_income = income_query.scalar() or Decimal("0.00")

    expense_query = db.query(func.sum(TransactionModel.amount)).filter(
        TransactionModel.user_id == current_user.id,
        TransactionModel.type == TransactionType.DEBIT,
        TransactionModel.date >= start_date,
        TransactionModel.date <= end_date
    )
    total_expenses = expense_query.scalar() or Decimal("0.00")

    net = total_income - total_expenses
    savings_rate = (net / total_income * 100) if total_income > 0 else Decimal("0.00")

    income_vs_expenses = IncomeVsExpenses(
        total_income=total_income,
        total_expenses=total_expenses,
        net=net,
        savings_rate=savings_rate
    )

    # Budget Status
    budgets = db.query(BudgetModel).filter(
        BudgetModel.user_id == current_user.id,
        BudgetModel.start_date <= end_date,
        or_(BudgetModel.end_date.is_(None), BudgetModel.end_date >= start_date)
    ).all()

    budget_status_list = []
    for budget in budgets:
        # Calculate spent for budget period
        budget_start = max(budget.start_date, start_date)
        budget_end = min(budget.end_date, end_date) if budget.end_date else end_date

        spent_query = db.query(func.sum(TransactionModel.amount)).filter(
            TransactionModel.user_id == current_user.id,
            TransactionModel.category_id == budget.category_id,
            TransactionModel.type == TransactionType.DEBIT,
            TransactionModel.date >= budget_start,
            TransactionModel.date <= budget_end
        )
        spent = spent_query.scalar() or Decimal("0.00")

        remaining = budget.amount - spent
        percentage = (spent / budget.amount * 100) if budget.amount > 0 else Decimal("0.00")
        is_over_budget = spent > budget.amount

        category = db.query(CategoryModel).filter(CategoryModel.id == budget.category_id).first()

        budget_status_list.append(BudgetStatus(
            budget_id=budget.id,
            budget_name=budget.name,
            category_name=category.name if category else "Unknown",
            amount=budget.amount,
            spent=spent,
            remaining=remaining,
            percentage=percentage,
            is_over_budget=is_over_budget,
            alert_threshold=budget.alert_threshold
        ))

    # Top Spending Categories (top 5)
    category_spending = db.query(
        CategoryModel.id,
        CategoryModel.name,
        func.sum(TransactionModel.amount).label("total"),
        func.count(TransactionModel.id).label("count")
    ).join(
        TransactionModel,
        TransactionModel.category_id == CategoryModel.id
    ).filter(
        TransactionModel.user_id == current_user.id,
        TransactionModel.type == TransactionType.DEBIT,
        TransactionModel.date >= start_date,
        TransactionModel.date <= end_date
    ).group_by(
        CategoryModel.id,
        CategoryModel.name
    ).order_by(
        func.sum(TransactionModel.amount).desc()
    ).limit(5).all()

    top_spending = []
    for cat_id, cat_name, total, count in category_spending:
        percentage = (total / total_expenses * 100) if total_expenses > 0 else Decimal("0.00")
        top_spending.append(CategorySpending(
            category_id=cat_id,
            category_name=cat_name,
            amount=total,
            percentage=percentage,
            transaction_count=count
        ))

    return DashboardSummary(
        account_summary=account_summary,
        income_vs_expenses=income_vs_expenses,
        budget_status=budget_status_list,
        top_spending_categories=top_spending,
        period_start=start_date,
        period_end=end_date
    )


@router.get("/spending-by-category", response_model=SpendingByCategoryResponse)
def get_spending_by_category(
    start_date: Optional[date] = Query(None, description="Start date (defaults to current month)"),
    end_date: Optional[date] = Query(None, description="End date (defaults to today)"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """Get spending breakdown by category."""

    # Default to current month if dates not provided
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = date(end_date.year, end_date.month, 1)

    # Get total spending
    total_query = db.query(func.sum(TransactionModel.amount)).filter(
        TransactionModel.user_id == current_user.id,
        TransactionModel.type == TransactionType.DEBIT,
        TransactionModel.date >= start_date,
        TransactionModel.date <= end_date
    )
    total_spending = total_query.scalar() or Decimal("0.00")

    # Get spending by category
    category_spending = db.query(
        CategoryModel.id,
        CategoryModel.name,
        func.sum(TransactionModel.amount).label("total"),
        func.count(TransactionModel.id).label("count")
    ).join(
        TransactionModel,
        TransactionModel.category_id == CategoryModel.id
    ).filter(
        TransactionModel.user_id == current_user.id,
        TransactionModel.type == TransactionType.DEBIT,
        TransactionModel.date >= start_date,
        TransactionModel.date <= end_date
    ).group_by(
        CategoryModel.id,
        CategoryModel.name
    ).order_by(
        func.sum(TransactionModel.amount).desc()
    ).all()

    categories = []
    for cat_id, cat_name, total, count in category_spending:
        percentage = (total / total_spending * 100) if total_spending > 0 else Decimal("0.00")
        categories.append(CategorySpending(
            category_id=cat_id,
            category_name=cat_name,
            amount=total,
            percentage=percentage,
            transaction_count=count
        ))

    return SpendingByCategoryResponse(
        total_spending=total_spending,
        categories=categories,
        period_start=start_date,
        period_end=end_date
    )


@router.get("/income-vs-expenses", response_model=IncomeVsExpensesResponse)
def get_income_vs_expenses(
    months: int = Query(6, ge=1, le=24, description="Number of months to include"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """Get income vs expenses with monthly trends."""

    end_date = date.today()
    start_date = end_date - relativedelta(months=months)

    # Current period totals
    income_query = db.query(func.sum(TransactionModel.amount)).filter(
        TransactionModel.user_id == current_user.id,
        TransactionModel.type == TransactionType.CREDIT,
        TransactionModel.date >= start_date,
        TransactionModel.date <= end_date
    )
    total_income = income_query.scalar() or Decimal("0.00")

    expense_query = db.query(func.sum(TransactionModel.amount)).filter(
        TransactionModel.user_id == current_user.id,
        TransactionModel.type == TransactionType.DEBIT,
        TransactionModel.date >= start_date,
        TransactionModel.date <= end_date
    )
    total_expenses = expense_query.scalar() or Decimal("0.00")

    net = total_income - total_expenses
    savings_rate = (net / total_income * 100) if total_income > 0 else Decimal("0.00")

    current_period = IncomeVsExpenses(
        total_income=total_income,
        total_expenses=total_expenses,
        net=net,
        savings_rate=savings_rate
    )

    # Monthly trends
    monthly_trends = []
    for i in range(months):
        month_start = end_date - relativedelta(months=i)
        month_start = date(month_start.year, month_start.month, 1)
        month_end = month_start + relativedelta(months=1) - relativedelta(days=1)

        month_income = db.query(func.sum(TransactionModel.amount)).filter(
            TransactionModel.user_id == current_user.id,
            TransactionModel.type == TransactionType.CREDIT,
            TransactionModel.date >= month_start,
            TransactionModel.date <= month_end
        ).scalar() or Decimal("0.00")

        month_expenses = db.query(func.sum(TransactionModel.amount)).filter(
            TransactionModel.user_id == current_user.id,
            TransactionModel.type == TransactionType.DEBIT,
            TransactionModel.date >= month_start,
            TransactionModel.date <= month_end
        ).scalar() or Decimal("0.00")

        month_net = month_income - month_expenses

        monthly_trends.insert(0, MonthlyTrend(
            month=month_start.strftime("%Y-%m"),
            income=month_income,
            expenses=month_expenses,
            net=month_net
        ))

    return IncomeVsExpensesResponse(
        current_period=current_period,
        monthly_trends=monthly_trends,
        period_start=start_date,
        period_end=end_date
    )


@router.get("/net-worth-history", response_model=NetWorthHistoryResponse)
def get_net_worth_history(
    months: int = Query(12, ge=1, le=60, description="Number of months of history to include"),
    account_id: Optional[int] = Query(None, description="Filter by specific account (optional)"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """Get net worth history over time with monthly data points."""

    end_date = date.today()
    start_date = end_date - relativedelta(months=months)

    # Get all user accounts (or filtered by account_id)
    accounts_query = db.query(AccountModel).filter(
        AccountModel.user_id == current_user.id,
        AccountModel.is_active == True
    )
    if account_id:
        accounts_query = accounts_query.filter(AccountModel.id == account_id)
    accounts = accounts_query.all()

    # Define asset and liability account types
    asset_types = [AccountType.CHECKING, AccountType.SAVINGS, AccountType.INVESTMENT, AccountType.CASH]
    liability_types = [AccountType.CREDIT_CARD, AccountType.LOAN]

    # Calculate current balances for each account
    account_balances = []
    current_assets = Decimal("0.00")
    current_liabilities = Decimal("0.00")

    for account in accounts:
        balance = account.calculate_balance(db, as_of_date=end_date)
        is_asset = account.type in asset_types

        if is_asset:
            current_assets += balance
        elif account.type in liability_types:
            current_liabilities += abs(balance)

        account_balances.append(AccountBalance(
            account_id=account.id,
            account_name=account.name,
            account_type=account.type.value,
            balance=balance,
            is_asset=is_asset
        ))

    current_net_worth = current_assets - current_liabilities

    current = NetWorthDataPoint(
        date=end_date,
        total_assets=current_assets,
        total_liabilities=current_liabilities,
        net_worth=current_net_worth
    )

    # Calculate historical net worth for each month
    history = []
    for i in range(months):
        # Calculate date for end of each month going back
        month_date = end_date - relativedelta(months=i)
        # Get the last day of that month
        if i > 0:
            month_date = date(month_date.year, month_date.month, 1) - relativedelta(days=1)

        month_assets = Decimal("0.00")
        month_liabilities = Decimal("0.00")

        for account in accounts:
            balance = account.calculate_balance(db, as_of_date=month_date)

            if account.type in asset_types:
                month_assets += balance
            elif account.type in liability_types:
                month_liabilities += abs(balance)

        month_net_worth = month_assets - month_liabilities

        history.insert(0, NetWorthDataPoint(
            date=month_date,
            total_assets=month_assets,
            total_liabilities=month_liabilities,
            net_worth=month_net_worth
        ))

    return NetWorthHistoryResponse(
        current=current,
        history=history,
        accounts=account_balances,
        period_start=start_date,
        period_end=end_date
    )


@router.get("/spending-trends", response_model=SpendingTrendsResponse)
def get_spending_trends(
    months: int = Query(6, ge=1, le=24, description="Number of months to include"),
    category_ids: Optional[str] = Query(None, description="Comma-separated category IDs to filter (optional)"),
    account_id: Optional[int] = Query(None, description="Filter by specific account (optional)"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """Get spending trends by category over time."""

    end_date = date.today()
    start_date = end_date - relativedelta(months=months)

    # Parse category IDs if provided
    filter_category_ids = None
    if category_ids:
        filter_category_ids = [int(id.strip()) for id in category_ids.split(",") if id.strip()]

    # Build list of months
    month_list = []
    for i in range(months):
        month_date = end_date - relativedelta(months=i)
        month_str = date(month_date.year, month_date.month, 1).strftime("%Y-%m")
        month_list.insert(0, month_str)

    # Base query filters
    base_filters = [
        TransactionModel.user_id == current_user.id,
        TransactionModel.type == TransactionType.DEBIT,
        TransactionModel.date >= start_date,
        TransactionModel.date <= end_date
    ]

    if account_id:
        base_filters.append(TransactionModel.account_id == account_id)

    # Get total spending
    total_query = db.query(func.sum(TransactionModel.amount)).filter(*base_filters)
    total_spending = total_query.scalar() or Decimal("0.00")

    # Get all categories with spending in this period
    category_query = db.query(
        CategoryModel.id,
        CategoryModel.name
    ).join(
        TransactionModel,
        TransactionModel.category_id == CategoryModel.id
    ).filter(*base_filters).group_by(
        CategoryModel.id,
        CategoryModel.name
    ).order_by(
        func.sum(TransactionModel.amount).desc()
    )

    if filter_category_ids:
        category_query = category_query.filter(CategoryModel.id.in_(filter_category_ids))

    categories_result = category_query.all()

    # Build category trends
    category_trends = []
    for cat_id, cat_name in categories_result:
        monthly_data = []
        total_amount = Decimal("0.00")

        for month_str in month_list:
            # Parse month string to get date range
            year, month = map(int, month_str.split("-"))
            month_start = date(year, month, 1)
            month_end = month_start + relativedelta(months=1) - relativedelta(days=1)

            # Query for this category in this month
            month_filters = base_filters + [
                TransactionModel.category_id == cat_id,
                TransactionModel.date >= month_start,
                TransactionModel.date <= month_end
            ]

            result = db.query(
                func.sum(TransactionModel.amount).label("amount"),
                func.count(TransactionModel.id).label("count")
            ).filter(*month_filters).first()

            amount = result.amount or Decimal("0.00")
            count = result.count or 0
            total_amount += amount

            monthly_data.append(CategoryMonthlySpending(
                month=month_str,
                amount=amount,
                transaction_count=count
            ))

        average_amount = total_amount / len(month_list) if month_list else Decimal("0.00")

        category_trends.append(CategoryTrend(
            category_id=cat_id,
            category_name=cat_name,
            total_amount=total_amount,
            average_amount=average_amount,
            monthly_data=monthly_data
        ))

    return SpendingTrendsResponse(
        total_spending=total_spending,
        categories=category_trends,
        months=month_list,
        period_start=start_date,
        period_end=end_date
    )


@router.get("/income-expense-detail", response_model=IncomeExpenseDetailResponse)
def get_income_expense_detail(
    months: int = Query(6, ge=1, le=24, description="Number of months to include"),
    account_id: Optional[int] = Query(None, description="Filter by specific account (optional)"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """Get detailed income vs expenses breakdown with sources."""

    end_date = date.today()
    start_date = end_date - relativedelta(months=months)

    # Base filters
    base_filters = [TransactionModel.user_id == current_user.id]
    if account_id:
        base_filters.append(TransactionModel.account_id == account_id)

    # Overall summary
    total_income = db.query(func.sum(TransactionModel.amount)).filter(
        *base_filters,
        TransactionModel.type == TransactionType.CREDIT,
        TransactionModel.date >= start_date,
        TransactionModel.date <= end_date
    ).scalar() or Decimal("0.00")

    total_expenses = db.query(func.sum(TransactionModel.amount)).filter(
        *base_filters,
        TransactionModel.type == TransactionType.DEBIT,
        TransactionModel.date >= start_date,
        TransactionModel.date <= end_date
    ).scalar() or Decimal("0.00")

    net = total_income - total_expenses
    savings_rate = (net / total_income * 100) if total_income > 0 else Decimal("0.00")

    summary = IncomeVsExpenses(
        total_income=total_income,
        total_expenses=total_expenses,
        net=net,
        savings_rate=savings_rate
    )

    # Income by source/category
    income_by_category = db.query(
        CategoryModel.id,
        CategoryModel.name,
        func.sum(TransactionModel.amount).label("total"),
        func.count(TransactionModel.id).label("count")
    ).join(
        TransactionModel,
        TransactionModel.category_id == CategoryModel.id
    ).filter(
        *base_filters,
        TransactionModel.type == TransactionType.CREDIT,
        TransactionModel.date >= start_date,
        TransactionModel.date <= end_date
    ).group_by(
        CategoryModel.id,
        CategoryModel.name
    ).order_by(
        func.sum(TransactionModel.amount).desc()
    ).all()

    income_sources = []
    for cat_id, cat_name, total, count in income_by_category:
        percentage = (total / total_income * 100) if total_income > 0 else Decimal("0.00")
        income_sources.append(IncomeSource(
            category_id=cat_id,
            category_name=cat_name,
            amount=total,
            percentage=percentage,
            transaction_count=count
        ))

    # Monthly breakdown
    monthly_breakdown = []
    for i in range(months):
        month_date = end_date - relativedelta(months=i)
        month_start = date(month_date.year, month_date.month, 1)
        month_end = month_start + relativedelta(months=1) - relativedelta(days=1)
        month_str = month_start.strftime("%Y-%m")

        # Month income
        month_income = db.query(func.sum(TransactionModel.amount)).filter(
            *base_filters,
            TransactionModel.type == TransactionType.CREDIT,
            TransactionModel.date >= month_start,
            TransactionModel.date <= month_end
        ).scalar() or Decimal("0.00")

        # Month expenses
        month_expenses = db.query(func.sum(TransactionModel.amount)).filter(
            *base_filters,
            TransactionModel.type == TransactionType.DEBIT,
            TransactionModel.date >= month_start,
            TransactionModel.date <= month_end
        ).scalar() or Decimal("0.00")

        month_net = month_income - month_expenses
        month_savings_rate = (month_net / month_income * 100) if month_income > 0 else Decimal("0.00")

        # Month income sources
        month_income_by_cat = db.query(
            CategoryModel.id,
            CategoryModel.name,
            func.sum(TransactionModel.amount).label("total"),
            func.count(TransactionModel.id).label("count")
        ).join(
            TransactionModel,
            TransactionModel.category_id == CategoryModel.id
        ).filter(
            *base_filters,
            TransactionModel.type == TransactionType.CREDIT,
            TransactionModel.date >= month_start,
            TransactionModel.date <= month_end
        ).group_by(
            CategoryModel.id,
            CategoryModel.name
        ).order_by(
            func.sum(TransactionModel.amount).desc()
        ).limit(5).all()

        month_income_sources = []
        for cat_id, cat_name, total, count in month_income_by_cat:
            percentage = (total / month_income * 100) if month_income > 0 else Decimal("0.00")
            month_income_sources.append(IncomeSource(
                category_id=cat_id,
                category_name=cat_name,
                amount=total,
                percentage=percentage,
                transaction_count=count
            ))

        # Month top expenses
        month_expense_by_cat = db.query(
            CategoryModel.id,
            CategoryModel.name,
            func.sum(TransactionModel.amount).label("total"),
            func.count(TransactionModel.id).label("count")
        ).join(
            TransactionModel,
            TransactionModel.category_id == CategoryModel.id
        ).filter(
            *base_filters,
            TransactionModel.type == TransactionType.DEBIT,
            TransactionModel.date >= month_start,
            TransactionModel.date <= month_end
        ).group_by(
            CategoryModel.id,
            CategoryModel.name
        ).order_by(
            func.sum(TransactionModel.amount).desc()
        ).limit(5).all()

        month_top_expenses = []
        for cat_id, cat_name, total, count in month_expense_by_cat:
            percentage = (total / month_expenses * 100) if month_expenses > 0 else Decimal("0.00")
            month_top_expenses.append(CategorySpending(
                category_id=cat_id,
                category_name=cat_name,
                amount=total,
                percentage=percentage,
                transaction_count=count
            ))

        monthly_breakdown.insert(0, MonthlyIncomeExpense(
            month=month_str,
            income=month_income,
            expenses=month_expenses,
            net=month_net,
            savings_rate=month_savings_rate,
            income_sources=month_income_sources,
            top_expenses=month_top_expenses
        ))

    return IncomeExpenseDetailResponse(
        summary=summary,
        monthly_breakdown=monthly_breakdown,
        income_by_source=income_sources,
        period_start=start_date,
        period_end=end_date
    )
