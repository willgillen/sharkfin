# Getting Started - Shark Fin Development

## Quick Start Guide

This guide will help you set up the development environment and start building the financial planning application.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Docker** (version 20.10+) and **Docker Compose** (version 2.0+)
- **Git** (version 2.30+)
- **Node.js** (version 18+ for local frontend development)
- **Python** (version 3.11+ for local backend development)
- **Code Editor** (VS Code recommended with extensions)

## Initial Setup Steps

### 1. Initialize Git Repository

```bash
# Initialize git repository
git init

# Create .gitignore
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
.venv/
*.egg-info/
dist/
build/

# Node
node_modules/
.next/
out/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Environment variables
.env
.env.local
.env.*.local

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Database
*.db
*.sqlite
postgres_data/

# Docker
*.log

# Testing
.coverage
htmlcov/
.pytest_cache/
coverage/

# Build artifacts
*.egg
*.whl
EOF

# Create initial commit
git add .
git commit -m "Initial commit: Project structure and documentation"
```

### 2. Create Project Structure

```bash
# Create main directories
mkdir -p frontend backend

# Create environment file template
cat > .env.example << 'EOF'
# Database
POSTGRES_USER=sharkfin
POSTGRES_PASSWORD=changeme_secure_password
POSTGRES_DB=shark_fin
DATABASE_URL=postgresql://sharkfin:changeme_secure_password@postgres:5432/shark_fin

# Backend
SECRET_KEY=changeme_generate_secure_random_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REDIS_URL=redis://redis:6379

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000

# Optional: Plaid Integration (for bank connections)
PLAID_CLIENT_ID=
PLAID_SECRET=
PLAID_ENV=sandbox

# Optional: Email (for notifications)
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
EMAIL_FROM=
EOF

# Copy to actual .env file
cp .env.example .env

# NOTE: Edit .env and change all passwords and secrets!
```

### 3. Set Up Backend (FastAPI)

```bash
cd backend

# Create directory structure
mkdir -p app/{api/{v1},core,db,models,schemas,services,tests}

# Create requirements.txt
cat > requirements.txt << 'EOF'
# FastAPI and server
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-multipart==0.0.6

# Database
sqlalchemy==2.0.25
alembic==1.13.1
psycopg2-binary==2.9.9

# Authentication
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-dotenv==1.0.0

# Data validation
pydantic==2.5.3
pydantic-settings==2.1.0
email-validator==2.1.0

# Redis
redis==5.0.1

# Testing
pytest==7.4.4
pytest-asyncio==0.23.3
httpx==0.26.0

# Utilities
python-dateutil==2.8.2
pytz==2023.3
EOF

# Create requirements-dev.txt for development dependencies
cat > requirements-dev.txt << 'EOF'
-r requirements.txt

# Development tools
black==24.1.1
flake8==7.0.0
mypy==1.8.0
isort==5.13.2

# Testing
pytest-cov==4.1.0
faker==22.0.0
EOF

# Create Dockerfile
cat > Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
EOF

# Create main.py
mkdir -p app
cat > app/main.py << 'EOF'
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Shark Fin API",
    description="Open-source financial planning and budgeting API",
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Shark Fin API", "version": "0.1.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
EOF

# Create __init__.py files
touch app/__init__.py
touch app/api/__init__.py
touch app/api/v1/__init__.py
touch app/core/__init__.py
touch app/db/__init__.py
touch app/models/__init__.py
touch app/schemas/__init__.py
touch app/services/__init__.py
touch app/tests/__init__.py

cd ..
```

### 4. Set Up Frontend (Next.js)

```bash
# Initialize Next.js project
npx create-next-app@latest frontend --typescript --tailwind --app --no-src-dir --import-alias "@/*"

# Or manually if you want more control:
cd frontend

# Create package.json
cat > package.json << 'EOF'
{
  "name": "shark-fin-frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint"
  },
  "dependencies": {
    "next": "14.1.0",
    "react": "^18",
    "react-dom": "^18",
    "axios": "^1.6.5",
    "swr": "^2.2.4",
    "recharts": "^2.12.0",
    "react-hook-form": "^7.49.3",
    "zod": "^3.22.4",
    "@hookform/resolvers": "^3.3.4",
    "date-fns": "^3.2.0"
  },
  "devDependencies": {
    "typescript": "^5",
    "@types/node": "^20",
    "@types/react": "^18",
    "@types/react-dom": "^18",
    "autoprefixer": "^10.0.1",
    "postcss": "^8",
    "tailwindcss": "^3.3.0",
    "eslint": "^8",
    "eslint-config-next": "14.1.0"
  }
}
EOF

# Create Dockerfile
cat > Dockerfile << 'EOF'
FROM node:20-alpine AS base

# Install dependencies only when needed
FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci

# Development image
FROM base AS dev
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

EXPOSE 3000
ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

CMD ["npm", "run", "dev"]

# Production builder
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

ENV NEXT_TELEMETRY_DISABLED 1

RUN npm run build

# Production image
FROM base AS runner
WORKDIR /app

ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000
ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

CMD ["node", "server.js"]
EOF

# Create next.config.js
cat > next.config.js << 'EOF'
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://backend:8000/:path*',
      },
    ]
  },
}

module.exports = nextConfig
EOF

cd ..
```

### 5. Create Docker Compose Configuration

```bash
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: shark-fin-db
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
    networks:
      - shark-fin

  redis:
    image: redis:7-alpine
    container_name: shark-fin-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - shark-fin

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: shark-fin-backend
    environment:
      DATABASE_URL: ${DATABASE_URL}
      REDIS_URL: ${REDIS_URL}
      SECRET_KEY: ${SECRET_KEY}
      ALGORITHM: ${ALGORITHM}
      ACCESS_TOKEN_EXPIRE_MINUTES: ${ACCESS_TOKEN_EXPIRE_MINUTES}
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
    volumes:
      - ./backend:/app
    networks:
      - shark-fin

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      target: dev
    container_name: shark-fin-frontend
    environment:
      NEXT_PUBLIC_API_URL: ${NEXT_PUBLIC_API_URL}
    ports:
      - "3000:3000"
    depends_on:
      - backend
    volumes:
      - ./frontend:/app
      - /app/node_modules
      - /app/.next
    networks:
      - shark-fin

volumes:
  postgres_data:
  redis_data:

networks:
  shark-fin:
    driver: bridge
EOF
```

### 6. Create README.md

```bash
cat > README.md << 'EOF'
# Shark Fin

An open-source, self-hosted financial planning, budgeting, and management application.

## Features

- Account management (checking, savings, credit cards, loans, investments)
- Transaction tracking and categorization
- Budget creation and monitoring
- Financial reports and analytics
- Goal tracking
- Multi-currency support
- Data import/export
- Self-hosted with complete data privacy

## Tech Stack

- **Frontend**: Next.js 14, React 18, TypeScript, Tailwind CSS
- **Backend**: Python 3.11, FastAPI, SQLAlchemy
- **Database**: PostgreSQL 15
- **Cache**: Redis 7
- **Deployment**: Docker & Docker Compose

## Quick Start

1. Clone the repository
2. Copy `.env.example` to `.env` and update the values
3. Run `docker-compose up -d`
4. Access the application at http://localhost:3000
5. API documentation available at http://localhost:8000/docs

## Development

See [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md) for detailed development roadmap.

## Documentation

- [Feature Research](FEATURE_RESEARCH.md) - Comprehensive feature analysis
- [Development Plan](DEVELOPMENT_PLAN.md) - Project roadmap and architecture
- [Getting Started](GETTING_STARTED.md) - Setup and development guide

## License

To be determined (AGPL-3.0 or MIT recommended)

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details.
EOF
```

### 7. Start Development

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

## Development Workflow

### Daily Development

```bash
# Start services
docker-compose up -d

# View logs for specific service
docker-compose logs -f backend
docker-compose logs -f frontend

# Restart a service after code changes
docker-compose restart backend

# Stop all services
docker-compose down

# Stop and remove volumes (database will be reset!)
docker-compose down -v
```

### Running Tests

```bash
# Backend tests
docker-compose exec backend pytest

# Backend tests with coverage
docker-compose exec backend pytest --cov=app

# Frontend tests
docker-compose exec frontend npm test
```

### Database Migrations

```bash
# Create a new migration
docker-compose exec backend alembic revision --autogenerate -m "description"

# Apply migrations
docker-compose exec backend alembic upgrade head

# Rollback migration
docker-compose exec backend alembic downgrade -1
```

### Installing New Dependencies

```bash
# Backend: Add to requirements.txt, then:
docker-compose exec backend pip install -r requirements.txt
# or rebuild: docker-compose up -d --build backend

# Frontend: Add to package.json, then:
docker-compose exec frontend npm install
# or rebuild: docker-compose up -d --build frontend
```

## VS Code Setup (Optional)

Install recommended extensions:
- Python
- Pylance
- ES7+ React/Redux/React-Native snippets
- Tailwind CSS IntelliSense
- ESLint
- Prettier
- Docker

## Next Steps

1. Review [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md) for the full roadmap
2. Set up authentication system (JWT)
3. Create database models for accounts and transactions
4. Build basic API endpoints
5. Create frontend pages for dashboard and transaction entry
6. Implement transaction import from CSV
7. Add budgeting functionality

## Useful Commands

```bash
# Access PostgreSQL database
docker-compose exec postgres psql -U sharkfin -d shark_fin

# Access Redis CLI
docker-compose exec redis redis-cli

# Shell into backend container
docker-compose exec backend bash

# Shell into frontend container
docker-compose exec frontend sh

# View running containers
docker-compose ps

# Remove all stopped containers
docker-compose rm
```

## Troubleshooting

### Port already in use
If you get "port already in use" errors, either stop the conflicting service or change the port in docker-compose.yml

### Database connection errors
Ensure PostgreSQL is healthy: `docker-compose ps`
Check logs: `docker-compose logs postgres`

### Frontend can't connect to backend
Verify NEXT_PUBLIC_API_URL in .env matches your backend URL

### Changes not reflecting
Try rebuilding: `docker-compose up -d --build`

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)

---

Happy coding! 🚀
EOF
```

## What You Should Do Next

### Immediate Actions (Today)

1. **Generate Secure Secrets**
   ```bash
   # Generate SECRET_KEY for JWT
   python3 -c "import secrets; print(secrets.token_urlsafe(32))"

   # Update .env file with generated key
   ```

2. **Initialize Git Repository** (if not already done)
   ```bash
   git init
   git add .
   git commit -m "Initial project setup"
   ```

3. **Test Docker Setup**
   ```bash
   docker-compose up -d
   docker-compose logs -f
   # Verify all services are running
   ```

4. **Access Services**
   - Frontend: http://localhost:3000
   - Backend: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### This Week

1. Set up GitHub repository
2. Implement user authentication (registration, login)
3. Create database models for accounts
4. Build basic API endpoints for account CRUD
5. Create simple frontend dashboard

### Recommended First Features to Build

1. **User Authentication** (Days 1-2)
   - Registration endpoint
   - Login with JWT
   - Password hashing
   - Protected routes

2. **Account Management** (Days 3-4)
   - Create account
   - List accounts
   - Update account
   - Delete account
   - Account types (checking, savings, credit card)

3. **Transaction Entry** (Days 5-7)
   - Manual transaction creation
   - Transaction list with pagination
   - Basic categorization
   - Simple dashboard showing recent transactions

## Learning Resources

- **FastAPI Tutorial**: https://fastapi.tiangolo.com/tutorial/
- **Next.js Learn**: https://nextjs.org/learn
- **SQLAlchemy ORM**: https://docs.sqlalchemy.org/en/20/orm/
- **Docker Compose**: https://docs.docker.com/compose/gettingstarted/
- **Tailwind CSS**: https://tailwindcss.com/docs

---

**You're all set!** The project structure is ready. Follow the steps above to get your development environment running.
