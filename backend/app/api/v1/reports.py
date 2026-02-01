from typing import Optional
from decimal import Decimal
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import csv
import io
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
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
    IncomeExpenseDetailResponse,
    CashFlowProjection,
    CashFlowForecastResponse,
    SankeyNode,
    SankeyLink,
    SankeyDiagramResponse
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


@router.get("/cash-flow-forecast", response_model=CashFlowForecastResponse)
def get_cash_flow_forecast(
    historical_months: int = Query(6, ge=3, le=24, description="Number of historical months to analyze"),
    forecast_months: int = Query(6, ge=1, le=12, description="Number of months to forecast"),
    account_id: Optional[int] = Query(None, description="Filter by specific account (optional)"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """Get cash flow forecast based on historical patterns."""

    end_date = date.today()
    start_date = end_date - relativedelta(months=historical_months)

    # Base filters
    base_filters = [TransactionModel.user_id == current_user.id]
    if account_id:
        base_filters.append(TransactionModel.account_id == account_id)

    # Get current balance
    asset_types = [AccountType.CHECKING, AccountType.SAVINGS, AccountType.INVESTMENT, AccountType.CASH]
    liability_types = [AccountType.CREDIT_CARD, AccountType.LOAN]

    accounts_query = db.query(AccountModel).filter(
        AccountModel.user_id == current_user.id,
        AccountModel.is_active == True
    )
    if account_id:
        accounts_query = accounts_query.filter(AccountModel.id == account_id)
    accounts = accounts_query.all()

    current_balance = Decimal("0.00")
    for account in accounts:
        balance = account.calculate_balance(db)
        if account.type in asset_types:
            current_balance += balance
        elif account.type in liability_types:
            current_balance -= abs(balance)

    # Calculate monthly averages from historical data
    monthly_incomes = []
    monthly_expenses = []

    for i in range(historical_months):
        month_date = end_date - relativedelta(months=i)
        month_start = date(month_date.year, month_date.month, 1)
        month_end = month_start + relativedelta(months=1) - relativedelta(days=1)

        month_income = db.query(func.sum(TransactionModel.amount)).filter(
            *base_filters,
            TransactionModel.type == TransactionType.CREDIT,
            TransactionModel.date >= month_start,
            TransactionModel.date <= month_end
        ).scalar() or Decimal("0.00")

        month_expenses = db.query(func.sum(TransactionModel.amount)).filter(
            *base_filters,
            TransactionModel.type == TransactionType.DEBIT,
            TransactionModel.date >= month_start,
            TransactionModel.date <= month_end
        ).scalar() or Decimal("0.00")

        monthly_incomes.append(month_income)
        monthly_expenses.append(month_expenses)

    # Calculate averages
    avg_income = sum(monthly_incomes) / len(monthly_incomes) if monthly_incomes else Decimal("0.00")
    avg_expenses = sum(monthly_expenses) / len(monthly_expenses) if monthly_expenses else Decimal("0.00")
    avg_net = avg_income - avg_expenses

    # Calculate variance for confidence
    income_variance = sum((x - avg_income) ** 2 for x in monthly_incomes) / len(monthly_incomes) if monthly_incomes else Decimal("0.00")
    expense_variance = sum((x - avg_expenses) ** 2 for x in monthly_expenses) / len(monthly_expenses) if monthly_expenses else Decimal("0.00")

    # Generate projections
    projections = []
    projected_balance = current_balance

    for i in range(1, forecast_months + 1):
        future_month = end_date + relativedelta(months=i)
        month_str = date(future_month.year, future_month.month, 1).strftime("%Y-%m")

        # Simple linear projection using averages
        projected_income = avg_income
        projected_expenses = avg_expenses
        projected_net = projected_income - projected_expenses
        projected_balance += projected_net

        # Determine confidence based on variance
        total_variance = float(income_variance + expense_variance)
        if total_variance < float(avg_income + avg_expenses) * 0.1:
            confidence = "high"
        elif total_variance < float(avg_income + avg_expenses) * 0.3:
            confidence = "medium"
        else:
            confidence = "low"

        projections.append(CashFlowProjection(
            month=month_str,
            projected_income=projected_income,
            projected_expenses=projected_expenses,
            projected_net=projected_net,
            projected_balance=projected_balance,
            confidence=confidence
        ))

    return CashFlowForecastResponse(
        current_balance=current_balance,
        avg_monthly_income=avg_income,
        avg_monthly_expenses=avg_expenses,
        avg_monthly_net=avg_net,
        projections=projections,
        historical_months_used=historical_months,
        forecast_months=forecast_months
    )


@router.get("/sankey-diagram", response_model=SankeyDiagramResponse)
def get_sankey_diagram(
    start_date: Optional[date] = Query(None, description="Start date (defaults to current month)"),
    end_date: Optional[date] = Query(None, description="End date (defaults to today)"),
    account_id: Optional[int] = Query(None, description="Filter by specific account (optional)"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """Get Sankey diagram data showing money flow from income to expenses."""

    # Default to current month if dates not provided
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = date(end_date.year, end_date.month, 1)

    # Base filters
    base_filters = [
        TransactionModel.user_id == current_user.id,
        TransactionModel.date >= start_date,
        TransactionModel.date <= end_date
    ]
    if account_id:
        base_filters.append(TransactionModel.account_id == account_id)

    # Get total income
    total_income = db.query(func.sum(TransactionModel.amount)).filter(
        *base_filters,
        TransactionModel.type == TransactionType.CREDIT
    ).scalar() or Decimal("0.00")

    # Get total expenses
    total_expenses = db.query(func.sum(TransactionModel.amount)).filter(
        *base_filters,
        TransactionModel.type == TransactionType.DEBIT
    ).scalar() or Decimal("0.00")

    net_savings = total_income - total_expenses

    # Get income by category
    income_by_category = db.query(
        CategoryModel.id,
        CategoryModel.name,
        func.sum(TransactionModel.amount).label("total")
    ).join(
        TransactionModel,
        TransactionModel.category_id == CategoryModel.id
    ).filter(
        *base_filters,
        TransactionModel.type == TransactionType.CREDIT
    ).group_by(
        CategoryModel.id,
        CategoryModel.name
    ).order_by(
        func.sum(TransactionModel.amount).desc()
    ).all()

    # Get expenses by category
    expense_by_category = db.query(
        CategoryModel.id,
        CategoryModel.name,
        func.sum(TransactionModel.amount).label("total")
    ).join(
        TransactionModel,
        TransactionModel.category_id == CategoryModel.id
    ).filter(
        *base_filters,
        TransactionModel.type == TransactionType.DEBIT
    ).group_by(
        CategoryModel.id,
        CategoryModel.name
    ).order_by(
        func.sum(TransactionModel.amount).desc()
    ).all()

    # Build nodes
    nodes = []

    # Income source nodes (left side)
    for cat_id, cat_name, total in income_by_category:
        nodes.append(SankeyNode(
            id=f"income_{cat_id}",
            name=cat_name,
            value=total
        ))

    # Central "Total Income" node
    nodes.append(SankeyNode(
        id="total_income",
        name="Total Income",
        value=total_income
    ))

    # Expense category nodes (right side)
    for cat_id, cat_name, total in expense_by_category:
        nodes.append(SankeyNode(
            id=f"expense_{cat_id}",
            name=cat_name,
            value=total
        ))

    # Savings node (if positive)
    if net_savings > 0:
        nodes.append(SankeyNode(
            id="savings",
            name="Savings",
            value=net_savings
        ))

    # Build links
    links = []

    # Links from income sources to total income
    for cat_id, cat_name, total in income_by_category:
        links.append(SankeyLink(
            source=f"income_{cat_id}",
            target="total_income",
            value=total
        ))

    # Links from total income to expense categories
    for cat_id, cat_name, total in expense_by_category:
        links.append(SankeyLink(
            source="total_income",
            target=f"expense_{cat_id}",
            value=total
        ))

    # Link from total income to savings
    if net_savings > 0:
        links.append(SankeyLink(
            source="total_income",
            target="savings",
            value=net_savings
        ))

    return SankeyDiagramResponse(
        nodes=nodes,
        links=links,
        total_income=total_income,
        total_expenses=total_expenses,
        net_savings=net_savings,
        period_start=start_date,
        period_end=end_date
    )


@router.get("/export/transactions")
def export_transactions_csv(
    start_date: Optional[date] = Query(None, description="Start date (defaults to current month)"),
    end_date: Optional[date] = Query(None, description="End date (defaults to today)"),
    account_id: Optional[int] = Query(None, description="Filter by specific account (optional)"),
    category_id: Optional[int] = Query(None, description="Filter by specific category (optional)"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """Export transactions to CSV file."""

    # Default to current month if dates not provided
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = date(end_date.year, end_date.month, 1)

    # Query transactions
    query = db.query(TransactionModel).filter(
        TransactionModel.user_id == current_user.id,
        TransactionModel.date >= start_date,
        TransactionModel.date <= end_date
    )

    if account_id:
        query = query.filter(TransactionModel.account_id == account_id)
    if category_id:
        query = query.filter(TransactionModel.category_id == category_id)

    transactions = query.order_by(TransactionModel.date.desc()).all()

    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow([
        "Date", "Description", "Amount", "Type", "Account", "Category", "Payee", "Notes"
    ])

    # Write data rows
    for txn in transactions:
        # Get account and category names
        account = db.query(AccountModel).filter(AccountModel.id == txn.account_id).first()
        category = db.query(CategoryModel).filter(CategoryModel.id == txn.category_id).first() if txn.category_id else None

        writer.writerow([
            txn.date.strftime("%Y-%m-%d"),
            txn.description,
            str(txn.amount),
            txn.type.value,
            account.name if account else "",
            category.name if category else "",
            txn.payee or "",
            txn.notes or ""
        ])

    # Create streaming response
    output.seek(0)
    filename = f"transactions_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/export/spending-by-category")
def export_spending_by_category_csv(
    start_date: Optional[date] = Query(None, description="Start date (defaults to current month)"),
    end_date: Optional[date] = Query(None, description="End date (defaults to today)"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """Export spending by category to CSV file."""

    # Default to current month if dates not provided
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = date(end_date.year, end_date.month, 1)

    # Get spending data
    total_spending = db.query(func.sum(TransactionModel.amount)).filter(
        TransactionModel.user_id == current_user.id,
        TransactionModel.type == TransactionType.DEBIT,
        TransactionModel.date >= start_date,
        TransactionModel.date <= end_date
    ).scalar() or Decimal("0.00")

    category_spending = db.query(
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
        CategoryModel.name
    ).order_by(
        func.sum(TransactionModel.amount).desc()
    ).all()

    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["Category", "Amount", "Percentage", "Transaction Count"])

    for cat_name, total, count in category_spending:
        percentage = (total / total_spending * 100) if total_spending > 0 else Decimal("0.00")
        writer.writerow([cat_name, str(total), f"{percentage:.2f}%", count])

    # Add total row
    writer.writerow(["Total", str(total_spending), "100%", sum(c[2] for c in category_spending)])

    output.seek(0)
    filename = f"spending_by_category_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/export/income-vs-expenses")
def export_income_vs_expenses_csv(
    months: int = Query(6, ge=1, le=24, description="Number of months to include"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """Export income vs expenses monthly data to CSV file."""

    end_date = date.today()
    start_date = end_date - relativedelta(months=months)

    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["Month", "Income", "Expenses", "Net", "Savings Rate"])

    for i in range(months):
        month_date = end_date - relativedelta(months=i)
        month_start = date(month_date.year, month_date.month, 1)
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
        savings_rate = (month_net / month_income * 100) if month_income > 0 else Decimal("0.00")

        writer.writerow([
            month_start.strftime("%Y-%m"),
            str(month_income),
            str(month_expenses),
            str(month_net),
            f"{savings_rate:.2f}%"
        ])

    output.seek(0)
    filename = f"income_vs_expenses_{months}months.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/export/net-worth-history")
def export_net_worth_history_csv(
    months: int = Query(12, ge=1, le=60, description="Number of months of history"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """Export net worth history to CSV file."""

    end_date = date.today()

    accounts = db.query(AccountModel).filter(
        AccountModel.user_id == current_user.id,
        AccountModel.is_active == True
    ).all()

    asset_types = [AccountType.CHECKING, AccountType.SAVINGS, AccountType.INVESTMENT, AccountType.CASH]
    liability_types = [AccountType.CREDIT_CARD, AccountType.LOAN]

    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["Date", "Total Assets", "Total Liabilities", "Net Worth", "Change"])

    prev_net_worth = None

    for i in range(months - 1, -1, -1):  # Iterate in chronological order
        month_date = end_date - relativedelta(months=i)
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
        change = (month_net_worth - prev_net_worth) if prev_net_worth is not None else Decimal("0.00")

        writer.writerow([
            month_date.strftime("%Y-%m-%d"),
            str(month_assets),
            str(month_liabilities),
            str(month_net_worth),
            str(change) if prev_net_worth is not None else "-"
        ])

        prev_net_worth = month_net_worth

    output.seek(0)
    filename = f"net_worth_history_{months}months.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
