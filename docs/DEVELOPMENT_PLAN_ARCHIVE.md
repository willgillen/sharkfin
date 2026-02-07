
# Shark Fin - Development Plan Archive


This document references the archived phases and tasks of development completed already.  For the current stack of development on the roadmap, refer to [Development Plan](DEVELOPMENT_PLAN.md) document.

## Development Progress Checklist


### Phase 1: MVP Foundation ✅ COMPLETED

#### Week 1-2: Project Setup ✅
- [x] Initialize Next.js and FastAPI projects
- [x] Configure Docker Compose environment
- [x] Set up PostgreSQL database with Alembic migrations
- [x] Implement authentication system (JWT)
- [x] Create basic user registration/login
- [x] Set up GitHub Actions CI/CD

#### Week 3-4: Account & Transaction Management ✅
- [x] Build account CRUD operations (Backend + Frontend)
- [x] Implement transaction creation and listing (Backend + Frontend)
- [x] Add basic categorization system (Backend + Frontend)
- [x] Create transaction import from CSV
- [x] Create transaction import from OFX/QFX
- [x] Build simple dashboard view

#### Week 5-6: Budgeting System ✅
- [x] Implement budget creation and management (Backend + Frontend)
- [x] Add budget tracking and alerts
- [x] Create budget vs actual reports
- [x] Build category management UI (hierarchical with color/icon support)
- [x] Add tags functionality (Backend)

#### Week 7-8: Reporting & Polish ✅
- [x] Create dashboard with key metrics
- [x] Build basic reports (spending by category, income vs expenses)
- [x] Add date range filters
- [x] Implement data export (CSV)
- [x] Add interactive charts (Recharts - pie chart, line chart)
- [x] Write comprehensive README and deployment docs

#### Import System Enhancements ✅
- [x] Smart CSV format detection (Mint, Chase, BofA, Wells Fargo)
- [x] Column mapping interface for custom CSV files
- [x] OFX/QFX import with FITID tracking
- [x] Fuzzy duplicate detection with confidence scoring
- [x] Import history page with rollback capability
- [x] Multi-step import wizard UI
- [x] Drag-and-drop file upload interface

**Phase 1 Status**: ✅ Complete - All MVP features delivered

### Phase 2: Advanced Features 🔄 IN PROGRESS

#### Week 9-10: Payee Entity System & Rules Engine 🔄 IN PROGRESS
**Backend: Payee Entity System** ✅
- [x] Payee model with relationships and metadata support
- [x] PayeeService with normalization and autocomplete
- [x] Pydantic schemas for Payee CRUD
- [x] Database migration for payees table
- [x] Comprehensive PayeeService unit tests (24 tests)
- [x] Smart rule suggestion service integration
- [x] Enhanced payee normalization (URLs, duplicates, cities, etc.)
- [x] Payee API endpoints (CRUD + autocomplete) - 14 API tests
- [x] Transaction service integration (auto-create payees during manual entry)
- [x] Import service integration (auto-create payees from CSV/OFX)
- [x] Transaction-Payee integration tests (5 tests)

**Backend: Rules Engine** ✅
- [x] CategorizationRule model (if/then conditions)
- [x] Rule execution engine with priority system
- [x] Pattern matching for transactions:
  - [x] Payee contains/exact/starts_with/ends_with/regex
  - [x] Amount greater/less than
  - [x] Description patterns
- [x] Smart rule suggestions during CSV import
- [x] Bulk rule application to historical transactions
- [ ] Update rules engine to work with Payee entities (instead of strings)
- [ ] Rule testing interface endpoint

**Frontend: Rules & Payees** 🔄
- [x] Smart rule suggestions in import wizard
- [x] Payee autocomplete in transaction forms (QuickAddBar with entity data)
- [x] Payee management pages
  - [x] Payee list with search and sorting by usage
  - [x] Edit payee page (name, type, category, logo, notes)
  - [x] Create new payee page
  - [ ] Merge payees functionality
  - [ ] View transaction history per payee
  - [ ] Bulk operations (delete, set category)
- [ ] Rules management page
- [ ] Rule creation/editing interface
- [ ] Rule testing interface UI

**Tests** ✅
- [x] PayeeService unit tests (24 tests)
- [x] Smart rule suggestion tests
- [x] Payee API integration tests (14 tests)
- [x] Transaction-Payee integration tests (5 tests)
- [x] All 151 backend tests passing
- [ ] Rules engine with Payee entity tests (when rules updated)

---

## 🔴 INSERTED PHASE: UAT Refinement & Quality Improvements (Weeks 11-17)

**Priority**: CRITICAL - Must complete before continuing with advanced features
**Objective**: Address 44 UAT observations to fix data integrity, improve UX, and polish application
**Reference**: See `/Users/willgillen/.claude/plans/uat-refinement-plan.md` for full technical specifications

### Week 11: Import Wizard Critical Fixes ✅ COMPLETED
**Priority**: Data Integrity Issues - **COMPLETED January 17, 2026**

#### 11.1 Fix Amount Sign Inconsistencies ✅
- [x] Investigate OFX/CSV TRNAMT parsing logic
- [x] Standardize amount sign interpretation across account types
- [x] Test with real bank file formats (checking, credit card, savings)
- [x] Create tests: `test_csv_debit_amounts_always_positive()`, `test_ofx_transaction_type_determines_sign()`
- [x] Files: `backend/app/services/ofx_service.py`, `backend/app/services/import_service.py`
- [x] **Implementation**: Fixed OFX service to use TRNTYPE field for authoritative transaction type determination
- [x] **Testing**: All 7 amount sign tests passing (test_import_amount_signs.py)

#### 11.2 Enhanced Duplicate Detection ✅
- [x] Add FITID column to transactions table (migration `ca1d4344fd9d`)
- [x] Update `detect_duplicates()` to check against ALL user transactions (not just current batch)
- [x] Implement confidence-based matching (Exact 100%, Very High 95%+, High 85-95%, Medium 70-85%)
- [x] Create indexes: `idx_transactions_fitid`, `idx_transactions_duplicate_check`
- [x] Tests: `test_duplicate_detection_against_all_transactions()`, `test_same_file_import_prevented()`
- [x] **Implementation**: FITID exact matching with 100% confidence for OFX/QFX imports
- [x] **Implementation**: Fuzzy matching with Levenshtein similarity for CSV imports (date ±2 days, exact amount, description)
- [x] **Testing**: All 16 duplicate detection tests passing (test_duplicate_detection.py)
- [x] **Real-world test**: Successfully detecting 3,901 duplicates from 393 transactions

#### 11.3 Duplicate Resolution UI ✅
- [x] Create new import wizard step: "Review Duplicates"
- [x] Side-by-side comparison table with confidence scores
- [x] User actions: Skip transactions (default all selected), Import selected
- [x] Bulk actions: "Skip All", "Import All"
- [x] Backend: Enhanced duplicate detection service with confidence scoring
- [x] Frontend: `DuplicateReviewStep.tsx` component with interactive selection
- [x] **Workflow**: Separated duplicate detection from smart rules - now Preview → Duplicates → Smart Rules → Result
- [x] **UX**: Shows duplicate count, confidence badges, existing vs new transaction comparison
- [x] **Testing**: Successfully tested with real-world file (3,901 duplicates properly displayed and handled)
- [x] **Development**: Environment-aware debug logging for development mode only

**All 190 backend tests passing** (including 7 amount sign + 16 duplicate detection tests)

### Week 12: Import Wizard Advanced Features
**Priority**: High - User Experience & Transparency

#### 12.1 Original File Storage ✅
- [x] **Database**: Added 4 columns to import_history (original_file_data, original_file_name, original_file_size, is_compressed)
- [x] **Compression**: Gzip level 9 compression achieving >50% reduction for typical CSV files
- [x] **Backend**: Download endpoint GET /api/v1/imports/{import_id}/download with:
  - User ownership verification
  - On-demand decompression
  - Proper media types (text/csv, application/x-ofx)
  - Content-Disposition headers for download
- [x] **Frontend**: Import history UI with:
  - File size display (formatted as KB/MB)
  - Download button with icon
  - Loading states during download
  - Error handling
- [x] **Testing**: Created test_file_storage.py with 9 comprehensive tests covering:
  - CSV/OFX compression and storage
  - Download endpoint with auth
  - Security (cross-user access prevention)
  - Compression ratio verification
  - Media type handling
- **All 183 backend tests passing**

#### 12.2 Smart Payee Extraction with Regex ✅
- [x] **Service**: Created PayeeExtractionService with comprehensive pattern matching:
  - Payment processors: Square (SQ *), Toast (TST*), PayPal, Venmo, Stripe, Zelle, CashApp
  - Store numbers: #1234, STORE 1234, trailing 4+ digit IDs
  - Transaction IDs: Long alphanumeric codes, asterisk prefixes
  - URL components: .COM, .NET, WWW., HTTP://
  - Location indicators: Street addresses, zip codes
- [x] **Extraction**: Returns (cleaned_name, confidence_score) with cumulative confidence based on patterns matched
- [x] **Fuzzy Matching**: Levenshtein distance matching to existing Payee entities (default 80% threshold)
- [x] **Normalization**: Title casing, whitespace cleanup, punctuation removal
- [x] **Integration**: Updated SmartRuleSuggestionService to use PayeeExtractionService:
  - Merchant detection uses extraction for cleaning names
  - Pattern detection groups transactions by extracted payee
  - Confidence scoring: 50% frequency + 50% extraction quality
  - Base confidence adjusted to 0.5-1.0 for better low-frequency pattern detection
- [x] **Frontend**: Updated SmartRuleSuggestionsStep UI to display:
  - Extracted payee name in suggestions
  - Extraction confidence as quality percentage
  - Enhanced suggestion cards with extraction data
- [x] **Testing**: Created test_payee_extraction.py with 25 tests (all passing):
  - Payment processor prefix removal
  - Store number and location removal
  - URL suffix cleaning
  - Real-world scenarios (Amazon, Starbucks, gas stations)
  - Fuzzy matching with various thresholds
  - Complete extract-and-match pipeline
- [x] **Integration Testing**: Created test_smart_suggestions_integration.py with 16 tests (all passing):
  - Merchant detection with extraction
  - Pattern detection for unknown merchants
  - Square/Toast/PayPal grouping by actual merchant
  - Confidence scoring with extraction boost
  - Edge cases and real-world scenarios
- **All 224 backend tests passing**

### Week 13: Payee System Enhancements
**Priority**: Medium-High - Payee Management & Visual Identity

#### Phase A: Foundation (13.1-13.3) ✅ COMPLETED

##### 13.1 Fix Category Display Bug ✅
- [x] Fix payee list to show category name instead of "Category: 4"
- [x] Add eager loading for `default_category` relationship
- [x] Return `default_category_name` in API response
- [x] Add link to category page
- [x] Tests: `test_payee_list_includes_category_name()`

##### 13.2 Recent Transactions List on Payee Page ✅
- [x] Add API endpoint: `GET /api/v1/payees/{id}/transactions?limit=50`
- [x] Show last 25-50 transactions for the payee on edit page
- [x] Display date, amount, account, category, description
- [x] Link each transaction to transaction detail/edit
- [x] Tests: `test_get_payee_transactions()`

##### 13.3 Spending Summary & Analytics ✅
- [x] Add API endpoint: `GET /api/v1/payees/{id}/stats`
- [x] Return: total_spent_all_time, total_this_month, total_this_year
- [x] Return: average_transaction_amount, transaction_count
- [x] Return: first_transaction_date, last_transaction_date
- [x] Frontend: Display stats card on payee edit page
- [x] Tests: `test_payee_spending_stats()`

#### Phase B: Matching Patterns (13.4) ✅ COMPLETED

##### 13.4 Payee Matching Patterns Management ✅
- [x] Add API endpoint: `GET /api/v1/payees/{id}/patterns`
- [x] Add API endpoint: `POST /api/v1/payees/{id}/patterns`
- [x] Add API endpoint: `PUT /api/v1/payees/patterns/{id}`
- [x] Add API endpoint: `DELETE /api/v1/payees/patterns/{id}`
- [x] Add API endpoint: `POST /api/v1/payees/patterns/test`
- [x] Frontend: Patterns section on payee edit page
  - [x] List existing patterns with type, value, confidence, match count
  - [x] Add new pattern form (type dropdown, value input, confidence score)
  - [x] Delete pattern with confirmation
  - [x] Test pattern against sample description before creating
- [x] Tests: 13 pattern endpoint tests (CRUD, validation, test endpoint)

#### Phase C: Visual Identity (13.5-13.6) ✅ COMPLETED

##### 13.5 Brand Logo Icon System ✅
- [x] Simple Icons CDN integration (3000+ brand SVGs)
  - Use CDN URLs: `https://cdn.simpleicons.org/{slug}/{color}`
  - No local storage needed - direct CDN links
- [x] Create `PayeeIconService` with brand → slug mapping (500+ brands)
  - Retailers, restaurants, tech companies, airlines, gas stations, etc.
  - Case-insensitive matching with partial name support
- [x] Auto-suggest logo URL based on payee name matching
- [x] API endpoints: `/api/v1/payees/icons/suggest`, `/parse`, `/brands`
- [x] Frontend: PayeeIcon component with brand logo rendering
- [x] Frontend: IconPicker component with suggestions, preview, and selection
- [x] Tests: 38 icon service tests (brand matching, emoji fallback, API endpoints)

##### 13.6 Emoji Icon Fallback System ✅
- [x] Integrated into `PayeeIconService` with keyword → emoji mapping
- [x] 200+ keyword mappings (restaurant🍽️, pizza🍕, coffee☕, grocery🛒, gas⛽, etc.)
- [x] Quick emoji picker with 16 common category emojis
- [x] Store emoji as `logo_url: "emoji:{emoji}"`
- [x] PayeeIcon component handles emoji display automatically
- [x] Default emoji for unknown payees: 🏪
- [x] Tests: emoji suggestion tests, parse tests, API tests



### Week 14: Transaction UX Improvements
**Priority**: Medium - User Experience Enhancements

#### 14.1 Collapsible Filters in Table Headers ✅ COMPLETED
- [x] Remove dedicated filter section
- [x] Add sortable column headers (click to sort ascending/descending)
- [x] Add filter icon in each column header → dropdown with filter options
- [x] Active filters shown as removable chips
- [x] "Clear all filters" button
- [x] Create `ColumnFilter.tsx` component

#### 14.2 Collapsible Quick Add Bar ✅ COMPLETED
- [x] Default state: Single line "+ Add Transaction" button
- [x] Expanded state: Full form inline with table
- [x] Position above transaction table
- [x] Smooth slide-down animation
- [x] Auto-collapse after successful add
- [x] ESC key to collapse
- [x] Enter key to submit and advance through fields

#### 14.3 Inline Type Selector & Remove Type Column ✅ COMPLETED
- [x] Replace Expense/Income toggle buttons with dropdown
- [x] Dropdown options: 📤 Expense (red), 📥 Income (green), 🔄 Transfer (blue)
- [x] Integrated into QuickAddBar and transaction forms
- [x] Use color coding for amounts (red=expense, green=income, blue=transfer)
- [x] Filter by type in Amount column dropdown

#### 14.4 Configurable Column Display ✅ COMPLETED
- [x] Add `ui_preferences JSONB` to users table (migration completed)
- [x] Gear icon in table header → column selector
- [x] Checkboxes for visible columns (Date and Amount required)
- [x] Backend API for saving preferences
- [x] Frontend ColumnSelector component
- [x] Preferences persist across sessions

#### 14.5 Infinite Scroll with Virtual Windowing ✅ COMPLETED
- [x] Install `react-window` and `react-window-infinite-loader`
- [x] Implement scroll-based pagination with offset/limit
- [x] Initial load: 100 transactions
- [x] Keep max 500 transactions in memory
- [x] Auto-load more on scroll to bottom (within 200px)
- [x] Inline loading indicators
- [x] Sticky table headers during scroll

#### 14.6 Transaction Notes Indicator ✅ COMPLETED
- [x] Add Notes column with 💬 icon (shows when notes exist)
- [x] Hover to show notes as tooltip
- [x] Configurable via column selector
- [x] Hidden by default, can be enabled by user

#### 14.7 Star/Flag Transactions
- [x] Add `is_starred BOOLEAN` to transactions table (migration)
- [x] Create index: `idx_transactions_starred`
- [x] Add star column in table (⭐/☆)
- [x] Click to toggle (optimistic update)
- [x] Add "Starred" filter quick button
- [x] Starred transactions highlighted with yellow background
- [ ] Tests: `test_star_transaction()`, `test_filter_starred_transactions()`

#### 14.8 Favor Payee Over Description ✅ COMPLETED
- [x] Display payee name prominently (larger, bold)
- [x] Show description as secondary text (smaller, gray)
- [x] Reverse current order (payee first, description second)
- [x] Ensure truncation works properly
- [x] Add column width constraints to prevent horizontal scrollbar
- [x] Fix dropdown clipping issues with smart positioning

#### 14.9 Payee/Description Column Filtering ✅ COMPLETED
- [x] Add filter dropdown to Description column header
- [x] Search/filter by payee name
- [x] Search/filter by description text
- [x] Backend API support with ILIKE pattern matching
- [x] Clear filter option
- [x] Filter chips showing active filters

#### 14.10 Date Range Filtering ✅ COMPLETED
- [x] Add date filter dropdown to Date column header
- [x] Custom date range picker (start/end dates)
- [x] Apply date filters to API query
- [x] Clear date filter option
- [x] Filter chips showing active date range
- [x] Smart dropdown positioning (above/below based on viewport)

#### 14.8 Payee Icons in Transaction List ✅ COMPLETED
- [x] Eager load `payee_entity` relationship in transaction list (already implemented)
- [x] Include `payee_logo_url` in API response (Transaction schema + _transaction_to_response)
- [x] Render payee icon before name using PayeeIconSmall component
- [x] Small size (24x24) with brand logos and emoji support

### Week 15: UI/UX Polish
**Priority**: High - Visual Quality & Usability

#### 15.1 Form Field Text Readability ✅ COMPLETED
- [x] Audit all form input className attributes
- [x] Update to use semantic color names (text-text-primary)
- [x] Ensure placeholders use placeholder-text-disabled
- [x] Create reusable `Input.tsx` component with proper styling
- [x] Create reusable `Select.tsx` component
- [x] Create reusable `Textarea.tsx` component
- [x] All components use WCAG AA compliant colors
- [x] **Phase 1: Core CRUD Forms** ✅ COMPLETED
  - [x] AccountForm.tsx ✅ COMPLETED
  - [x] CategoryForm.tsx ✅ COMPLETED
  - [x] BudgetForm.tsx ✅ COMPLETED
  - [x] TransactionForm.tsx ✅ COMPLETED
- [x] **Phase 2: Import Wizard Forms** ✅ COMPLETED
  - [x] FileUploadStep.tsx ✅ COMPLETED
  - [x] ColumnMappingStep.tsx ✅ COMPLETED
- [x] **Phase 3: Authentication Pages** ✅ COMPLETED
  - [x] Login page ✅ COMPLETED
  - [x] Register page ✅ COMPLETED
- [x] **Phase 4: Rules & High-Priority Components** ✅ COMPLETED
  - [x] Rules new page (app/dashboard/rules/new/page.tsx) ✅ COMPLETED
  - [x] Rules edit page (app/dashboard/rules/[id]/page.tsx) ✅ COMPLETED
  - [x] QuickAddBar component (components/transactions/QuickAddBar.tsx) ✅ COMPLETED
- [x] **Phase 5: Remaining Import Wizard Steps** ✅ COMPLETED
  - [x] DuplicateReviewStep.tsx ✅ COMPLETED
  - [x] EnhancedPayeeReviewStep.tsx ✅ COMPLETED
  - [x] ImportResultStep.tsx ✅ COMPLETED
  - [x] PayeeReviewStep.tsx ✅ COMPLETED
  - [x] PreviewStep.tsx ✅ COMPLETED
  - [x] SmartRuleSuggestionsStep.tsx ✅ COMPLETED
- [x] **Phase 6: List/Table Pages** ✅ COMPLETED
  - [x] Accounts list page ✅ COMPLETED
  - [x] Budgets list page ✅ COMPLETED
  - [x] Categories list page ✅ COMPLETED
  - [x] Transactions list page ✅ COMPLETED
  - [x] Payees list page ✅ COMPLETED
  - [x] Rules list page ✅ COMPLETED (already done in Phase 4)
  - [x] Import history page ✅ COMPLETED
- [x] **Phase 7: Other Components** ✅ COMPLETED
  - [x] VirtualizedTransactionTable.tsx ✅ COMPLETED
  - [x] ColumnFilter.tsx ✅ COMPLETED
  - [x] ColumnSelector.tsx ✅ COMPLETED
  - [x] DashboardLayout.tsx ✅ COMPLETED
  - [x] IconPicker.tsx ✅ COMPLETED
  - [x] PayeeIcon.tsx ✅ COMPLETED
  - [x] Chart components (CategorySpendingChart, IncomeTrendChart) ✅ COMPLETED

#### 15.2 Overall Color Scheme Review ✅ COMPLETED
- [x] Define color palette in `tailwind.config.js`
- [x] Primary: Blue #3B82F6
- [x] Success/Income: Green #10B981
- [x] Warning: Yellow #F59E0B
- [x] Danger/Expense: Red #EF4444
- [x] Transfer: Blue #3B82F6
- [x] Semantic transaction colors (expense, income, transfer)
- [x] Neutral colors (surface, border, text with primary/secondary/tertiary)
- [x] All colors WCAG AA compliant
- [x] Applied to UI components (Input, Select, Textarea)

#### 15.3 Refined Navigation Structure ✅ COMPLETED
- [x] Implement dropdown menu or collapsible sidebar
- [x] Main nav: Dashboard, Accounts, Transactions, Budgets, Reports
- [x] Dropdown "More" menu: Categories, Payees, Rules, Import, Import History, Settings
- [x] Group items logically (Settings group, Tools group)
- [x] Mobile-friendly responsive design
- [x] Test navigation interactions

#### 15.4 Fix Account Institution Field Bug ✅ COMPLETED
- [x] Verify `institution` field exists in Account model
- [x] Verify `AccountCreate` and `AccountUpdate` schemas include `institution`
- [x] Verify frontend form sends `institution` in API call
- [x] Check database migration includes `institution` column
- [x] Tests: `test_create_account_with_institution()`, `test_institution_persists_after_save()`
- [x] Added `account_number` field as well (last 4 digits)

### Week 15.5: Account Balance Architecture Refactor ✅ COMPLETED
**Priority**: Critical - Data Integrity & Architectural Correctness

#### Background & Problem Statement
The current implementation stores `current_balance` as a static field on the Account model that:
- Is never automatically updated when transactions are created, modified, or deleted
- Can become stale immediately after any transaction activity
- Is manually editable via the account update API (can cause data inconsistency)
- Is used for net worth calculations, potentially showing incorrect values
- Violates single source of truth principle (transactions should be authoritative)

This is a fundamental data integrity issue that must be addressed before adding more features.

#### Architectural Decision: Opening Balance + Calculated Approach
After analyzing approaches used by similar platforms (GnuCash, YNAB, Firefly III, Mint, QuickBooks), the recommended approach is:

**Opening Balance + Calculated Delta**
- Store a fixed `opening_balance` and `opening_balance_date` on each account
- Calculate current balance on-the-fly: `opening_balance + SUM(transactions since opening_date)`
- Benefits:
  - Always accurate (transactions are single source of truth)
  - Supports imports with existing balances
  - Fast enough for personal finance (even 10k transactions < 50ms)
  - Clear audit trail
  - Supports reconciliation workflows

#### 15.5.1 Database Migration ✅
- [x] Create migration to add new fields to accounts table:
  - `opening_balance` (Numeric(15,2), default 0, not null)
  - `opening_balance_date` (Date, nullable - if null, implies account start)
- [x] Data migration script to:
  - Copy existing `current_balance` to `opening_balance`
  - Set `opening_balance_date` to earliest transaction date for the account (or created_at if no transactions)
- [x] Keep `current_balance` column temporarily for rollback safety
- [x] Migration: `2439bb1b1c17_add_opening_balance_fields_to_accounts.py`

#### 15.5.2 Backend Model & Service Updates ✅
- [x] Update Account model:
  - Add `opening_balance` and `opening_balance_date` columns
  - Add `calculate_balance(db: Session, as_of_date: date)` method
  - Handles CREDIT, DEBIT, and TRANSFER transaction types correctly
- [x] Create `AccountBalanceService`:
  - `get_current_balance(account_id)` - returns calculated balance
  - `get_balance_as_of(account_id, date)` - returns balance at specific date
  - `get_all_account_balances(user_id)` - batch calculation for dashboard
  - `recalculate_opening_balance(account_id)` - for reconciliation
- [x] Tests: 9 comprehensive balance calculation tests created

#### 15.5.3 API Endpoint Updates ✅
- [x] Update `GET /api/v1/accounts` to include calculated `current_balance`
- [x] Update `GET /api/v1/accounts/{id}` to include calculated `current_balance`
- [x] Update `POST /api/v1/accounts` to return calculated balance
- [x] Update `PUT /api/v1/accounts/{id}` to return calculated balance
- [x] Update `AccountCreate` schema - uses `opening_balance` and `opening_balance_date`
- [x] Update `AccountUpdate` schema - supports `opening_balance` for reconciliation
- [x] Created `_account_to_response()` helper for consistent balance calculation
- [ ] Add new endpoint: `GET /api/v1/accounts/{id}/balance-history` (future enhancement)
- [ ] Update `GET /api/v1/reports/dashboard` to use calculated balances (verify working)

#### 15.5.4 Transaction Hooks (Validation Only) ✅
- [x] Note: No balance update hooks needed since balance is calculated
- [x] Existing validation already handles account ownership
- [ ] Add audit logging for large transactions (future enhancement)

#### 15.5.5 Frontend Updates ✅
- [x] Update Account types to include `opening_balance` and `opening_balance_date`
- [x] Update Account form:
  - New account: Show `opening_balance` field with helper text
  - Edit account: Show `opening_balance` and `opening_balance_date` fields
  - Add "Calculated Balance" read-only display showing live balance
- [x] Account list page displays calculated balance (API returns it automatically)
- [x] Dashboard net worth uses calculated balances (API returns it automatically)
- [ ] Add "Reconcile" feature (future enhancement):
  - Compare calculated balance to bank statement
  - Adjust opening balance or add adjustment transaction

#### 15.5.6 Running Balance in Transaction List ✅
- [x] Add `running_balance` field to Transaction API response
- [x] Calculate running balance using PostgreSQL window functions
- [x] Add `display_order` field to Transaction model for intra-day ordering
- [x] Create database migration for `display_order` column
- [x] Add composite index: `idx_transactions_account_date_order` on (account_id, date, display_order, id)
- [x] Running balance only calculated when:
  - Filtering by single account (account_id provided)
  - Sorting by date (chronological order)
- [x] Running balance calculated over ALL account transactions before applying filters
  - Filters (payee, category, type, starred) don't affect running balance calculation
  - Shows true account balance at each transaction point
- [x] Frontend: Add Balance column to transaction table
  - Warning indicator when balance unavailable (wrong sort/no account filter)
  - Tooltips explaining why balance is unavailable
- [x] Document running balance architecture in ARCHITECTURE.md
- [x] Tests: 12 comprehensive running balance tests including:
  - `test_running_balance_with_account_filter`
  - `test_running_balance_same_day_ordering_desc`
  - `test_running_balance_with_payee_filter`
  - `test_running_balance_with_category_filter`
  - `test_running_balance_with_display_order`

#### 15.5.7 Cleanup & Documentation 🔜
- [ ] Create migration to drop `current_balance` column (safe for local dev)
- [ ] Update API documentation (OpenAPI/Swagger)
- [ ] Update CLAUDE.md with balance architecture decision
- [ ] Add reconciliation workflow documentation

#### Success Criteria ✅
- [x] Account balances are always accurate (calculated from transactions)
- [x] No manual balance editing possible (except opening_balance for reconciliation)
- [x] Net worth and reports show correct values
- [x] Balance calculation is fast and efficient
- [x] All existing tests pass + 21 new balance-related tests (306+ total tests pass)
- [x] Import workflow works correctly with opening_balance
- [x] Frontend displays correct balances throughout application
- [x] Running balance shows in transaction list when filtering by account + sorting by date
- [x] Running balance reflects true account state even when filtering by payee/category

#### Technical Notes
**Transaction Amount Sign Convention:**
- All transaction amounts are stored as positive numbers
- Transaction `type` field determines direction:
  - `CREDIT` = money in (adds to balance)
  - `DEBIT` = money out (subtracts from balance)
  - `TRANSFER` = affects two accounts (subtract from source, add to destination)

**Balance Calculation Query (PostgreSQL):**
```sql
SELECT
    a.opening_balance + COALESCE(SUM(
        CASE
            WHEN t.type = 'credit' THEN t.amount
            WHEN t.type = 'debit' THEN -t.amount
            WHEN t.type = 'transfer' AND t.account_id = a.id THEN -t.amount
            WHEN t.type = 'transfer' AND t.transfer_account_id = a.id THEN t.amount
            ELSE 0
        END
    ), 0) as current_balance
FROM accounts a
LEFT JOIN transactions t ON (
    t.account_id = a.id OR t.transfer_account_id = a.id
) AND (a.opening_balance_date IS NULL OR t.date >= a.opening_balance_date)
WHERE a.id = :account_id
GROUP BY a.id;
```

**Files to Modify:**
- `backend/app/models/account.py` - Add new fields, calculate method
- `backend/app/schemas/account.py` - Update Create/Update schemas
- `backend/app/api/v1/accounts.py` - Calculate balance on response
- `backend/app/api/v1/reports.py` - Use calculated balances
- `backend/app/services/account_balance_service.py` - New service (create)
- `backend/alembic/versions/xxx_add_opening_balance.py` - Migration
- `frontend/components/forms/AccountForm.tsx` - Update form fields
- `frontend/app/dashboard/accounts/page.tsx` - Verify balance display

---