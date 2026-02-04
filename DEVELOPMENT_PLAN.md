# Shark Fin - Development Plan

## Project Overview

A self-hosted, open-source financial planning, budgeting, and management application built with:
- **Frontend**: Next.js (React framework with SSR)
- **Backend**: Python with FastAPI
- **Database**: PostgreSQL
- **Deployment**: Docker Compose for containerization

This application aims to provide feature parity with applications like Mint (now discontinued) and Firefly III, offering users complete control over their financial data through self-hosting.

## Development Progress Checklist

**Last Updated**: February 1, 2026
**Current Phase**: Phase 2 - Advanced Features (Week 18-19: Goals & Advanced Reporting)



#### 12.3 Saved Column Mapping Templates
- [ ] Create `column_mapping_templates` table (migration)
- [ ] CRUD API endpoints for templates
- [ ] Save/load mapping templates in import wizard
- [ ] Auto-detect matching template based on CSV headers (>80% match)
- [ ] Frontend: Template selector dropdown, "Save Mapping" button
- [ ] Tests: `test_save_column_mapping_template()`, `test_auto_detect_matching_template()`

#### 12.4 Drag-and-Drop Column Mapping UI
- [ ] Install `react-beautiful-dnd` or `dnd-kit`
- [ ] Rewrite MapColumnsStep with drag-and-drop interface
- [ ] Left panel: Available CSV columns (draggable)
- [ ] Right panel: Target fields (drop zones)
- [ ] Live preview of mapped data
- [ ] Visual indicators for required vs optional fields

#### 12.5 Import Process Transparency & Logging
- [ ] Create `import_logs` table (migration)
- [ ] Create "Review Plan" step showing actions before execution
- [ ] User toggles: Auto-create payees, Auto-apply rules, Skip duplicates
- [ ] Log all import events (INFO, WARNING, ERROR levels)
- [ ] Frontend: Import log viewer with filtering
- [ ] Tests: `test_import_log_creation()`, `test_review_plan_shows_actions()`

#### 12.6 Enhanced Rollback/Undo
- [ ] Create `import_created_entities` table (tracks all created entities)
- [ ] Track: transactions, payees, rules, categories created during import
- [ ] Cascade rollback to delete all created entities
- [ ] Safeguards: prevent rollback if transactions modified or payees reused
- [ ] Impact analysis before rollback
- [ ] Tests: `test_rollback_deletes_created_payees()`, `test_rollback_prevents_if_transactions_modified()`

### Week 13: Payee System Enhancements
**Priority**: Medium-High - Payee Management & Visual Identity


#### Phase D: Advanced Features (13.7-13.10)

##### 13.7 Payee Aliases
- [ ] Add `payee_aliases` table (payee_id, alias_name, created_at)
- [ ] API endpoints for alias CRUD
- [ ] Frontend: Aliases section on payee edit page
- [ ] During import, check aliases for matching
- [ ] Tests: `test_payee_alias_matching()`

##### 13.8 Merge Payees
- [ ] Add API endpoint: `POST /api/v1/payees/{id}/merge`
- [ ] Accept target_payee_id, migrate all transactions
- [ ] Merge patterns and aliases to target payee
- [ ] Delete source payee after merge
- [ ] Frontend: "Merge into another payee" button with search
- [ ] Tests: `test_merge_payees_migrates_transactions()`

##### 13.9 Similar Payees Detection
- [ ] Add API endpoint: `GET /api/v1/payees/{id}/similar`
- [ ] Use fuzzy matching to find similar payee names
- [ ] Frontend: "Similar payees" suggestion on edit page
- [ ] Quick merge button for obvious duplicates
- [ ] Tests: `test_similar_payees_detection()`

##### 13.10 Orphaned Payees Cleanup
- [ ] Add API endpoint: `GET /api/v1/payees/orphaned`
- [ ] Return payees with 0 transactions
- [ ] Frontend: "Cleanup" section in payee list with bulk delete
- [ ] Tests: `test_orphaned_payees_detection()`

---

### Week 16: Settings & Preferences System ✅ COMPLETE
**Priority**: High - Infrastructure for Future Features
**Status**: Completed February 1, 2026

> **Architecture Note**: Settings are split into two categories:
> - **App Settings** (`app_settings` table): System-wide configuration (API keys, server defaults)
> - **User Preferences** (`users.ui_preferences` JSONB): Per-user display and behavior preferences
>
> This architecture was established during Logo.dev integration (see `IconProviderSettings`).

#### 16.1 Settings Infrastructure ✅ COMPLETE
- [x] `app_settings` table for system-wide settings (API keys, etc.)
- [x] `AppSettingsService` for app settings CRUD
- [x] `users.ui_preferences` JSONB column for per-user preferences
- [x] `UserPreferences` Pydantic schema with validation
- [x] Basic settings API at `/api/v1/settings/...`
- [x] User preferences updated via `PUT /api/v1/users/me`
- [x] `UserPreferencesService` with typed getters/setters and defaults
- [x] `DEFAULT_USER_PREFERENCES` constant with all default values
- [x] `GET /api/v1/users/me/preferences` endpoint (returns merged defaults + user prefs)
- [x] `PATCH /api/v1/users/me/preferences` endpoint (partial update)
- [x] `DELETE /api/v1/users/me/preferences/{key}` endpoint (reset to default)
- [x] Expanded `UserPreferences` schema with all preference fields
- [x] Tests: 24 tests passing for preferences service and endpoints

#### 16.2 Settings UI ✅ COMPLETE
- [x] Refactored Settings page with category-based navigation layout
- [x] Left sidebar: Category tabs (Display, Transactions, Import, API Keys)
- [x] Right panel: Settings for selected category
- [x] Reusable `SettingItem` component supporting toggle, select, text, number inputs
- [x] Help text/description under each setting
- [x] "Reset to Default" button per setting
- [x] Components: `SettingsNav.tsx`, `SettingItem.tsx`, category-specific preference components

#### 16.3 Display Preferences ✅ COMPLETE
- [x] Date format selector (MM/DD/YYYY, DD/MM/YYYY, YYYY-MM-DD, MMM D, YYYY)
- [x] Number format selector (1,234.56 vs 1.234,56 vs 1 234.56)
- [x] Currency symbol preference
- [x] Currency position preference (before/after amount)
- [x] Decimal places preference (0-4)
- [x] Start of week preference (Sunday/Monday)

#### 16.4 Transaction Preferences ✅ COMPLETE
- [x] Default sort column preference (date, payee, amount, category)
- [x] Default sort order preference (asc/desc)
- [x] Rows per page preference (25, 50, 100)
- [x] Visible columns preference (persist column toggle state)

#### 16.5 Import Preferences ✅ COMPLETE
- [x] Auto-create payees toggle (default: true)
- [x] Auto-apply rules toggle (default: true)
- [x] Duplicate detection strictness (strict, moderate, relaxed)
- [x] Default account for imports preference

#### 16.6 Account-Centric Transactions View ✅ COMPLETE (Added)
- [x] `AccountSelector` component for prominent account selection
- [x] Transactions page always views one account at a time
- [x] Account selection persisted in URL (?account=123)
- [x] QuickAddBar uses selected account automatically (no dropdown)
- [x] Running balance always available (single account filter)

### Week 17: Testing & Development Tools
**Priority**: Medium - Developer Experience & UAT Support

#### 17.1 Database Reset Scripts
- [ ] Create `backend/scripts/db_reset.sh` and `db_reset.py`
- [ ] Commands: `--full` (drop all), `--soft` (keep users), `--transactions`, `--accounts`, `--payees`
- [ ] `--seed` flag to reseed after reset
- [ ] `--user` flag to reset specific user data
- [ ] Safety: Require confirmation, only allow in dev environment
- [ ] Docker integration: `docker-compose exec backend python scripts/db_reset.py`
- [ ] Tests: `test_soft_reset_keeps_users()`, `test_full_reset_clears_all()`

#### 17.2 Enhanced Seed Data
- [ ] Create `enhanced_seeds.py` with realistic test data
- [ ] Multiple users (demo, heavy volume, minimal data)
- [ ] Diverse accounts (checking, savings, credit cards, loans, investments)
- [ ] 500+ realistic transactions per user (12 months)
- [ ] Recurring bills, groceries, restaurants, entertainment, healthcare
- [ ] Major retailers with appropriate logos/emojis
- [ ] Full category tree with subcategories
- [ ] Budgets with over/under scenarios
- [ ] Import history examples
- [ ] Tests: Test seed script integrity

#### 17.3 Test Data Factories
- [ ] Install Factory Boy
- [ ] Create `backend/app/tests/factories.py`
- [ ] Factories: UserFactory, AccountFactory, TransactionFactory, PayeeFactory, CategoryFactory
- [ ] Use in tests to reduce boilerplate
- [ ] Support sequences and randomization
- [ ] Tests: Example usage in existing tests

---

**UAT Refinement Phase Status**: 📋 Planned - Inserting before advanced features
**Total Duration**: 7 weeks (Weeks 11-17)
**Deliverables**: 50+ improvements, 100+ new tests, professional UI polish, settings system
**Success Criteria**: All 44 UAT observations addressed, >85% test coverage, no critical bugs

---

## Phase 2 (Continued): Advanced Features (Weeks 18-24)

#### Week 18-19: Reports & Analytics 🚀 CURRENT FOCUS
**Priority**: High - Core reporting capabilities for financial insight

> **Current State**: Reports page consolidated as main Dashboard with full reporting capabilities.
> - Dashboard/Reports page at `/dashboard/reports` with sidebar navigation
> - Net Worth, Spending Trends, Income vs Expenses, Cash Flow Forecast, Sankey Diagram reports
> - Date range picker, account filtering, PDF export
> - Budget status integrated into Overview

##### 18.1 Reports Infrastructure & Navigation (Priority 1) ✅ COMPLETE
- [x] Create `/dashboard/reports` page with report type selector
- [x] Create `ReportsLayout` component with sidebar navigation
- [x] Add date range picker component (preset ranges: MTD, QTD, YTD, Last 30/90 days, Custom)
- [ ] Create `useReportData` hook for loading with caching (not implemented - data loaded directly)
- [x] Add account filter support (single account or all accounts)
- [x] Create shared `ReportHeader` component (title, date range, export button)
- [x] Consolidated Dashboard into Reports page (Dashboard now redirects to Reports/Overview)

##### 18.2 Net Worth Report (Priority 2) ✅ COMPLETE
**Business Value**: Track financial progress over time
- [x] Backend: `GET /api/v1/reports/net-worth-history` endpoint
  - Calculate net worth at end of each month (assets - liabilities)
  - Support date range parameter
  - Return array of {month, assets, liabilities, net_worth}
- [x] Frontend: `NetWorthReport` page component (integrated into Reports page)
- [x] Line chart: Net worth trend over time (`NetWorthChart` component)
- [x] Stacked area chart: Assets vs Liabilities breakdown
- [x] Summary cards: Current net worth, Change since last period, All-time high
- [x] Account breakdown table showing contribution to net worth
- [x] Tests: `test_net_worth_history()`, `test_net_worth_history_with_account_filter()`

##### 18.3 Spending Trends Report (Priority 3) ✅ COMPLETE
**Business Value**: Understand spending patterns and identify areas for improvement
- [x] Backend: `GET /api/v1/reports/spending-trends` endpoint
  - Monthly spending by category over time
  - Support comparison periods (this month vs last month, this year vs last year)
  - Calculate average spending per category
- [x] Frontend: `SpendingTrendsReport` page component (integrated into Reports page)
- [x] Stacked bar chart: Monthly spending by top categories (`SpendingTrendsChart`)
- [ ] Heat map: Spending by category over months (POSTPONED)
- [x] Month-over-month comparison with change indicators (↑↓) - Added to summary card and category table
- [x] Drill-down: Click category to see transactions - CategorySpendingChart now clickable
- [x] Tests: `test_spending_trends()`, `test_spending_trends_with_category_filter()`

##### 18.4 Income vs Expenses Report (Priority 4) ✅ COMPLETE
**Business Value**: Monitor cash flow and savings rate
- [x] Backend: Enhance existing `/api/v1/reports/income-vs-expenses`
  - Add income source breakdown (via income-expense-detail endpoint)
  - Add expense category breakdown
  - [ ] Add year-over-year comparison (POSTPONED)
- [x] Frontend: `IncomeVsExpensesReport` page component (integrated into Reports page)
- [x] Dual bar chart: Income vs Expenses by month (`IncomeTrendChart`)
- [x] Sankey diagram: Income sources → Expense categories (separate report)
- [x] Savings rate trend line (shown in monthly breakdown)
- [ ] Income stability metrics (variance, consistency) (POSTPONED)
- [x] Tests: `test_income_expense_detail()`

##### 18.5 Cash Flow Forecast (Priority 5) ✅ COMPLETE
**Business Value**: Plan ahead and avoid cash shortfalls
- [x] Backend: `GET /api/v1/reports/cash-flow-forecast` endpoint
  - Analyze recurring transactions (bills, income)
  - Project forward 30/60/90 days
  - [x] Detect recurring bills with automatic pattern detection
  - Calculate projected balance by date
- [x] Frontend: `CashFlowForecastReport` page component (integrated into Reports page)
- [x] Timeline chart: Projected balance over next 90 days (`CashFlowForecastChart`)
- [x] Upcoming/recurring bills list with due dates and amounts (pattern-detected)
- [x] Warning indicators for low balance periods (confidence indicators)
- [ ] "What-if" toggle to exclude planned expenses (POSTPONED)
- [x] Tests: `test_cash_flow_forecast()`

##### 18.6 Cash Flow Sankey Diagram (Priority 6) ✅ COMPLETE
**Business Value**: Visualize the complete flow of money from income sources through to expenses/savings
- [x] Backend: `GET /api/v1/reports/sankey-diagram` endpoint
  - Aggregate income by source (payee/category)
  - Aggregate expenses by category (top-level groupings)
  - [ ] Calculate intermediate flows (Gross Income → Tax Withholding → Net Income) (POSTPONED)
  - [ ] Support custom grouping levels (show sub-categories or roll up) (POSTPONED)
  - Return nodes and links for Sankey visualization
- [x] Frontend: `CashFlowSankeyReport` page component (integrated into Reports page)
- [x] Use recharts Sankey for visualization (`SankeyDiagramChart`)
- [x] Left side: Income sources (Salary, Other Income, etc.)
- [ ] Middle: Intermediate aggregations (POSTPONED - direct flow works well)
- [x] Right side: Outflow destinations (Expenses by category, Savings)
- [ ] Far right: Detailed breakdown (POSTPONED)
- [x] Interactive: Hover to highlight flow path (tooltips implemented)
- [x] Date range filter integration
- [x] Account filter support (single account or all accounts)
- [x] Tests: `test_sankey_diagram()`, `test_sankey_diagram_with_date_range()`

##### 18.7 Report Export (All Reports) ✅ COMPLETE
- [x] Add PDF export using html2canvas + jspdf (all reports)
- [x] Add CSV export for data download (transactions export on Transactions page)
- [x] Tests: `test_export_transactions_csv()`, `test_export_transactions_csv_with_payee_entity()`
- [ ] Add Excel export option (xlsx) (POSTPONED)
- [ ] Email report option (POSTPONED - future enhancement)
- [ ] Scheduled report generation (POSTPONED - future enhancement)

#### Week 20-21: Bill Tracking & Recurring Transactions ⏳
- [ ] Backend: Recurring transaction templates
- [ ] Backend: Automated transaction generation engine
- [ ] Backend: Schedule management (daily, weekly, monthly, yearly)
- [ ] Backend: Bill reminders system
- [ ] Frontend: Recurring transactions page
- [ ] Frontend: Template creation and editing
- [ ] Frontend: Calendar view of upcoming bills
- [ ] Frontend: Subscription detection interface
- [ ] Tests: Recurring transactions test coverage

#### Week 22-24: Data Management & Backup ⏳
- [ ] Backend: Full data backup export
- [ ] Backend: Data restore functionality
- [ ] Backend: Import history tracking improvements
- [ ] Backend: Data migration tools
- [ ] Frontend: Backup/restore interface
- [ ] Frontend: Import history enhancements
- [ ] Tests: Backup and restore tests


### Phase 3: Premium Features ⏳ PLANNED

#### Week 17-20: Investment Tracking
- [ ] Backend: Investment account type support
- [ ] Backend: Portfolio holdings tracking
- [ ] Backend: Performance metrics (ROI, gains/losses)
- [ ] Backend: Dividend tracking
- [ ] Backend: Asset allocation calculations
- [ ] Frontend: Portfolio management page
- [ ] Frontend: Investment performance charts
- [ ] Frontend: Asset allocation visualization
- [ ] Tests: Investment tracking test coverage

#### Week 21-22: Analytics & ML Features
- [ ] Backend: Spending pattern detection
- [ ] Backend: Anomaly detection algorithms
- [ ] Backend: Predictive budgeting engine
- [ ] Backend: Spending insights generation
- [ ] Frontend: Insights dashboard
- [ ] Frontend: Spending pattern visualization
- [ ] Frontend: Predictive budget suggestions
- [ ] Tests: Analytics and ML tests

#### Week 23-24: Advanced Features
- [ ] Backend: Credit score integration (API)
- [ ] Backend: Tax report generation
- [ ] Backend: Custom report builder engine
- [ ] Frontend: Credit score monitoring page
- [ ] Frontend: Tax reports interface
- [ ] Frontend: Custom report builder UI
- [ ] Tests: Advanced features test coverage

**Phase 3 Status**: ⏳ Planned

### Phase 4: Mobile & Collaboration ⏳ FUTURE

#### Mobile Application
- [ ] React Native project setup
- [ ] Mobile UI components
- [ ] Quick transaction entry
- [ ] Receipt capture with OCR
- [ ] Push notifications
- [ ] Biometric authentication
- [ ] Offline mode support

#### Collaboration Features
- [ ] Shared budgets support
- [ ] Multi-user accounts
- [ ] Permission levels (view/edit)
- [ ] Activity log/audit trail
- [ ] Comments on transactions
- [ ] User invitations system

**Phase 4 Status**: ⏳ Future development



### Phase 5: Additional UAT Observations



---

## Technology Stack

### Frontend
- **Framework**: Next.js 14+ with App Router
- **UI Library**: React 18+
- **Styling**: Tailwind CSS (recommended for rapid development)
- **Charts/Visualizations**: Recharts or Chart.js
- **State Management**: React Context API / Zustand
- **API Client**: Axios or native fetch with SWR for data fetching
- **Forms**: React Hook Form with Zod validation

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **ORM**: SQLAlchemy 2.0+
- **Migrations**: Alembic
- **Validation**: Pydantic v2
- **Authentication**: JWT tokens with FastAPI dependencies
- **Testing**: Pytest with HTTPX
- **ASGI Server**: Uvicorn (development) / Gunicorn + Uvicorn (production)

### Database
- **Primary Database**: PostgreSQL 15+
- **Caching Layer**: Redis (for sessions, rate limiting)
- **Connection Pooling**: SQLAlchemy pool configuration

### DevOps & Infrastructure
- **Containerization**: Docker with multi-stage builds
- **Orchestration**: Docker Compose
- **Reverse Proxy**: Traefik or Nginx
- **CI/CD**: GitHub Actions
- **Version Control**: Git with GitHub

## Core Features (MVP - Phase 1)

### 1. Account Management
- **Manual Account Creation**: Support for checking, savings, credit cards, loans, investments
- **Multi-Currency Support**: Track accounts in different currencies with exchange rate management
- **Account Types**:
  - Asset accounts (checking, savings, cash)
  - Liability accounts (credit cards, loans)
  - Revenue accounts (income sources)
  - Expense accounts (spending categories)

### 2. Transaction Management
- **Manual Transaction Entry**: Quick entry interface with keyboard shortcuts
- **Bulk Import**: CSV/OFX/QFX file import with mapping configuration
- **Transaction Fields**:
  - Date, amount, payee/merchant
  - Category and tags
  - Notes/memo
  - Attachments (receipts, invoices)
- **Split Transactions**: Divide single transaction across multiple categories
- **Transfer Detection**: Automatically identify transfers between accounts
- **Recurring Transactions**: Schedule repeating income/expenses

### 3. Categorization & Organization
- **Custom Categories**: Hierarchical category structure (parent/child)
- **Smart Tagging**: Multiple tags per transaction for flexible organization
- **Auto-Categorization**: Rule-based automatic categorization
- **Category Groups**: Organize categories by type (needs, wants, savings)

### 4. Budgeting System
- **Budget Creation**: Monthly, quarterly, annual budgets
- **Category-Based Budgets**: Set limits per category or group
- **Budget Types**:
  - Fixed amount budgets
  - Percentage-based budgets
  - Rollover budgets (unused amounts carry forward)
- **Budget Alerts**: Notifications at 50%, 75%, 90%, 100% thresholds
- **Budget vs Actual Reports**: Visual comparison of planned vs actual spending

### 5. Reporting & Analytics
- **Dashboard Overview**:
  - Net worth trends
  - Cash flow summary (income vs expenses)
  - Top spending categories
  - Budget status overview
- **Transaction Reports**:
  - Spending by category (pie/bar charts)
  - Income vs expenses over time (line charts)
  - Month-over-month comparisons
  - Year-over-year trends
- **Custom Date Ranges**: Filter reports by any time period
- **Export Capabilities**: Export reports as PDF, CSV, Excel

### 6. Financial Goals
- **Savings Goals**: Set target amounts with deadlines
- **Debt Payoff Goals**: Track progress on loan/credit card payoff
- **Piggy Banks**: Allocate funds from existing accounts toward goals
- **Progress Tracking**: Visual indicators showing goal completion percentage
- **Goal Milestones**: Set intermediate targets

### 7. Authentication & Security
- **User Management**: Registration, login, password reset
- **JWT Authentication**: Secure token-based auth
- **Password Security**: Bcrypt hashing, minimum strength requirements
- **Session Management**: Secure session handling with expiration
- **Multi-User Support**: Separate data isolation per user
- **2FA (Future)**: Two-factor authentication for enhanced security

## Advanced Features (Phase 2)

### 8. Bill Tracking & Reminders
- **Bill Calendar**: Visual calendar of upcoming bills
- **Bill Reminders**: Email/push notifications before due dates
- **Recurring Bill Management**: Track regular bills (utilities, subscriptions)
- **Bill Payment Tracking**: Mark bills as paid/unpaid
- **Subscription Detection**: Identify and track subscription services

### 9. Investment Tracking
- **Portfolio Management**: Track stocks, bonds, mutual funds, ETFs
- **Asset Allocation**: View portfolio distribution
- **Performance Metrics**: ROI, gains/losses, dividend tracking
- **Manual Price Updates**: Update security prices manually
- **Investment Goals**: Track investment performance against goals

### 10. Advanced Reporting
- **Cash Flow Forecasting**: Predict future balances based on recurring transactions
- **Spending Trends Analysis**: Identify spending patterns and anomalies
- **Category Trends**: Track category spending changes over time
- **Net Worth Tracking**: Historical net worth with trend visualization
- **Tax Reports**: Annual summaries for tax preparation
- **Custom Reports Builder**: Create custom queries and visualizations

### 11. Rules Engine
- **Auto-Categorization Rules**: IF/THEN rules for automatic categorization
- **Transaction Modification**: Automatically rename, split, or tag transactions
- **Condition Matching**:
  - Payee contains/matches text
  - Amount greater/less than
  - Description patterns
- **Rule Priority**: Order rules by execution priority
- **Bulk Rule Application**: Apply rules to historical transactions

### 12. Data Import/Export
- **Bank Import Formats**:
  - CSV with configurable column mapping
  - OFX/QFX (Open Financial Exchange)
  - QIF (Quicken Interchange Format)
- **Import History**: Track what files have been imported
- **Duplicate Detection**: Prevent duplicate transaction imports
- **Full Data Export**: Export complete database for backup/migration
- **Scheduled Exports**: Automatic periodic backups

## Premium Features (Phase 3)

### 13. Account Aggregation (via Plaid/Similar)
- **Bank Connection**: Connect to 17,000+ financial institutions
- **Automatic Sync**: Daily transaction synchronization
- **Balance Updates**: Real-time account balance tracking
- **Institution Management**: Add/remove/reauthorize connections
- **Sync History**: Track last sync time per account

### 14. Credit Score Monitoring
- **Credit Score Integration**: Display credit score (via third-party API)
- **Score Trends**: Track credit score changes over time
- **Credit Report Summary**: Key factors affecting score
- **Improvement Tips**: Suggestions for improving credit score

### 15. Mobile Application
- **React Native App**: iOS and Android mobile apps
- **Quick Entry**: Fast transaction entry on the go
- **Receipt Capture**: Camera-based receipt scanning with OCR
- **Push Notifications**: Bill reminders, budget alerts
- **Biometric Auth**: Face ID / Touch ID support
- **Offline Mode**: Cache data for offline access

### 16. Collaboration Features
- **Shared Budgets**: Multi-user access to single budget
- **Family Accounts**: Separate user accounts with shared visibility
- **Permission Levels**: View-only vs edit access
- **Activity Log**: Audit trail of all changes
- **Comments**: Add notes/discussions on transactions

### 17. Advanced Analytics
- **Machine Learning Insights**:
  - Spending pattern detection
  - Unusual transaction alerts
  - Predictive budgeting suggestions
- **Comparative Analytics**: Compare your spending to averages (anonymized)
- **Scenario Planning**: "What-if" analysis for financial decisions
- **Retirement Planning**: Long-term financial projection tools

## Technical Architecture

### Project Structure

```
shark-fin/
├── frontend/                    # Next.js application
│   ├── src/
│   │   ├── app/                # App router pages
│   │   │   ├── (auth)/        # Auth group routes
│   │   │   ├── dashboard/     # Main dashboard
│   │   │   ├── transactions/  # Transaction management
│   │   │   ├── budgets/       # Budget management
│   │   │   ├── accounts/      # Account management
│   │   │   ├── reports/       # Reports and analytics
│   │   │   └── settings/      # User settings
│   │   ├── components/        # React components
│   │   │   ├── ui/           # Reusable UI components
│   │   │   ├── forms/        # Form components
│   │   │   ├── charts/       # Chart components
│   │   │   └── layout/       # Layout components
│   │   ├── lib/              # Utility functions
│   │   │   ├── api/          # API client functions
│   │   │   ├── hooks/        # Custom React hooks
│   │   │   └── utils/        # Helper functions
│   │   ├── types/            # TypeScript type definitions
│   │   └── styles/           # Global styles
│   ├── public/               # Static assets
│   ├── Dockerfile
│   ├── package.json
│   └── next.config.js
│
├── backend/                     # FastAPI application
│   ├── app/
│   │   ├── api/               # API routes
│   │   │   ├── v1/
│   │   │   │   ├── accounts.py
│   │   │   │   ├── transactions.py
│   │   │   │   ├── budgets.py
│   │   │   │   ├── categories.py
│   │   │   │   ├── reports.py
│   │   │   │   └── auth.py
│   │   │   └── deps.py       # Dependencies (auth, db session)
│   │   ├── models/           # SQLAlchemy models
│   │   │   ├── user.py
│   │   │   ├── account.py
│   │   │   ├── transaction.py
│   │   │   ├── budget.py
│   │   │   └── category.py
│   │   ├── schemas/          # Pydantic schemas
│   │   │   ├── user.py
│   │   │   ├── account.py
│   │   │   ├── transaction.py
│   │   │   └── budget.py
│   │   ├── services/         # Business logic
│   │   │   ├── account_service.py
│   │   │   ├── transaction_service.py
│   │   │   ├── budget_service.py
│   │   │   └── import_service.py
│   │   ├── core/             # Core configuration
│   │   │   ├── config.py     # Settings management
│   │   │   ├── security.py   # Auth utilities
│   │   │   └── database.py   # DB connection
│   │   ├── db/               # Database utilities
│   │   │   ├── base.py       # Base model imports
│   │   │   └── session.py    # Session management
│   │   ├── alembic/          # Database migrations
│   │   │   └── versions/
│   │   ├── tests/            # Test suite
│   │   │   ├── test_accounts.py
│   │   │   ├── test_transactions.py
│   │   │   └── conftest.py
│   │   └── main.py           # FastAPI app entry
│   ├── requirements.txt
│   ├── Dockerfile
│   └── pytest.ini
│
├── docker-compose.yml          # Multi-service orchestration
├── docker-compose.dev.yml      # Development overrides
├── .env.example               # Environment variables template
├── .gitignore
├── README.md                  # Project documentation
├── LICENSE                    # AGPL-3.0 or MIT license
└── CONTRIBUTING.md            # Contribution guidelines
```

### Database Schema (Initial)

#### Users Table
```sql
- id (UUID, PK)
- email (VARCHAR, UNIQUE)
- hashed_password (VARCHAR)
- full_name (VARCHAR)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
- is_active (BOOLEAN)
- is_verified (BOOLEAN)
```

#### Accounts Table
```sql
- id (UUID, PK)
- user_id (UUID, FK -> users)
- name (VARCHAR)
- type (ENUM: checking, savings, credit_card, loan, investment, cash)
- currency (VARCHAR, default: USD)
- initial_balance (DECIMAL)
- current_balance (DECIMAL)
- is_active (BOOLEAN)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
```

#### Transactions Table
```sql
- id (UUID, PK)
- user_id (UUID, FK -> users)
- account_id (UUID, FK -> accounts)
- date (DATE)
- amount (DECIMAL)
- payee (VARCHAR)
- description (TEXT)
- category_id (UUID, FK -> categories, nullable)
- type (ENUM: income, expense, transfer)
- is_recurring (BOOLEAN)
- recurring_rule_id (UUID, FK -> recurring_rules, nullable)
- transfer_id (UUID, FK -> transactions, nullable) # For linked transfers
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
```

#### Categories Table
```sql
- id (UUID, PK)
- user_id (UUID, FK -> users)
- name (VARCHAR)
- parent_id (UUID, FK -> categories, nullable)
- type (ENUM: income, expense)
- color (VARCHAR)
- icon (VARCHAR)
- created_at (TIMESTAMP)
```

#### Budgets Table
```sql
- id (UUID, PK)
- user_id (UUID, FK -> users)
- name (VARCHAR)
- category_id (UUID, FK -> categories)
- amount (DECIMAL)
- period (ENUM: monthly, quarterly, yearly)
- start_date (DATE)
- end_date (DATE, nullable)
- rollover (BOOLEAN)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
```

#### Tags Table
```sql
- id (UUID, PK)
- user_id (UUID, FK -> users)
- name (VARCHAR)
- color (VARCHAR)
```

#### Transaction_Tags Table (Many-to-Many)
```sql
- transaction_id (UUID, FK -> transactions)
- tag_id (UUID, FK -> tags)
- PRIMARY KEY (transaction_id, tag_id)
```

#### Goals Table
```sql
- id (UUID, PK)
- user_id (UUID, FK -> users)
- name (VARCHAR)
- type (ENUM: savings, debt_payoff, custom)
- target_amount (DECIMAL)
- current_amount (DECIMAL)
- deadline (DATE, nullable)
- account_id (UUID, FK -> accounts, nullable)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
```

### API Endpoints (RESTful)

#### Authentication
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login (returns JWT)
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/logout` - Logout user
- `POST /api/v1/auth/password-reset` - Request password reset

#### Accounts
- `GET /api/v1/accounts` - List all user accounts
- `POST /api/v1/accounts` - Create new account
- `GET /api/v1/accounts/{id}` - Get account details
- `PUT /api/v1/accounts/{id}` - Update account
- `DELETE /api/v1/accounts/{id}` - Delete account
- `GET /api/v1/accounts/{id}/balance-history` - Get balance history

#### Transactions
- `GET /api/v1/transactions` - List transactions (with pagination, filters)
- `POST /api/v1/transactions` - Create transaction
- `GET /api/v1/transactions/{id}` - Get transaction details
- `PUT /api/v1/transactions/{id}` - Update transaction
- `DELETE /api/v1/transactions/{id}` - Delete transaction
- `POST /api/v1/transactions/bulk` - Bulk create transactions
- `POST /api/v1/transactions/import` - Import from file

#### Categories
- `GET /api/v1/categories` - List all categories
- `POST /api/v1/categories` - Create category
- `PUT /api/v1/categories/{id}` - Update category
- `DELETE /api/v1/categories/{id}` - Delete category
- `GET /api/v1/categories/tree` - Get hierarchical category tree

#### Budgets
- `GET /api/v1/budgets` - List all budgets
- `POST /api/v1/budgets` - Create budget
- `GET /api/v1/budgets/{id}` - Get budget details
- `PUT /api/v1/budgets/{id}` - Update budget
- `DELETE /api/v1/budgets/{id}` - Delete budget
- `GET /api/v1/budgets/{id}/progress` - Get budget progress/status

#### Reports
- `GET /api/v1/reports/dashboard` - Dashboard summary data
- `GET /api/v1/reports/spending-by-category` - Category breakdown
- `GET /api/v1/reports/income-vs-expenses` - Income vs expenses over time
- `GET /api/v1/reports/net-worth` - Net worth calculation
- `GET /api/v1/reports/cash-flow` - Cash flow analysis
- `POST /api/v1/reports/export` - Export report data

#### Goals
- `GET /api/v1/goals` - List all goals
- `POST /api/v1/goals` - Create goal
- `PUT /api/v1/goals/{id}` - Update goal
- `DELETE /api/v1/goals/{id}` - Delete goal

### Docker Compose Configuration

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    environment:
      DATABASE_URL: postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      REDIS_URL: redis://redis:6379
      SECRET_KEY: ${SECRET_KEY}
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
    volumes:
      - ./backend:/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000
    ports:
      - "3000:3000"
    depends_on:
      - backend
    volumes:
      - ./frontend:/app
      - /app/node_modules
      - /app/.next
    command: npm run dev

volumes:
  postgres_data:
  redis_data:
```

## Development Phases & Roadmap

### Phase 1: MVP Foundation (Weeks 1-8)
**Goal**: Build core functionality for self-hosted financial tracking

1. **Week 1-2: Project Setup**
   - Initialize Next.js and FastAPI projects
   - Configure Docker Compose environment
   - Set up PostgreSQL database with Alembic migrations
   - Implement authentication system (JWT)
   - Create basic user registration/login

2. **Week 3-4: Account & Transaction Management**
   - Build account CRUD operations
   - Implement transaction creation and listing
   - Add basic categorization system
   - Create transaction import from CSV
   - Build simple dashboard view

3. **Week 5-6: Budgeting System**
   - Implement budget creation and management
   - Add budget tracking and alerts
   - Create budget vs actual reports
   - Build category management UI
   - Add tags functionality

4. **Week 7-8: Reporting & Polish**
   - Create dashboard with key metrics
   - Build basic reports (spending by category, income vs expenses)
   - Add date range filters
   - Implement data export (CSV)
   - Write comprehensive README and deployment docs

**Deliverable**: Working self-hosted application with core features

### Phase 2: Advanced Features (Weeks 9-16)
**Goal**: Add sophisticated financial management capabilities

1. **Week 9-10: Rules Engine**
   - Build auto-categorization rules
   - Implement rule priority system
   - Add bulk rule application
   - Create rule testing interface

2. **Week 11-12: Goals & Advanced Reporting**
   - Implement savings goals and debt tracking
   - Build net worth tracking over time
   - Add cash flow forecasting
   - Create custom report builder

3. **Week 13-14: Bill Tracking & Recurring Transactions**
   - Add recurring transaction templates
   - Implement bill reminders
   - Create calendar view of upcoming bills
   - Add subscription detection

4. **Week 15-16: Import/Export & Data Management**
   - Support OFX/QFX imports
   - Add duplicate detection
   - Implement full data backup/restore
   - Build data migration tools

**Deliverable**: Feature-complete application rivaling commercial offerings

### Phase 3: Premium Features (Weeks 17-24)
**Goal**: Add integrations and advanced capabilities

1. **Week 17-20: Bank Integration (Plaid)**
   - Integrate Plaid API for account aggregation
   - Build automatic transaction sync
   - Implement connection management UI
   - Add sync status monitoring

2. **Week 21-22: Investment Tracking**
   - Add investment account support
   - Implement portfolio tracking
   - Build performance metrics
   - Create asset allocation views

3. **Week 23-24: Analytics & ML Features**
   - Add spending pattern detection
   - Implement anomaly detection
   - Build predictive budgeting
   - Create spending insights

**Deliverable**: Premium-tier application with automation

### Phase 4: Mobile & Collaboration (Future)
**Goal**: Expand platform support and multi-user features

- React Native mobile application
- Shared budgets and family accounts
- Real-time collaboration features
- Enhanced security (2FA)

## Best Practices & Considerations

### Security
- Never store plaintext passwords (use bcrypt)
- Implement rate limiting on API endpoints
- Use environment variables for all secrets
- Enable CORS properly for frontend-backend communication
- Implement SQL injection protection (SQLAlchemy ORM)
- Add CSRF protection for state-changing operations
- Use HTTPS in production (Traefik with Let's Encrypt)

### Performance
- Implement pagination for all list endpoints (default 50 items)
- Add database indexes on frequently queried fields
- Use Redis for caching frequently accessed data
- Optimize database queries (avoid N+1 problems)
- Implement connection pooling for PostgreSQL
- Use Next.js ISR (Incremental Static Regeneration) where applicable

### Testing
- **Backend**: Pytest with >80% code coverage target
- **Frontend**: Jest + React Testing Library for unit tests
- **E2E**: Playwright or Cypress for critical user flows
- **API**: Integration tests for all endpoints
- **Load Testing**: k6 or Locust for performance validation

### Documentation
- OpenAPI/Swagger documentation for all API endpoints (auto-generated by FastAPI)
- Comprehensive README with setup instructions
- Architecture decision records (ADRs) for major decisions
- User documentation for self-hosting
- Contribution guidelines for open-source contributors

### Open Source Considerations
- Choose appropriate license (AGPL-3.0 like Firefly III, or MIT)
- Create clear CONTRIBUTING.md with development setup
- Set up issue templates for bugs and features
- Implement conventional commits for clear history
- Add CI/CD with GitHub Actions for automated testing
- Create CODE_OF_CONDUCT.md
- Set up dependabot for dependency updates

## Deployment & Operations

### Self-Hosting Options
1. **Docker Compose** (Primary method)
   - Easiest setup with single `docker-compose up` command
   - Include example `.env` file
   - Provide upgrade path documentation

2. **Kubernetes** (Advanced)
   - Provide Helm charts for k8s deployment
   - Support for horizontal scaling
   - Integration with existing k8s infrastructure

3. **Traditional VPS**
   - Manual installation guide
   - Systemd service files
   - Nginx configuration examples

### Monitoring & Maintenance
- Health check endpoints (`/health`, `/ready`)
- Structured logging with correlation IDs
- Error tracking (Sentry integration optional)
- Database backup automation
- Update notification system

## Success Metrics

### Technical Metrics
- API response time <200ms for 95th percentile
- Frontend Time to Interactive (TTI) <3 seconds
- Zero critical security vulnerabilities
- >80% test coverage
- Docker image size <500MB combined

### User Metrics
- Complete user flow without errors
- Successful CSV import on first try
- Budget creation in <2 minutes
- Intuitive categorization (minimal re-categorization needed)

## Competitive Analysis Summary

### Advantages over Firefly III
- Modern tech stack (Next.js vs Blade templates)
- Better mobile-responsive design from day one
- Built-in support for bank aggregation (via Plaid)
- More intuitive budgeting UI
- Advanced analytics and ML insights

### Advantages over Mint
- Complete data privacy (self-hosted)
- No ads or upselling
- Open source and customizable
- Lifetime free (no subscription fees)
- Export your data anytime

## Research Sources

This development plan was informed by research on:
- Mint features and capabilities: [Mint.com](https://mint.intuit.com/), [SmartAsset Mint Review](https://smartasset.com/financial-advisor/mint-review)
- Firefly III architecture: [Firefly III GitHub](https://github.com/firefly-iii/firefly-iii), [Firefly III Docs](https://docs.firefly-iii.org/explanation/firefly-iii/about/introduction/)
- Personal finance app best practices: [NerdWallet Budget Apps](https://www.nerdwallet.com/finance/learn/best-budget-apps), [CNBC Best Budget Apps](https://www.cnbc.com/select/best-budgeting-apps/)
- Next.js + FastAPI architecture: [Travis Luong Tutorial](https://www.travisluong.com/how-to-develop-a-full-stack-next-js-fastapi-postgresql-app-using-docker/), [FastAPI-NextJS Template](https://github.com/Nneji123/fastapi-nextjs)
- Docker best practices: [Next.js Docker 2026](https://thelinuxcode.com/nextjs-docker-images-how-i-build-predictable-fast-deployments-in-2026/), [TestDriven.io FastAPI Docker](https://testdriven.io/blog/fastapi-docker-traefik/)

## Next Steps

1. **Initial Setup**:
   - Initialize Git repository
   - Create GitHub repository with appropriate license
   - Set up project structure with frontend/backend folders
   - Configure Docker Compose development environment
   - Create initial documentation (README, CONTRIBUTING)

2. **Technology Setup**:
   - Initialize Next.js project with TypeScript
   - Set up FastAPI project with SQLAlchemy and Alembic
   - Configure PostgreSQL and Redis containers
   - Implement basic authentication system

3. **First Features**:
   - Build user registration and login
   - Create account management CRUD
   - Implement basic transaction entry
   - Build simple dashboard view

4. **Community Building**:
   - Create project roadmap and milestones
   - Set up GitHub project board
   - Write architecture documentation
   - Establish contribution workflow

---

**Project Start Date**: January 2026
**Target MVP Release**: March 2026 (8 weeks)
**Target v1.0 Release**: May 2026 (16 weeks)
**License**: To be determined (AGPL-3.0 or MIT recommended)
**Repository**: To be created on GitHub
