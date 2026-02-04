from pydantic import BaseModel
from typing import List, Optional
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


class NetWorthDataPoint(BaseModel):
    """Net worth at a point in time."""
    date: date
    total_assets: Decimal
    total_liabilities: Decimal
    net_worth: Decimal


class AccountBalance(BaseModel):
    """Balance details for a single account."""
    account_id: int
    account_name: str
    account_type: str
    balance: Decimal
    is_asset: bool


class NetWorthHistoryResponse(BaseModel):
    """Response for net worth history report."""
    current: NetWorthDataPoint
    history: List[NetWorthDataPoint]
    accounts: List[AccountBalance]
    period_start: date
    period_end: date


class CategoryMonthlySpending(BaseModel):
    """Monthly spending for a single category."""
    month: str  # Format: "2024-01"
    amount: Decimal
    transaction_count: int


class CategoryTrend(BaseModel):
    """Spending trend for a category over time."""
    category_id: int
    category_name: str
    total_amount: Decimal
    average_amount: Decimal
    monthly_data: List[CategoryMonthlySpending]


class SpendingTrendsResponse(BaseModel):
    """Response for spending trends over time."""
    total_spending: Decimal
    categories: List[CategoryTrend]
    months: List[str]  # List of months in order
    period_start: date
    period_end: date


class IncomeSource(BaseModel):
    """Income from a single source/category."""
    category_id: int
    category_name: str
    amount: Decimal
    percentage: Decimal
    transaction_count: int


class MonthlyIncomeExpense(BaseModel):
    """Monthly breakdown with income and expense details."""
    month: str  # Format: "2024-01"
    income: Decimal
    expenses: Decimal
    net: Decimal
    savings_rate: Decimal
    income_sources: List[IncomeSource]
    top_expenses: List[CategorySpending]


class IncomeExpenseDetailResponse(BaseModel):
    """Detailed income vs expenses response."""
    summary: IncomeVsExpenses
    monthly_breakdown: List[MonthlyIncomeExpense]
    income_by_source: List[IncomeSource]
    period_start: date
    period_end: date


class CashFlowProjection(BaseModel):
    """Projected cash flow for a future month."""
    month: str  # Format: "2024-01"
    projected_income: Decimal
    projected_expenses: Decimal
    projected_net: Decimal
    projected_balance: Decimal
    confidence: str  # "high", "medium", "low"


class RecurringBill(BaseModel):
    """A detected recurring expense/bill."""
    payee_name: str
    category_name: Optional[str] = None
    typical_amount: Decimal
    frequency: str  # "monthly", "quarterly", "annual"
    last_paid: Optional[date] = None
    next_expected: Optional[date] = None
    occurrences: int  # How many times it appeared in historical data


class CashFlowForecastResponse(BaseModel):
    """Response for cash flow forecast."""
    current_balance: Decimal
    avg_monthly_income: Decimal
    avg_monthly_expenses: Decimal
    avg_monthly_net: Decimal
    projections: List[CashFlowProjection]
    historical_months_used: int
    forecast_months: int
    recurring_bills: List[RecurringBill] = []  # Detected recurring expenses


class SankeyNode(BaseModel):
    """Node in the Sankey diagram."""
    id: str
    name: str
    value: Decimal


class SankeyLink(BaseModel):
    """Link between nodes in the Sankey diagram."""
    source: str
    target: str
    value: Decimal


class SankeyDiagramResponse(BaseModel):
    """Response for Sankey diagram data."""
    nodes: List[SankeyNode]
    links: List[SankeyLink]
    total_income: Decimal
    total_expenses: Decimal
    net_savings: Decimal
    period_start: date
    period_end: date
