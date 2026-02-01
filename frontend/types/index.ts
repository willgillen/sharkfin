// User types
export type IconProvider = "simple_icons" | "logo_dev";

// Date format options
export type DateFormat = "MM/DD/YYYY" | "DD/MM/YYYY" | "YYYY-MM-DD" | "MMM D, YYYY";

// Number format options
export type NumberFormat = "1,234.56" | "1.234,56" | "1 234.56";

// Currency position
export type CurrencyPosition = "before" | "after";

// Start of week
export type StartOfWeek = "sunday" | "monday";

// Rows per page options
export type RowsPerPage = 25 | 50 | 100;

// Transaction sort columns
export type TransactionSortColumn = "date" | "payee" | "amount" | "category";

// Sort order
export type SortOrder = "asc" | "desc";

// Duplicate detection strictness
export type DuplicateStrictness = "strict" | "moderate" | "relaxed";

export interface UserPreferences {
  // Display preferences
  date_format?: DateFormat;
  number_format?: NumberFormat;
  currency_symbol?: string;
  currency_position?: CurrencyPosition;
  currency_decimals?: number;
  start_of_week?: StartOfWeek;

  // Transaction preferences
  transactions_sort_column?: TransactionSortColumn;
  transactions_sort_order?: SortOrder;
  transactions_rows_per_page?: RowsPerPage;
  transactions_visible_columns?: Record<string, boolean>;

  // Import preferences
  import_auto_create_payees?: boolean;
  import_auto_apply_rules?: boolean;
  import_duplicate_strictness?: DuplicateStrictness;
  import_default_account_id?: number;

  // Appearance preferences
  icon_provider?: IconProvider;

  // Allow other fields for flexibility
  [key: string]: any;
}

// Preference metadata for UI rendering
export interface PreferenceOption {
  value: string | number | boolean;
  label: string;
}

export interface PreferenceMetadataItem {
  type: "select" | "boolean" | "number" | "string";
  label: string;
  description: string;
  category: string;
  default: any;
  options?: PreferenceOption[];
  min?: number;
  max?: number;
}

export interface PreferencesMetadata {
  categories: Record<string, string[]>;
  preferences: Record<string, PreferenceMetadataItem>;
}

export interface User {
  id: number;
  email: string;
  full_name: string;
  is_active: boolean;
  is_superuser: boolean;
  ui_preferences: UserPreferences | null;
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
  ui_preferences?: Record<string, any>;
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
  opening_balance: string;
  opening_balance_date: string | null;
  current_balance: string;  // Calculated field from API
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
  opening_balance: string;
  opening_balance_date?: string;
  currency?: string;
  is_active?: boolean;
  notes?: string;
}

export interface AccountUpdate {
  name?: string;
  type?: AccountType;
  institution?: string;
  account_number?: string;
  opening_balance?: string;
  opening_balance_date?: string;
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

// Payee types
export interface Payee {
  id: number;
  user_id: number;
  canonical_name: string;
  default_category_id: number | null;
  payee_type: string | null;
  logo_url: string | null;
  notes: string | null;
  transaction_count: number;
  last_used_at: string | null;
  created_at: string;
  updated_at: string | null;
}

export interface PayeeWithCategory extends Payee {
  default_category_name: string | null;
}

export interface PayeeCreate {
  canonical_name: string;
  default_category_id?: number;
  payee_type?: string;
  logo_url?: string;
  notes?: string;
}

export interface PayeeUpdate {
  canonical_name?: string;
  default_category_id?: number;
  payee_type?: string;
  logo_url?: string;
  notes?: string;
}

// Payee autocomplete response
export interface PayeeSuggestion {
  id: number;
  canonical_name: string;
  default_category_id: number | null;
  transaction_count: number;
  default_category_name: string | null;
}

// Payee transaction list item
export interface PayeeTransaction {
  id: number;
  date: string;
  amount: string;
  type: string;
  account_id: number;
  account_name: string;
  category_id: number | null;
  category_name: string | null;
  description: string | null;
}

// Payee spending statistics
export interface PayeeStats {
  total_spent_all_time: string;
  total_spent_this_month: string;
  total_spent_this_year: string;
  total_income_all_time: string;
  average_transaction_amount: string | null;
  transaction_count: number;
  first_transaction_date: string | null;
  last_transaction_date: string | null;
}

// Payee matching patterns
export type PatternType = "description_contains" | "exact_match" | "fuzzy_match_base" | "description_regex";

export interface PayeePattern {
  id: number;
  payee_id: number;
  pattern_type: PatternType;
  pattern_value: string;
  confidence_score: string;
  match_count: number;
  last_matched_at: string | null;
  source: string;
  created_at: string;
}

export interface PayeePatternCreate {
  pattern_type: PatternType;
  pattern_value: string;
  confidence_score?: string;
}

export interface PayeePatternUpdate {
  pattern_type?: PatternType;
  pattern_value?: string;
  confidence_score?: string;
}

export interface PatternTestResult {
  matches: boolean;
  pattern_type: string;
  pattern_value: string;
  description: string;
  match_details: string | null;
}

// Payee icon types
export type IconType = "brand" | "emoji" | "custom" | "none";

export interface IconSuggestion {
  icon_type: "brand" | "emoji";
  icon_value: string;
  brand_color: string | null;
  matched_term: string | null;
  confidence: number;
  slug?: string;
  emoji?: string;
}

export interface IconParsed {
  type: IconType;
  value: string | null;
  display_value: string;
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
  payee_id: number | null;
  type: TransactionType;
  amount: string;
  date: string;
  description: string;
  notes: string | null;
  payee: string | null;  // Legacy field - use payee_name instead
  payee_name: string | null;  // Payee name from linked Payee entity
  payee_logo_url: string | null;  // Payee logo URL for visual display
  is_starred: boolean;
  is_recurring: boolean;
  tags: string[];
  created_at: string;
  updated_at: string | null;
  running_balance: string | null;  // Running balance after this transaction (only when filtering by account)
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

// Import types
export interface CSVColumnMapping {
  date: string;
  amount: string;
  description?: string;
  payee?: string;
  category?: string;
  notes?: string;
}

export interface CSVPreviewResponse {
  columns: string[];
  sample_rows: Record<string, any>[];
  detected_format?: string;
  suggested_mapping?: CSVColumnMapping;
  row_count: number;
}

export interface OFXPreviewResponse {
  account_name: string;
  account_type: string;
  account_number?: string;
  bank_name?: string;
  start_date?: string;
  end_date?: string;
  transaction_count: number;
  sample_transactions: any[];
}

export interface PotentialDuplicate {
  existing_transaction_id: number;
  existing_date: string;
  existing_amount: string;
  existing_description?: string;
  new_transaction: Record<string, any>;
  confidence_score: number;
}

export interface DuplicatesResponse {
  duplicates: PotentialDuplicate[];
  total_new_transactions: number;
  total_duplicates: number;
}

export interface ImportExecuteResponse {
  import_id: number;
  status: string;
  total_rows: number;
  imported_count: number;
  duplicate_count: number;
  error_count: number;
  message: string;
}

export interface ImportHistoryResponse {
  id: number;
  import_type: "csv" | "ofx" | "qfx";
  filename: string;
  file_size?: number;
  account_id?: number;
  account_name?: string;
  total_rows: number;
  imported_count: number;
  duplicate_count: number;
  error_count: number;
  status: "pending" | "completed" | "failed" | "cancelled";
  started_at: string;
  completed_at?: string;
  can_rollback: boolean;
  original_file_name?: string;
  original_file_size?: number;
  has_file_data?: boolean;
}

// Smart Rule Suggestions during Import
export interface SmartRuleSuggestionResponse {
  suggested_name: string;
  payee_pattern: string;
  payee_match_type: string;
  matching_row_indices: number[];
  sample_descriptions: string[];
  confidence: number;
  detected_merchant?: string;
  extracted_payee_name?: string;
  extraction_confidence?: number;
}

export interface AnalyzeImportForRulesRequest {
  transactions: Record<string, any>[];
  min_occurrences?: number;
  min_confidence?: number;
}

export interface AnalyzeImportForRulesResponse {
  suggestions: SmartRuleSuggestionResponse[];
  total_transactions_analyzed: number;
  total_suggestions: number;
}

// Categorization Rule types
export enum MatchType {
  CONTAINS = "contains",
  STARTS_WITH = "starts_with",
  ENDS_WITH = "ends_with",
  EXACT = "exact",
  REGEX = "regex",
}

export enum TransactionTypeFilter {
  DEBIT = "DEBIT",
  CREDIT = "CREDIT",
  TRANSFER = "TRANSFER",
}

export interface CategorizationRule {
  id: number;
  user_id: number;
  name: string;
  priority: number;
  enabled: boolean;
  payee_pattern?: string;
  payee_match_type?: MatchType;
  description_pattern?: string;
  description_match_type?: MatchType;
  amount_min?: string;
  amount_max?: string;
  transaction_type?: TransactionTypeFilter;
  category_id?: number;
  new_payee?: string;
  notes_append?: string;
  created_at: string;
  updated_at: string;
  last_matched_at?: string;
  match_count: number;
  auto_created: boolean;
  confidence_score?: string;
}

export interface CategorizationRuleCreate {
  name: string;
  priority?: number;
  enabled?: boolean;
  payee_pattern?: string;
  payee_match_type?: MatchType;
  description_pattern?: string;
  description_match_type?: MatchType;
  amount_min?: string;
  amount_max?: string;
  transaction_type?: TransactionTypeFilter;
  category_id?: number;
  new_payee?: string;
  notes_append?: string;
}

export interface CategorizationRuleUpdate {
  name?: string;
  priority?: number;
  enabled?: boolean;
  payee_pattern?: string;
  payee_match_type?: MatchType;
  description_pattern?: string;
  description_match_type?: MatchType;
  amount_min?: string;
  amount_max?: string;
  transaction_type?: TransactionTypeFilter;
  category_id?: number;
  new_payee?: string;
  notes_append?: string;
}

export interface RuleTestRequest {
  payee?: string;
  description?: string;
  amount: string;
  transaction_type: TransactionTypeFilter;
}

export interface RuleTestResponse {
  matches: boolean;
  matched_conditions: string[];
  actions_to_apply: Record<string, any>;
}

export interface BulkApplyRulesRequest {
  transaction_ids?: number[];
  rule_ids?: number[];
  overwrite_existing?: boolean;
}

export interface BulkApplyRulesResponse {
  total_processed: number;
  categorized_count: number;
  skipped_count: number;
  rules_used: number;
  transactions_updated: number[];
}

export interface RuleSuggestion {
  suggested_rule_name: string;
  payee_pattern?: string;
  payee_match_type?: MatchType;
  description_pattern?: string;
  description_match_type?: MatchType;
  amount_min?: string;
  amount_max?: string;
  transaction_type?: TransactionTypeFilter;
  category_id: number;
  category_name: string;
  confidence_score: number;
  match_count: number;
  sample_transactions: number[];
}

export interface SuggestRulesRequest {
  min_occurrences?: number;
  min_confidence?: number;
}

export interface AcceptSuggestionRequest {
  suggested_rule_name: string;
  payee_pattern?: string;
  payee_match_type?: MatchType;
  description_pattern?: string;
  description_match_type?: MatchType;
  amount_min?: string;
  amount_max?: string;
  transaction_type?: TransactionTypeFilter;
  category_id: number;
  priority?: number;
  enabled?: boolean;
}

// Settings types
export interface IconProviderInfo {
  available: boolean;
  requires_api_key: boolean;
  requires_attribution: boolean;
  description: string;
}

export interface IconProviderStatus {
  providers: {
    simple_icons: IconProviderInfo;
    logo_dev: IconProviderInfo;
  };
  default_provider: IconProvider;
}

export interface LogoDevSettings {
  api_key_configured: boolean;
  description: string;
}

export interface LogoDevSettingsUpdate {
  api_key: string | null;
}
