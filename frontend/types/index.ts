// User types
export interface User {
  id: number;
  email: string;
  full_name: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
  updated_at: string | null;
}

export interface UserCreate {
  email: string;
  full_name: string;
  password: string;
}

export interface UserUpdate {
  email?: string;
  full_name?: string;
  password?: string;
}

// Authentication types
export interface Token {
  access_token: string;
  token_type: string;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

// Account types
export enum AccountType {
  CHECKING = "checking",
  SAVINGS = "savings",
  CREDIT_CARD = "credit_card",
  LOAN = "loan",
  INVESTMENT = "investment",
  CASH = "cash",
  OTHER = "other",
}

export interface Account {
  id: number;
  user_id: number;
  name: string;
  type: AccountType;
  institution: string | null;
  account_number: string | null;
  current_balance: string;
  currency: string;
  is_active: boolean;
  notes: string | null;
  created_at: string;
  updated_at: string | null;
}

export interface AccountCreate {
  name: string;
  type: AccountType;
  institution?: string;
  account_number?: string;
  current_balance: string;
  currency?: string;
  is_active?: boolean;
  notes?: string;
}

export interface AccountUpdate {
  name?: string;
  type?: AccountType;
  institution?: string;
  account_number?: string;
  current_balance?: string;
  currency?: string;
  is_active?: boolean;
  notes?: string;
}

// Category types
export enum CategoryType {
  INCOME = "income",
  EXPENSE = "expense",
}

export interface Category {
  id: number;
  user_id: number;
  name: string;
  type: CategoryType;
  color: string | null;
  icon: string | null;
  is_system: boolean;
  parent_id: number | null;
  created_at: string;
  updated_at: string | null;
}

export interface CategoryCreate {
  name: string;
  type: CategoryType;
  color?: string;
  icon?: string;
  parent_id?: number;
}

export interface CategoryUpdate {
  name?: string;
  type?: CategoryType;
  color?: string;
  icon?: string;
  parent_id?: number;
}

// Transaction types
export enum TransactionType {
  DEBIT = "debit",
  CREDIT = "credit",
  TRANSFER = "transfer",
}

export interface Transaction {
  id: number;
  user_id: number;
  account_id: number;
  category_id: number | null;
  type: TransactionType;
  amount: string;
  date: string;
  description: string;
  notes: string | null;
  payee: string | null;
  is_recurring: boolean;
  tags: string[];
  created_at: string;
  updated_at: string | null;
}

export interface TransactionCreate {
  account_id: number;
  category_id?: number;
  type: TransactionType;
  amount: string;
  date: string;
  description: string;
  notes?: string;
  payee?: string;
  is_recurring?: boolean;
  tags?: string[];
}

export interface TransactionUpdate {
  account_id?: number;
  category_id?: number;
  type?: TransactionType;
  amount?: string;
  date?: string;
  description?: string;
  notes?: string;
  payee?: string;
  is_recurring?: boolean;
  tags?: string[];
}

// Budget types
export enum BudgetPeriod {
  WEEKLY = "weekly",
  MONTHLY = "monthly",
  QUARTERLY = "quarterly",
  YEARLY = "yearly",
}

export interface Budget {
  id: number;
  user_id: number;
  category_id: number;
  name: string;
  amount: string;
  period: BudgetPeriod;
  start_date: string;
  end_date: string | null;
  rollover: boolean;
  alert_enabled: boolean;
  alert_threshold: string;
  created_at: string;
  updated_at: string | null;
}

export interface BudgetCreate {
  category_id: number;
  name: string;
  amount: string;
  period: BudgetPeriod;
  start_date: string;
  end_date?: string;
  rollover?: boolean;
  alert_enabled?: boolean;
  alert_threshold?: string;
}

export interface BudgetUpdate {
  category_id?: number;
  name?: string;
  amount?: string;
  period?: BudgetPeriod;
  start_date?: string;
  end_date?: string;
  rollover?: boolean;
  alert_enabled?: boolean;
  alert_threshold?: string;
}

export interface BudgetWithProgress extends Budget {
  spent: string;
  remaining: string;
  percentage: string;
  is_over_budget: boolean;
}

// Dashboard types
export interface AccountSummary {
  total_assets: string;
  total_liabilities: string;
  net_worth: string;
}

export interface CategorySpending {
  category_id: number;
  category_name: string;
  amount: string;
  percentage: string;
  transaction_count: number;
}

export interface IncomeVsExpenses {
  total_income: string;
  total_expenses: string;
  net: string;
  savings_rate: string;
}

export interface MonthlyTrend {
  month: string;
  income: string;
  expenses: string;
  net: string;
}

export interface BudgetStatus {
  budget_id: number;
  budget_name: string;
  category_name: string;
  amount: string;
  spent: string;
  remaining: string;
  percentage: string;
  is_over_budget: boolean;
  alert_threshold: string;
}

export interface DashboardSummary {
  account_summary: AccountSummary;
  income_vs_expenses: IncomeVsExpenses;
  budget_status: BudgetStatus[];
  top_spending_categories: CategorySpending[];
  period_start: string;
  period_end: string;
}

export interface SpendingByCategoryResponse {
  total_spending: string;
  categories: CategorySpending[];
  period_start: string;
  period_end: string;
}

export interface IncomeVsExpensesResponse {
  current_period: IncomeVsExpenses;
  monthly_trends: MonthlyTrend[];
  period_start: string;
  period_end: string;
}

// API Error types
export interface APIError {
  detail: string | { msg: string; type: string }[];
}
