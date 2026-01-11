from pydantic import BaseModel
from typing import List
from decimal import Decimal
from datetime import date


class AccountSummary(BaseModel):
    """Summary of account balances."""
    total_assets: Decimal
    total_liabilities: Decimal
    net_worth: Decimal


class CategorySpending(BaseModel):
    """Spending summary for a category."""
    category_id: int
    category_name: str
    amount: Decimal
    percentage: Decimal
    transaction_count: int


class SpendingByCategoryResponse(BaseModel):
    """Response for spending by category report."""
    total_spending: Decimal
    categories: List[CategorySpending]
    period_start: date
    period_end: date


class IncomeVsExpenses(BaseModel):
    """Income vs expenses summary."""
    total_income: Decimal
    total_expenses: Decimal
    net: Decimal
    savings_rate: Decimal  # Percentage


class MonthlyTrend(BaseModel):
    """Monthly trend data point."""
    month: str  # Format: "2024-01"
    income: Decimal
    expenses: Decimal
    net: Decimal


class IncomeVsExpensesResponse(BaseModel):
    """Response for income vs expenses report."""
    current_period: IncomeVsExpenses
    monthly_trends: List[MonthlyTrend]
    period_start: date
    period_end: date


class BudgetStatus(BaseModel):
    """Budget status summary."""
    budget_id: int
    budget_name: str
    category_name: str
    amount: Decimal
    spent: Decimal
    remaining: Decimal
    percentage: Decimal
    is_over_budget: bool
    alert_threshold: Decimal


class DashboardSummary(BaseModel):
    """Complete dashboard summary."""
    account_summary: AccountSummary
    income_vs_expenses: IncomeVsExpenses
    budget_status: List[BudgetStatus]
    top_spending_categories: List[CategorySpending]
    period_start: date
    period_end: date
