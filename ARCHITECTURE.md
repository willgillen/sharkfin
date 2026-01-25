# Shark Fin - Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface                          │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │   Browser    │  │  Mobile App  │  │  API Clients │        │
│  │  (React/Next)│  │(React Native)│  │              │        │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘        │
└─────────┼──────────────────┼──────────────────┼────────────────┘
          │                  │                  │
          └──────────────────┴──────────────────┘
                             │
                    ┌────────▼─────────┐
                    │   Traefik/Nginx  │
                    │  Reverse Proxy   │
                    │   (HTTPS/TLS)    │
                    └────────┬─────────┘
                             │
          ┌──────────────────┴──────────────────┐
          │                                     │
┌─────────▼──────────┐              ┌──────────▼──────────┐
│  Next.js Frontend  │              │  FastAPI Backend    │
│  ─────────────────  │              │  ────────────────   │
│  - SSR/SSG Pages   │              │  - REST API         │
│  - React Components│              │  - Authentication   │
│  - State Management│              │  - Business Logic   │
│  - API Client      │              │  - Data Validation  │
└────────┬───────────┘              └──────────┬──────────┘
         │                                     │
         │                                     │
         │              ┌──────────────────────┤
         │              │                      │
         │    ┌─────────▼────────┐  ┌─────────▼────────┐
         │    │   PostgreSQL     │  │      Redis       │
         │    │   ─────────────  │  │  ──────────────  │
         │    │  - User Data     │  │  - Sessions      │
         └────►  - Transactions  │  │  - Cache         │
              │  - Accounts      │  │  - Rate Limiting │
              │  - Budgets       │  │                  │
              └──────────────────┘  └──────────────────┘

                      External Services (Optional)
                      ─────────────────────────────
                    ┌────────────┐  ┌──────────────┐
                    │   Plaid    │  │  Email SMTP  │
                    │ (Bank Sync)│  │(Notifications)│
                    └────────────┘  └──────────────┘
```

## Component Details

### Frontend Layer (Next.js)

```
frontend/
├── app/                          # Next.js App Router
│   ├── (auth)/                  # Authentication routes
│   │   ├── login/
│   │   └── register/
│   ├── dashboard/               # Main dashboard
│   ├── accounts/                # Account management
│   ├── transactions/            # Transaction views
│   ├── budgets/                # Budget management
│   ├── reports/                # Analytics & reports
│   ├── goals/                  # Financial goals
│   └── settings/               # User settings
│
├── components/                  # React components
│   ├── ui/                     # Base UI components
│   │   ├── Button.tsx
│   │   ├── Input.tsx
│   │   ├── Modal.tsx
│   │   └── Card.tsx
│   ├── forms/                  # Form components
│   │   ├── TransactionForm.tsx
│   │   ├── BudgetForm.tsx
│   │   └── AccountForm.tsx
│   ├── charts/                 # Chart components
│   │   ├── SpendingChart.tsx
│   │   ├── TrendChart.tsx
│   │   └── PieChart.tsx
│   └── layout/                 # Layout components
│       ├── Header.tsx
│       ├── Sidebar.tsx
│       └── Footer.tsx
│
├── lib/                        # Utilities
│   ├── api/                   # API client
│   │   ├── client.ts          # Axios configuration
│   │   ├── auth.ts            # Auth endpoints
│   │   ├── accounts.ts        # Account endpoints
│   │   └── transactions.ts    # Transaction endpoints
│   ├── hooks/                 # Custom hooks
│   │   ├── useAuth.ts
│   │   ├── useAccounts.ts
│   │   └── useTransactions.ts
│   └── utils/                 # Helper functions
│       ├── formatting.ts
│       ├── validation.ts
│       └── date.ts
│
└── types/                      # TypeScript types
    ├── api.ts
    ├── models.ts
    └── forms.ts
```

### Backend Layer (FastAPI)

```
backend/
├── app/
│   ├── main.py                 # FastAPI application entry
│   │
│   ├── api/                    # API routes
│   │   ├── deps.py            # Shared dependencies
│   │   └── v1/                # API version 1
│   │       ├── auth.py        # Authentication endpoints
│   │       ├── accounts.py    # Account CRUD
│   │       ├── transactions.py# Transaction CRUD
│   │       ├── budgets.py     # Budget CRUD
│   │       ├── categories.py  # Category CRUD
│   │       ├── reports.py     # Reporting endpoints
│   │       └── goals.py       # Goals CRUD
│   │
│   ├── models/                # SQLAlchemy ORM models
│   │   ├── user.py           # User model
│   │   ├── account.py        # Account model
│   │   ├── transaction.py    # Transaction model
│   │   ├── budget.py         # Budget model
│   │   ├── category.py       # Category model
│   │   └── goal.py           # Goal model
│   │
│   ├── schemas/              # Pydantic schemas
│   │   ├── user.py          # User schemas (request/response)
│   │   ├── account.py       # Account schemas
│   │   ├── transaction.py   # Transaction schemas
│   │   ├── budget.py        # Budget schemas
│   │   └── token.py         # Auth token schemas
│   │
│   ├── services/            # Business logic layer
│   │   ├── account_service.py
│   │   ├── transaction_service.py
│   │   ├── budget_service.py
│   │   ├── import_service.py
│   │   └── report_service.py
│   │
│   ├── core/                # Core configuration
│   │   ├── config.py       # Settings (env vars)
│   │   ├── security.py     # Auth utilities (JWT, hashing)
│   │   └── database.py     # DB connection setup
│   │
│   └── tests/              # Test suite
│       ├── conftest.py     # Pytest fixtures
│       ├── test_auth.py
│       ├── test_accounts.py
│       └── test_transactions.py
```

## Data Flow

### Transaction Creation Flow

```
┌──────────┐   1. User Input    ┌───────────────┐
│  Browser │ ──────────────────► │ TransactionForm│
└──────────┘                     │   Component   │
                                 └───────┬───────┘
                                         │
                             2. Form Validation (Zod)
                                         │
                                         ▼
                                 ┌───────────────┐
                                 │  API Client   │
                                 │ POST /api/v1/ │
                                 │  transactions │
                                 └───────┬───────┘
                                         │
                              3. HTTP Request (JWT Auth)
                                         │
                                         ▼
                                 ┌───────────────┐
                                 │ FastAPI Route │
                                 │ (transactions)│
                                 └───────┬───────┘
                                         │
                           4. Auth Middleware (Verify JWT)
                                         │
                                         ▼
                                 ┌───────────────┐
                                 │Pydantic Schema│
                                 │  Validation   │
                                 └───────┬───────┘
                                         │
                           5. Business Logic
                                         │
                                         ▼
                              ┌──────────────────┐
                              │Transaction Service│
                              │  - Apply rules   │
                              │  - Auto-categorize│
                              └────────┬─────────┘
                                       │
                           6. Database Operation
                                       │
                                       ▼
                              ┌────────────────┐
                              │  SQLAlchemy    │
                              │  ORM (Insert)  │
                              └────────┬───────┘
                                       │
                                       ▼
                              ┌────────────────┐
                              │   PostgreSQL   │
                              │   (Persist)    │
                              └────────┬───────┘
                                       │
                           7. Return Response
                                       │
                     ┌─────────────────┴─────────────────┐
                     ▼                                   ▼
            ┌────────────────┐                  ┌────────────────┐
            │  JSON Response │                  │  Update Cache  │
            │    (201)       │                  │    (Redis)     │
            └────────┬───────┘                  └────────────────┘
                     │
          8. Update UI State
                     │
                     ▼
            ┌────────────────┐
            │  React State   │
            │    Update      │
            └────────┬───────┘
                     │
          9. Re-render Components
                     │
                     ▼
            ┌────────────────┐
            │  User sees new │
            │   transaction  │
            └────────────────┘
```

## Authentication Flow

```
┌──────────┐   1. Login Form    ┌──────────────┐
│   User   │ ──────────────────► │POST /auth/login│
└──────────┘                     └───────┬──────┘
                                         │
                              2. Validate Credentials
                                         │
                                         ▼
                              ┌──────────────────┐
                              │  Verify Password │
                              │  (bcrypt.check)  │
                              └────────┬─────────┘
                                       │
                                  ✓ Valid
                                       │
                                       ▼
                              ┌──────────────────┐
                              │  Generate JWT    │
                              │  - user_id       │
                              │  - expiration    │
                              │  - signature     │
                              └────────┬─────────┘
                                       │
                              3. Store in Redis
                                       │
                                       ▼
                              ┌──────────────────┐
                              │ Return Token     │
                              │ {access_token:..}│
                              └────────┬─────────┘
                                       │
                              4. Store in Client
                                       │
                   ┌───────────────────┴──────────────────┐
                   ▼                                      ▼
          ┌────────────────┐                    ┌────────────────┐
          │  localStorage  │                    │  httpOnly      │
          │  (access_token)│                    │   Cookie       │
          └────────────────┘                    └────────────────┘

     Subsequent Requests
     ────────────────────

┌──────────┐   Request + Token   ┌──────────────┐
│  Client  │ ───────────────────► │  API Endpoint│
└──────────┘  Authorization:      └───────┬──────┘
              Bearer <token>               │
                                          │
                              5. Verify JWT Signature
                                          │
                                          ▼
                              ┌──────────────────┐
                              │  Check Redis     │
                              │  (not revoked?)  │
                              └────────┬─────────┘
                                       │
                                  ✓ Valid
                                       │
                                       ▼
                              ┌──────────────────┐
                              │  Extract user_id │
                              │  Allow request   │
                              └──────────────────┘
```

## Database Schema

### Entity Relationship Diagram

```
┌──────────────────┐
│      users       │
├──────────────────┤
│ id (PK)          │
│ email            │──┐
│ hashed_password  │  │
│ full_name        │  │
│ created_at       │  │
└──────────────────┘  │
                      │
         ┌────────────┴────────────────────────────────┐
         │                                             │
         │                                             │
┌────────▼────────┐         ┌──────────────────┐      │
│    accounts     │         │   categories     │      │
├─────────────────┤         ├──────────────────┤      │
│ id (PK)         │         │ id (PK)          │      │
│ user_id (FK)    │         │ user_id (FK)     │      │
│ name            │         │ name             │      │
│ type            │         │ parent_id (FK)   │      │
│ currency        │         │ type             │      │
│ current_balance │         │ color            │      │
└────────┬────────┘         └────────┬─────────┘      │
         │                           │                │
         │              ┌────────────┴─────────┐      │
         │              │                      │      │
         │   ┌──────────▼──────────┐           │      │
         │   │   transactions      │           │      │
         │   ├─────────────────────┤           │      │
         └──►│ id (PK)             │           │      │
             │ user_id (FK)        │◄──────────┘      │
             │ account_id (FK)     │                  │
             │ category_id (FK)    │◄─────────────────┘
             │ amount              │
             │ date                │
             │ payee               │
             │ description         │
             └──────────┬──────────┘
                        │
          ┌─────────────┴─────────────┐
          │                           │
┌─────────▼────────┐        ┌─────────▼──────┐
│  budgets         │        │ transaction_   │
├──────────────────┤        │     tags       │
│ id (PK)          │        ├────────────────┤
│ user_id (FK)     │        │ transaction_id │
│ category_id (FK) │        │ tag_id (FK)    │
│ amount           │        └────────────────┘
│ period           │
│ start_date       │
└──────────────────┘

┌──────────────────┐        ┌──────────────────┐
│      tags        │        │      goals       │
├──────────────────┤        ├──────────────────┤
│ id (PK)          │        │ id (PK)          │
│ user_id (FK)     │        │ user_id (FK)     │
│ name             │        │ name             │
│ color            │        │ type             │
└──────────────────┘        │ target_amount    │
                            │ current_amount   │
                            │ deadline         │
                            └──────────────────┘
```

## Security Architecture

### Security Layers

```
┌─────────────────────────────────────────────────────────┐
│                   Security Layers                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  1. Network Layer                                       │
│     ┌─────────────────────────────────────────┐        │
│     │ - HTTPS/TLS encryption                  │        │
│     │ - Firewall rules                        │        │
│     │ - Rate limiting (per IP)                │        │
│     └─────────────────────────────────────────┘        │
│                                                         │
│  2. Application Layer                                   │
│     ┌─────────────────────────────────────────┐        │
│     │ - CORS configuration                    │        │
│     │ - JWT token validation                  │        │
│     │ - Input validation (Pydantic)           │        │
│     │ - SQL injection prevention (ORM)        │        │
│     │ - XSS protection (React escaping)       │        │
│     └─────────────────────────────────────────┘        │
│                                                         │
│  3. Authentication Layer                                │
│     ┌─────────────────────────────────────────┐        │
│     │ - Password hashing (bcrypt)             │        │
│     │ - JWT tokens with expiration            │        │
│     │ - Session management (Redis)            │        │
│     │ - Token revocation support              │        │
│     │ - 2FA (future)                          │        │
│     └─────────────────────────────────────────┘        │
│                                                         │
│  4. Authorization Layer                                 │
│     ┌─────────────────────────────────────────┐        │
│     │ - User ownership validation             │        │
│     │ - Resource-level permissions            │        │
│     │ - API endpoint protection               │        │
│     └─────────────────────────────────────────┘        │
│                                                         │
│  5. Data Layer                                          │
│     ┌─────────────────────────────────────────┐        │
│     │ - Encrypted connections to DB           │        │
│     │ - Row-level security (user_id)          │        │
│     │ - Database backups (encrypted)          │        │
│     │ - Audit logging                         │        │
│     └─────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────┘
```

## Performance Optimization

### Caching Strategy

```
┌──────────────┐
│   Request    │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Check Redis  │
│    Cache     │
└──────┬───────┘
       │
  ┌────┴────┐
  │         │
  ▼         ▼
Cache     Cache
Hit       Miss
  │         │
  │         ▼
  │    ┌──────────────┐
  │    │ Query DB     │
  │    └──────┬───────┘
  │           │
  │           ▼
  │    ┌──────────────┐
  │    │  Store in    │
  │    │   Cache      │
  │    └──────┬───────┘
  │           │
  └───────────┘
       │
       ▼
┌──────────────┐
│   Response   │
└──────────────┘

Cache Keys:
- user:{user_id}:accounts
- user:{user_id}:transactions:page:{n}
- user:{user_id}:budgets
- user:{user_id}:dashboard
```

### Database Optimization

```sql
-- Indexes for performance
CREATE INDEX idx_transactions_user_id ON transactions(user_id);
CREATE INDEX idx_transactions_date ON transactions(date DESC);
CREATE INDEX idx_transactions_category ON transactions(category_id);
CREATE INDEX idx_accounts_user_id ON accounts(user_id);

-- Composite indexes
CREATE INDEX idx_transactions_user_date
  ON transactions(user_id, date DESC);

-- Partial indexes
CREATE INDEX idx_active_accounts
  ON accounts(user_id)
  WHERE is_active = true;
```

## Deployment Architecture

### Docker Compose (Development & Self-Hosting)

```
┌─────────────────────────────────────────────────────┐
│                Docker Host                          │
│                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────┐ │
│  │   frontend   │  │   backend    │  │ postgres │ │
│  │   :3000      │  │   :8000      │  │  :5432   │ │
│  └──────┬───────┘  └──────┬───────┘  └────┬─────┘ │
│         │                 │                │       │
│         └─────────┬───────┴────────────────┘       │
│                   │                                 │
│         ┌─────────▼─────────┐                      │
│         │     redis         │                      │
│         │     :6379         │                      │
│         └───────────────────┘                      │
│                                                     │
│  Volumes:                                          │
│  - postgres_data:/var/lib/postgresql/data         │
│  - redis_data:/data                                │
└─────────────────────────────────────────────────────┘
         │
         ▼ Port Mapping
┌─────────────────┐
│   Host Machine  │
│  localhost:3000 │
│  localhost:8000 │
└─────────────────┘
```

### Production (Kubernetes - Future)

```
┌──────────────────────────────────────────────────────┐
│                 Kubernetes Cluster                   │
│                                                      │
│  ┌────────────────────────────────────────────────┐ │
│  │            Ingress Controller                  │ │
│  │         (HTTPS, Load Balancing)                │ │
│  └──────────────────┬─────────────────────────────┘ │
│                     │                                │
│        ┌────────────┴────────────┐                   │
│        │                         │                   │
│  ┌─────▼──────┐          ┌──────▼─────┐            │
│  │  Frontend  │          │  Backend   │            │
│  │    Pods    │          │   Pods     │            │
│  │  (3 replicas)        │ (3 replicas)│            │
│  └────────────┘          └────┬───────┘            │
│                               │                     │
│        ┌──────────────────────┴──────────┐          │
│        │                                 │          │
│  ┌─────▼──────┐                  ┌──────▼─────┐   │
│  │ PostgreSQL │                  │   Redis    │   │
│  │StatefulSet │                  │    Pod     │   │
│  └────────────┘                  └────────────┘   │
│        │                                           │
│  ┌─────▼──────┐                                    │
│  │Persistent  │                                    │
│  │  Volume    │                                    │
│  └────────────┘                                    │
└──────────────────────────────────────────────────────┘
```

## Monitoring & Observability

```
┌─────────────────────────────────────────────────────┐
│              Application Metrics                    │
│                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────┐ │
│  │   Logs       │  │   Metrics    │  │  Traces  │ │
│  │  (Stdout)    │  │ (Prometheus) │  │  (Jaeger)│ │
│  └──────┬───────┘  └──────┬───────┘  └────┬─────┘ │
│         │                 │                │       │
│         └─────────┬───────┴────────────────┘       │
│                   │                                 │
│         ┌─────────▼─────────┐                      │
│         │     Grafana       │                      │
│         │   (Dashboards)    │                      │
│         └───────────────────┘                      │
└─────────────────────────────────────────────────────┘
```

## Account Balances and Running Balance

### Balance Concepts

Shark Fin tracks several types of balances:

1. **Opening Balance**: The initial balance set when an account is created, with an optional `opening_balance_date`.

2. **Current Balance**: The real-time balance of an account, calculated as:
   ```
   current_balance = opening_balance + sum(all_transaction_deltas)
   ```
   Where transaction deltas are:
   - CREDIT: +amount (adds to balance)
   - DEBIT: -amount (subtracts from balance)
   - TRANSFER: -amount (from source account), +amount (to destination account)

3. **Running Balance**: The cumulative balance after each transaction, shown in the transaction list view. This allows users to see what the account balance was at any point in time.

### Running Balance Calculation

Running balance is calculated using PostgreSQL window functions for optimal performance:

```sql
SELECT
    t.*,
    opening_balance + SUM(
        CASE
            WHEN type = 'credit' THEN amount
            WHEN type = 'debit' THEN -amount
            WHEN type = 'transfer' AND account_id = ? THEN -amount
            WHEN type = 'transfer' AND transfer_account_id = ? THEN amount
            ELSE 0
        END
    ) OVER (
        ORDER BY date ASC, display_order ASC NULLS LAST, id ASC
    ) as running_balance
FROM transactions t
WHERE account_id = ? OR transfer_account_id = ?
```

### Running Balance Display Rules

Running balance is **only calculated and displayed** when:

1. **Filtering by a single account** - Running balance is account-specific and meaningless when viewing transactions across multiple accounts.

2. **Sorting by date** - Running balance represents a chronological cumulative sum. When sorting by amount, payee, or other fields, the running balance values would be misleading.

When either condition is not met, the Balance column shows "—" with a tooltip explaining why the balance is not available.

### Transaction Display Order

For transactions on the same date, the order is determined by:

1. **`display_order`** (if set) - An optional integer field that allows manual control of transaction sequence within a day. Lower values appear first.

2. **`id`** (fallback) - The database primary key provides a stable fallback ordering when `display_order` is not set.

This ordering is used for:
- Window function calculations (running balance)
- Default display order in the transaction list
- Database index optimization

### Intra-Day Transaction Ordering

Banks typically don't provide the exact time of transactions - only the date. This creates ambiguity when multiple transactions occur on the same day. Shark Fin handles this by:

1. **Default ordering by ID** - Transactions are ordered by their database ID within each day, which generally reflects the order they were entered or imported.

2. **Manual reordering via `display_order`** - Users can set explicit ordering for same-day transactions when the correct sequence is known (future feature).

3. **Index optimization** - A composite index on `(account_id, date, display_order, id)` ensures efficient running balance queries.

### Performance Considerations

Running balance calculation uses:

- **Window functions** instead of subqueries or application-level loops
- **Composite indexes** for efficient date-based ordering
- **Lazy calculation** - only computed when needed (account filter + date sort)
- **Pagination support** - running balance is calculated correctly across paginated results

## API Documentation

FastAPI provides automatic interactive API documentation:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

## Development Workflow

```
┌──────────────┐
│ Developer    │
│ Local Setup  │
└──────┬───────┘
       │
       ▼
┌──────────────┐      ┌──────────────┐
│ Code Changes │─────►│ Git Commit   │
└──────────────┘      └──────┬───────┘
                             │
                             ▼
                      ┌──────────────┐
                      │  Git Push    │
                      └──────┬───────┘
                             │
                             ▼
                      ┌──────────────┐
                      │ GitHub       │
                      │ Pull Request │
                      └──────┬───────┘
                             │
                  ┌──────────┴──────────┐
                  │                     │
                  ▼                     ▼
           ┌──────────────┐      ┌──────────────┐
           │  Linting     │      │  Tests       │
           │  (Black,     │      │  (Pytest,    │
           │   Flake8)    │      │   Jest)      │
           └──────┬───────┘      └──────┬───────┘
                  │                     │
                  └──────────┬──────────┘
                             │
                             ▼
                      ┌──────────────┐
                      │  Code Review │
                      └──────┬───────┘
                             │
                             ▼
                      ┌──────────────┐
                      │    Merge     │
                      └──────┬───────┘
                             │
                             ▼
                      ┌──────────────┐
                      │   Deploy     │
                      │  (Docker)    │
                      └──────────────┘
```

---

This architecture is designed to be:
- **Scalable**: Horizontal scaling through containerization
- **Maintainable**: Clear separation of concerns
- **Secure**: Multiple layers of security
- **Performant**: Caching and database optimization
- **Testable**: Comprehensive testing at all layers
- **Observable**: Logging and monitoring built-in
