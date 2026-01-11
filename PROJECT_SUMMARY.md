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
✅ Dashboard with key metrics
✅ Basic reports (spending by category, income vs expenses)

### Phase 2 (Advanced - 16 weeks total)
✅ Automated categorization rules
✅ Recurring transactions
✅ Savings goals and debt tracking
✅ Bill tracking and reminders
✅ Advanced reporting (cash flow, net worth trends)
✅ OFX/QFX import support
✅ Full data backup and restore

### Phase 3 (Premium - 24 weeks total)
✅ Bank account aggregation (via Plaid)
✅ Investment portfolio tracking
✅ Credit score monitoring
✅ ML-powered spending insights
✅ Predictive budgeting
✅ Advanced analytics

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
- [ ] Set up CI/CD with GitHub Actions

### Short Term (Week 3-8) 🔄 IN PROGRESS
- [x] Account CRUD operations
- [x] Transaction management
- [x] Basic categorization
- [x] Budget creation and tracking
- [ ] Dashboard with charts
- [ ] CSV import
- [ ] Basic reports

### Medium Term (Week 9-16)
- [ ] Rules engine for auto-categorization
- [ ] Recurring transactions
- [ ] Goals and savings tracking
- [ ] Bill tracking
- [ ] Advanced reporting
- [ ] OFX/QFX import

### Long Term (Week 17-24)
- [ ] Plaid integration for bank sync
- [ ] Investment tracking
- [ ] ML-powered insights
- [ ] Credit score monitoring
- [ ] Mobile app (React Native)

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

#### Infrastructure
- Docker Compose multi-service setup
- PostgreSQL 15 database with Alembic migrations
- Redis 7 for caching/sessions
- Comprehensive test suite (53 tests, 90% coverage)
- Seed data script with realistic demo data
- SQLite for isolated test execution

### 🔄 Next Priorities

#### Immediate (Next Sprint)
1. [ ] Dashboard API with key financial metrics
2. [ ] Basic reporting endpoints (spending by category, income vs expenses)
3. [ ] Frontend foundation (Next.js setup)
4. [ ] CSV import functionality

#### This Month
1. [ ] Advanced reporting (trends, forecasting)
2. [ ] Frontend dashboard and charts
3. [ ] User documentation
4. [ ] Set up CI/CD with GitHub Actions
5. [ ] Mobile-responsive design

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
2. **[FEATURE_RESEARCH.md](FEATURE_RESEARCH.md)** - Detailed feature analysis
3. **[GETTING_STARTED.md](GETTING_STARTED.md)** - Setup and development guide
4. **[CONTRIBUTING.md](CONTRIBUTING.md)** - Contribution guidelines
5. **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - This document

## Contact and Support

- **GitHub**: https://github.com/willgillen/sharkfin
- **Issues**: GitHub Issues for bugs and features
- **Discussions**: GitHub Discussions for Q&A

---

**Project Status**: MVP Development - Core Backend Complete ✅
**Current Phase**: Backend APIs (Accounts, Categories, Transactions, Budgets ✅)
**Next Phase**: Dashboard APIs & Basic Reporting
**Last Updated**: January 11, 2026

### Recent Progress
- ✅ Authentication system with JWT tokens
- ✅ Account management (7 account types)
- ✅ Category system (hierarchical with subcategories)
- ✅ Transaction management (debits, credits, transfers)
- ✅ **Budget system with progress tracking** ← Latest!
- ✅ 90% test coverage (53 tests passing)
- ✅ Comprehensive seed data with 6 budgets

Let's build something amazing together! 🚀
