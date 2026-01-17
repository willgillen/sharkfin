# Shark Fin - Project Summary

## Overview

**Shark Fin** is an open-source, self-hosted financial planning, budgeting, and management application designed to give users complete control over their financial data while providing feature parity with commercial applications like Mint and Firefly III.

## Project Goals

1. **Privacy First**: Self-hosted solution with complete data ownership
2. **Feature Complete**: Comprehensive financial management capabilities
3. **Modern Architecture**: Built with Next.js, FastAPI, and PostgreSQL
4. **Open Source**: Community-driven development under permissive license
5. **Easy Deployment**: Docker Compose for simple self-hosting

## Technology Decisions

### Frontend: Next.js + TypeScript
**Why?**
- Modern React framework with excellent developer experience
- Server-side rendering for better performance
- Built-in API routes and optimization
- Strong TypeScript support
- Large ecosystem and community

### Backend: FastAPI + Python
**Why?**
- High performance async framework
- Automatic API documentation (OpenAPI/Swagger)
- Excellent data validation with Pydantic
- Type hints for better code quality
- Easy to learn and maintain
- Strong data processing ecosystem

### Database: PostgreSQL
**Why?**
- Robust, mature relational database
- Strong data integrity and ACID compliance
- Advanced features (JSON, full-text search, etc.)
- Excellent performance for financial data
- Wide deployment support

### Deployment: Docker Compose
**Why?**
- Simple single-command deployment
- Consistent environments (dev, staging, production)
- Easy updates and rollbacks
- Portable across platforms
- Industry standard for self-hosted applications

## Key Features

### Phase 1 (MVP - 8 weeks)
✅ User authentication and authorization
✅ Account management (checking, savings, credit cards, loans)
✅ Manual transaction entry and management
✅ Transaction categorization and tagging
✅ Basic budgeting system
✅ CSV import for transactions
✅ OFX/QFX import for transactions
✅ Dashboard with key metrics
✅ Basic reports (spending by category, income vs expenses)

### Phase 2 (Advanced - 16 weeks total)
⏳ Automated categorization rules
⏳ Recurring transactions
⏳ Savings goals and debt tracking
⏳ Bill tracking and reminders
⏳ Advanced reporting (cash flow, net worth trends)
⏳ Full data backup and restore

### Phase 3 (Premium - 24 weeks total)
❌ Bank account aggregation (via Plaid) - Replaced with OFX/QFX for privacy
⏳ Investment portfolio tracking
⏳ Credit score monitoring
⏳ ML-powered spending insights
⏳ Predictive budgeting
⏳ Advanced analytics

### Phase 4 (Future)
📱 React Native mobile app
👥 Multi-user and shared budgets
🔐 Two-factor authentication
🌍 Multi-language support

## Core User Personas

1. **Privacy-Conscious Self-Hoster**: Wants complete data control, no cloud sync
2. **Budget-Focused Saver**: Needs detailed expense tracking and budgeting
3. **Debt-Payoff Motivated**: Tracking multiple debts and payoff progress
4. **Investment Tracker**: Monitoring portfolio and net worth
5. **Small Business Owner**: Separating business/personal finances

## Competitive Advantages

### vs Mint (Discontinued)
- ✅ Still exists and actively maintained
- ✅ Self-hosted with complete privacy
- ✅ No ads or upselling
- ✅ Open source and customizable
- ✅ Free forever

### vs Firefly III
- ✅ Modern tech stack (Next.js vs Laravel Blade)
- ✅ Better mobile-responsive design
- ✅ Simpler, more intuitive UI
- ✅ Built-in bank aggregation support
- ✅ Advanced analytics and ML insights

### vs YNAB/PocketGuard/Monarch
- ✅ No subscription fees
- ✅ Complete data ownership
- ✅ Self-hosted (no external servers)
- ✅ Open source (inspect all code)
- ✅ Unlimited users and accounts

## Project Structure

```
shark-fin/
├── frontend/              # Next.js application
│   ├── app/              # App router (pages)
│   ├── components/       # React components
│   ├── lib/             # Utilities and API client
│   └── types/           # TypeScript definitions
│
├── backend/              # FastAPI application
│   ├── app/
│   │   ├── api/v1/      # API endpoints
│   │   ├── models/      # Database models
│   │   ├── schemas/     # Pydantic schemas
│   │   ├── services/    # Business logic
│   │   └── tests/       # Test suite
│   └── alembic/         # Database migrations
│
├── docker-compose.yml    # Multi-service orchestration
├── .env.example         # Environment template
└── docs/                # Documentation
```

## Development Roadmap

### Immediate (Week 1-2) ✅ COMPLETED
- [x] Research features and create plan
- [x] Initialize Git repository
- [x] Set up Docker Compose environment
- [x] Create project structure
- [x] Implement authentication system
- [x] Set up CI/CD with GitHub Actions

### Short Term (Week 3-8) ✅ COMPLETED
- [x] Account CRUD operations (Backend)
- [x] Transaction management (Backend)
- [x] Basic categorization (Backend)
- [x] Budget creation and tracking (Backend)
- [x] Dashboard with summary metrics (Backend)
- [x] Basic reports (spending by category, income vs expenses) (Backend)
- [x] Frontend foundation with authentication
- [x] Dashboard charts and visualizations
- [x] Accounts page (view, create, edit, delete)
- [x] Transactions page (view, create, edit, delete, filter)
- [x] Budgets page (view, create, edit, delete)
- [x] Categories management page
- [x] Transaction import system (CSV + OFX/QFX with duplicate detection)

### UAT Refinement Phase (Week 9-15) 🔄 INSERTED - IN PROGRESS
**Priority**: CRITICAL - Address quality and UX issues before continuing with advanced features

#### Week 9: Import Wizard Critical Fixes
- [ ] Fix amount sign inconsistencies in CSV/OFX imports
- [ ] Enhanced duplicate detection (check against ALL transactions, not just current batch)
- [ ] User-controlled duplicate resolution UI (skip/merge/replace/import anyway)
- [ ] FITID tracking for exact duplicate matching
- [ ] 15+ new integration tests

#### Week 10: Import Wizard Advanced Features
- [ ] Store original import files in database for audit/rollback
- [ ] Smart payee extraction with regex (Square, Toast, PayPal patterns)
- [ ] Saved column mapping templates (reusable across imports)
- [ ] Drag-and-drop column mapping UI
- [ ] Import process transparency and detailed logging
- [ ] Enhanced rollback capabilities with entity tracking

#### Week 11: Payee System Enhancements
- [ ] Fix category display bug in payee list (shows "Category: 4" instead of name)
- [ ] Brand logo system (1000+ company logos via Clearbit API)
- [ ] Emoji fallback system for unknown/local payees
- [ ] Auto-suggest logos and emojis on payee creation

#### Week 12: Transaction UX Improvements
- [ ] Collapsible filters in table column headers
- [ ] Collapsible Quick Add bar (default collapsed)
- [ ] Inline type selector (replace toggle buttons with dropdown)
- [ ] Remove Type column (use color coding instead)
- [ ] Configurable column display (user preferences)
- [ ] Infinite scroll with virtual windowing
- [ ] Transaction notes indicator with inline expansion
- [ ] Star/flag transactions for follow-up
- [ ] Payee icons in transaction list

#### Week 13: UI/UX Polish
- [ ] Fix form field text readability (color contrast)
- [ ] Overall color scheme review and refinement
- [ ] Refined navigation structure (dropdown or collapsible sidebar)
- [ ] Fix account institution field save bug

#### Week 14: Settings & Preferences System
- [ ] Settings infrastructure (database schema, API)
- [ ] Settings UI (VS Code/Obsidian inspired layout)
- [ ] 6 setting categories: General, Transactions, Import, Display, Notifications, Privacy
- [ ] Settings integration throughout application
- [ ] Searchable settings with help text

#### Week 15: Testing & Development Tools
- [ ] Database reset scripts (full/soft/entity-specific)
- [ ] Enhanced realistic seed data (multiple users, 12 months of transactions)
- [ ] Test data factories (Factory Boy integration)
- [ ] UAT validation and sign-off

**Deliverables**: 50+ improvements, 100+ new tests, professional UI polish, comprehensive settings system

**Success Metrics**: All 44 UAT observations addressed, >85% test coverage maintained, no critical bugs

### Medium Term (Week 16-24) 📋 PLANNED
- [ ] Rules engine for auto-categorization (complete integration with Payee entities)
- [ ] Recurring transactions
- [ ] Goals and savings tracking
- [ ] Bill tracking
- [ ] Advanced reporting
- [ ] Full data backup and restore

### Long Term (Week 17-24)
- [ ] Investment tracking
- [ ] ML-powered insights
- [ ] Credit score monitoring
- [ ] Mobile app (React Native)
- [ ] Multi-user and shared budgets

## Architecture Highlights

### API-First Design
- Complete REST API for all operations
- Auto-generated OpenAPI documentation
- Versioned API (v1, v2, etc.)
- Standardized response formats

### Security
- JWT token authentication
- Bcrypt password hashing
- Rate limiting on endpoints
- CORS protection
- SQL injection prevention (ORM)
- HTTPS in production

### Performance
- Database indexing on key fields
- Redis caching for sessions
- Pagination for large datasets
- Connection pooling
- Optimized queries (avoid N+1)
- Next.js optimizations (ISR, code splitting)

### Testing
- Backend: Pytest with >80% coverage
- Frontend: Jest + React Testing Library
- E2E: Playwright/Cypress
- CI/CD automated testing

### Documentation
- Comprehensive README
- API documentation (auto-generated)
- User guides for self-hosting
- Developer contribution guide
- Architecture decision records

## Database Schema (Core Tables)

1. **users**: User accounts and authentication
2. **accounts**: Financial accounts (checking, savings, etc.)
3. **transactions**: All financial transactions
4. **categories**: Transaction categories (hierarchical)
5. **budgets**: Budget definitions and limits
6. **tags**: Transaction tags for organization
7. **goals**: Savings and debt payoff goals
8. **recurring_rules**: Recurring transaction definitions
9. **rules**: Auto-categorization rules
10. **attachments**: Receipt and document storage

## API Endpoints (Key Routes)

- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `GET /api/v1/accounts` - List accounts
- `POST /api/v1/accounts` - Create account
- `GET /api/v1/transactions` - List transactions (paginated)
- `POST /api/v1/transactions` - Create transaction
- `GET /api/v1/budgets` - List budgets
- `GET /api/v1/reports/dashboard` - Dashboard summary
- `GET /api/v1/reports/spending-by-category` - Spending breakdown

## Deployment Options

### Docker Compose (Recommended)
```bash
git clone https://github.com/willgillen/sharkfin.git
cd sharkfin
cp .env.example .env
# Edit .env with your settings
docker-compose up -d
```

### Kubernetes (Advanced)
Helm charts provided for K8s deployment with:
- Horizontal pod autoscaling
- Persistent volume claims
- Ingress configuration
- Secret management

### Traditional VPS
Manual installation guide with:
- Systemd service files
- Nginx reverse proxy config
- SSL/TLS setup (Let's Encrypt)
- Backup automation

## Success Metrics

### Technical
- API response time <200ms (95th percentile)
- Frontend Time to Interactive <3 seconds
- >80% test coverage
- Zero critical security vulnerabilities
- Docker image <500MB total

### User Experience
- Complete onboarding in <5 minutes
- Successful CSV import on first try
- Budget creation in <2 minutes
- Intuitive UI (minimal support questions)

## Open Source Strategy

### License
**To Be Determined**: AGPL-3.0 or MIT
- AGPL-3.0: Like Firefly III, ensures modifications stay open
- MIT: More permissive, allows commercial use

### Community Building
1. Clear contribution guidelines
2. Good first issues for new contributors
3. Responsive to issues and PRs
4. Regular releases with changelogs
5. Active discussions and Q&A
6. Recognition for contributors

### Documentation Focus
- User documentation for self-hosting
- Developer documentation for contributing
- API documentation for integrations
- Video tutorials and guides
- FAQ and troubleshooting

## Risks and Mitigations

### Risk: Feature Creep
**Mitigation**: Strict MVP definition, phased roadmap, user feedback prioritization

### Risk: Security Vulnerabilities
**Mitigation**: Regular dependency updates, security audits, automated scanning, responsible disclosure process

### Risk: Adoption Challenges
**Mitigation**: Excellent documentation, Docker simplicity, active community support

### Risk: Plaid/API Costs
**Mitigation**: Make bank aggregation optional, support manual imports, provide cost transparency

### Risk: Maintainer Burnout
**Mitigation**: Build active maintainer team, clear contribution process, community involvement

## Current Development Status

### ✅ Completed Features

#### Authentication & User Management
- JWT-based authentication with bcrypt password hashing
- User registration and login endpoints
- Protected API endpoints with user verification
- Token-based authorization

#### Account Management
- Full CRUD operations for financial accounts
- Support for 7 account types (checking, savings, credit card, loan, investment, cash, other)
- Multi-currency support (ISO 4217)
- User-scoped data access with proper isolation
- 10 comprehensive tests with 93% coverage

#### Categories
- Hierarchical category structure (parent/subcategories)
- Three category types (Income, Expense, Transfer)
- Color coding with hex validation (#RRGGBB)
- Icon support for visual identification
- Cascade delete for parent categories
- Type-based filtering
- 14 comprehensive tests

#### Transactions
- Full transaction management (debits, credits, transfers)
- Account-to-account transfer support
- Category linking and filtering
- Date range filtering
- Amount validation (positive values only)
- Support for payees, descriptions, and notes
- 15 comprehensive tests

#### Budgets
- Full budget CRUD operations
- Four period types (weekly, monthly, quarterly, yearly)
- Category-based budget limits
- Time-bound budgets with start/end dates
- Rollover functionality for unused amounts
- Alert system with configurable thresholds
- Budget progress tracking with spent/remaining calculations
- Over-budget detection
- 14 comprehensive tests

#### Dashboard & Reports
- Complete dashboard API with financial summary
- Account summary (assets, liabilities, net worth)
- Income vs expenses with savings rate calculation
- Budget status tracking with visual indicators
- Top spending categories analysis
- Monthly trend tracking (configurable 1-24 months)
- Spending by category breakdown
- 8 comprehensive dashboard/reports tests

#### Transaction Import System
- Complete CSV import with smart format detection
  - Auto-detect Mint, Chase, BofA, Wells Fargo formats
  - Column mapping interface for custom CSV files
  - Sample data preview before import
- OFX/QFX file import support
  - Quicken-compatible bank downloads
  - FITID tracking for deduplication
  - Account and transaction parsing
- Fuzzy duplicate detection
  - Multi-layered matching (date ±2 days, exact amount, description similarity)
  - Levenshtein distance algorithm with 70% threshold
  - Confidence scoring (High, Medium, Very High)
  - Side-by-side comparison review
- Import history and management
  - Track all imports with status and counts
  - Rollback capability for completed imports
  - Import statistics (imported, duplicates, errors)
  - File type and account tracking
- 8 backend API endpoints with full test coverage
- Multi-step wizard UI with progress indicator
- Drag-and-drop file upload interface

#### Frontend Application
- Next.js 14 with TypeScript and Tailwind CSS
- Complete API client with automatic JWT token management
- Authentication system (login, registration)
- Dashboard page with real-time financial metrics and interactive charts
  - Category spending pie chart with Recharts
  - 6-month income vs expenses trend line chart
  - Account summary cards (assets, liabilities, net worth)
  - Budget status with progress bars
  - Top spending categories
- Accounts management (full CRUD interface)
  - List view with sortable table
  - Create, edit, delete operations
  - 7 account types with color-coded badges
  - Balance tracking and currency formatting
- Transactions management (full CRUD with filtering)
  - Comprehensive transaction list
  - Filter by account, category, and type
  - Color-coded transaction types
  - Date, payee, and description tracking
- Budgets management (full CRUD with progress tracking)
  - Card-based budget display
  - Color-coded progress bars (green/yellow/red)
  - Period types (weekly, monthly, quarterly, yearly)
  - Alert thresholds and rollover support
  - Real-time spending vs budget calculations
- Categories management (full CRUD with hierarchy)
  - Table view with type filtering
  - Hierarchical parent/subcategory support
  - Color picker with hex validation
  - Icon support for emojis
  - System category protection
- Import wizard with multi-step flow
  - File upload (CSV/OFX/QFX)
  - Column mapping (CSV only)
  - Transaction preview
  - Duplicate review and selection
  - Import results summary
- Import history page with rollback capability
- Responsive layout with navigation
- Type-safe API integration
- Currency and date formatting utilities
- Reusable form components
- Running in Docker on http://localhost:3001

#### Infrastructure
- Docker Compose multi-service setup
- PostgreSQL 15 database with Alembic migrations
- Redis 7 for caching/sessions
- GitHub Actions CI/CD for automated testing
- Comprehensive test suite (61 tests, 91% coverage)
- Seed data script with realistic demo data
- SQLite for isolated test execution
- Demo user account (demo@sharkfin.com / demo123)

### 🔄 Next Priorities

#### CRITICAL: UAT Refinement Phase (Weeks 9-15)
**Status**: Inserted before continuing with advanced features
**Objective**: Address 44 UAT observations to improve quality, UX, and data integrity

**Week 9 Focus** (Current):
1. [ ] Fix amount sign inconsistencies in import
2. [ ] Enhanced duplicate detection (all transactions)
3. [ ] Duplicate resolution UI with user control
4. [ ] FITID tracking for exact matching

**See full UAT Refinement Plan**: `/Users/willgillen/.claude/plans/uat-refinement-plan.md`

**Why This Phase is Critical**:
- Fixes data integrity issues (duplicate imports, amount signs)
- Significantly improves user experience (import wizard, transaction table)
- Adds essential infrastructure (settings system, testing tools)
- Polishes UI/UX to professional standards
- Must be completed before complex features like recurring transactions

#### After UAT Refinement (Week 16+)
1. [ ] Rules engine for auto-categorization (complete Payee entity integration)
2. [ ] Recurring transactions
3. [ ] Goals and savings tracking
4. [ ] Bill tracking and reminders
5. [ ] Advanced reporting (cash flow, net worth trends)
6. [ ] Full data backup and restore

## Resources and References

### Research Sources
- [Mint Features](https://mint.intuit.com/)
- [Firefly III Documentation](https://docs.firefly-iii.org/)
- [Personal Finance App Comparison](https://www.nerdwallet.com/finance/learn/best-budget-apps)
- [Next.js + FastAPI Tutorial](https://www.travisluong.com/how-to-develop-a-full-stack-next-js-fastapi-postgresql-app-using-docker/)

### Technical Documentation
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

### Community Examples
- [Firefly III GitHub](https://github.com/firefly-iii/firefly-iii)
- [FastAPI-NextJS Template](https://github.com/Nneji123/fastapi-nextjs)
- [Actual Budget](https://actualbudget.org/) - Another open-source alternative

## Project Documents

1. **[DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md)** - Comprehensive development roadmap
2. **[UAT Refinement Plan](.claude/plans/uat-refinement-plan.md)** - Critical quality improvements (Weeks 11-17)
3. **[UAT_OBSERVATIONS.md](UAT_OBSERVATIONS.md)** - User acceptance testing observations
4. **[FEATURE_RESEARCH.md](FEATURE_RESEARCH.md)** - Detailed feature analysis
5. **[GETTING_STARTED.md](GETTING_STARTED.md)** - Setup and development guide
6. **[CONTRIBUTING.md](CONTRIBUTING.md)** - Contribution guidelines
7. **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - This document

## Contact and Support

- **GitHub**: https://github.com/willgillen/sharkfin
- **Issues**: GitHub Issues for bugs and features
- **Discussions**: GitHub Discussions for Q&A

---

**Project Status**: UAT Refinement Phase (Inserted)
**Current Phase**: 🔴 CRITICAL - UAT Refinement & Quality Improvements (Weeks 11-17)
**After UAT Phase**: Advanced Features (Goals, Recurring Transactions, Advanced Reporting)
**Last Updated**: January 17, 2026

### Recent Progress

**Latest (January 17, 2026)**:
- ✅ **Payee Entity System (Complete - Backend + Frontend)** ← Latest!
  - Backend: Payee model, service, API with 43 tests
  - Frontend: Autocomplete, management pages (list, edit, create)
  - Auto-creates payees from transaction entry and imports
  - Intelligent normalization and deduplication
- ✅ **UAT Testing & Observations**
  - Conducted comprehensive user acceptance testing
  - Identified 44 critical observations and improvements
  - Created UAT Refinement Plan (7 weeks, Weeks 11-17)
  - **Inserted as top priority before continuing with advanced features**
- ✅ Navigation updated (added Payees link)
- ✅ 151 backend tests passing (up from 146)

**Phase 1 MVP Completed**:
- ✅ Complete backend API (Auth, Accounts, Categories, Transactions, Budgets, Reports)
- ✅ Dashboard & Reports API with financial analytics
- ✅ Frontend foundation with Next.js 14
- ✅ Authentication flow (login/register)
- ✅ Dashboard with interactive charts (pie chart, line chart)
- ✅ Accounts management (full CRUD)
- ✅ Transactions management (full CRUD with filtering)
- ✅ Budgets management (full CRUD with progress tracking)
- ✅ Categories management (hierarchical with color/icon support)
- ✅ Transaction Import System (CSV + OFX/QFX with duplicate detection)
- ✅ Import History with rollback capability
- ✅ GitHub Actions CI/CD for automated testing
- ✅ 91% test coverage (151 tests passing)
- ✅ Demo user with realistic financial data
- ✅ Full Docker environment (Frontend + Backend + DB + Redis)

### Application Access
- **Frontend**: http://localhost:3001
- **Backend API**: http://localhost:8001
- **API Docs**: http://localhost:8001/docs
- **Demo Login**: demo@sharkfin.com / demo123

Let's build something amazing together! 🚀
