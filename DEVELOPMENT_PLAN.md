# Shark Fin - Development Plan

## Project Overview

A self-hosted, open-source financial planning, budgeting, and management application built with:
- **Frontend**: Next.js (React framework with SSR)
- **Backend**: Python with FastAPI
- **Database**: PostgreSQL
- **Deployment**: Docker Compose for containerization

This application aims to provide feature parity with applications like Mint (now discontinued) and Firefly III, offering users complete control over their financial data through self-hosting.

## Development Progress Checklist

**Last Updated**: January 13, 2026
**Current Phase**: Phase 2 - Advanced Features (Rules Engine & Recurring Transactions)

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

#### Week 9-10: Rules Engine ⏳ NEXT
- [ ] Backend: Rule model (if/then conditions)
- [ ] Backend: Rule execution engine
- [ ] Backend: Pattern matching for transactions
  - [ ] Payee contains/matches text
  - [ ] Amount greater/less than
  - [ ] Description patterns
- [ ] Backend: Rule priority system
- [ ] Backend: Bulk rule application to historical transactions
- [ ] Frontend: Rules management page
- [ ] Frontend: Rule creation/editing interface
- [ ] Frontend: Rule testing interface
- [ ] Tests: Comprehensive rule engine test coverage

#### Week 11-12: Goals & Advanced Reporting ⏳
- [ ] Backend: Savings goals model and API
- [ ] Backend: Debt tracking with payoff calculations
- [ ] Backend: Net worth tracking over time
- [ ] Backend: Cash flow forecasting
- [ ] Frontend: Goals management page
- [ ] Frontend: Goal progress visualization
- [ ] Frontend: Net worth trend chart
- [ ] Frontend: Cash flow forecast view
- [ ] Tests: Goals and advanced reports tests

#### Week 13-14: Bill Tracking & Recurring Transactions ⏳
- [ ] Backend: Recurring transaction templates
- [ ] Backend: Automated transaction generation engine
- [ ] Backend: Schedule management (daily, weekly, monthly, yearly)
- [ ] Backend: Bill reminders system
- [ ] Frontend: Recurring transactions page
- [ ] Frontend: Template creation and editing
- [ ] Frontend: Calendar view of upcoming bills
- [ ] Frontend: Subscription detection interface
- [ ] Tests: Recurring transactions test coverage

#### Week 15-16: Data Management & Backup ⏳
- [ ] Backend: Full data backup export
- [ ] Backend: Data restore functionality
- [ ] Backend: Import history tracking improvements
- [ ] Backend: Data migration tools
- [ ] Frontend: Backup/restore interface
- [ ] Frontend: Import history enhancements
- [ ] Tests: Backup and restore tests

**Phase 2 Status**: 🔄 In Progress - Starting with Rules Engine

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
