# Shark Fin - Claude Development Guide

This document provides guidelines for Claude Code when working on the Shark Fin project. Follow these principles to ensure consistent, high-quality development.

## Project Overview

**Shark Fin** is an open-source, self-hosted financial planning and budgeting application built with:
- **Frontend**: Next.js 14, React 18, TypeScript, Tailwind CSS
- **Backend**: Python 3.11, FastAPI, SQLAlchemy
- **Database**: PostgreSQL 15
- **Cache**: Redis 7
- **Deployment**: Docker Compose

## Core Development Principles

### 1. Test-Driven Development (TDD)

**Always follow TDD practices:**

- Write tests BEFORE implementing features
- Follow the Red-Green-Refactor cycle:
  1. **Red**: Write a failing test
  2. **Green**: Write minimal code to pass the test
  3. **Refactor**: Improve code while keeping tests green

**Test Coverage Requirements:**
- Aim for >80% code coverage
- All new endpoints must have integration tests
- All business logic must have unit tests
- Test both success and failure scenarios

**Running Tests:**
```bash
# Backend tests
docker-compose exec backend pytest
docker-compose exec backend pytest --cov=app --cov-report=html

# Frontend tests
docker-compose exec frontend npm test
docker-compose exec frontend npm run test:coverage
```

### 2. Always Run Tests After Development

**After completing ANY significant development phase:**

1. Run the full test suite
2. Check for failing tests
3. Review test coverage
4. Fix any issues before committing
5. Only commit when all tests pass

**Definition of "significant development phase":**
- Adding a new feature
- Modifying existing functionality
- Refactoring code
- Adding new endpoints
- Changing database models
- Updating dependencies

### 3. Follow the Planned Architecture

**Always consult these documents before implementation:**
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture and component design
- [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md) - Feature roadmap and technical specs
- [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - High-level project goals

**Architecture Principles:**
- Maintain clear separation between layers (API, Services, Models)
- Use dependency injection for database sessions
- Keep business logic in service layer, not controllers
- Follow RESTful API conventions
- Use Pydantic schemas for request/response validation

**File Organization:**
```
backend/app/
├── api/v1/          # API endpoints (thin controllers)
├── services/        # Business logic (thick services)
├── models/          # SQLAlchemy ORM models
├── schemas/         # Pydantic request/response schemas
├── core/            # Configuration, database, security
└── tests/           # Test files mirroring app structure
```

### 4. Use Local Docker Environment

**All development, building, and testing must use Docker:**

```bash
# Start environment
docker-compose up -d

# Rebuild after dependency changes
docker-compose up -d --build

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Execute commands in containers
docker-compose exec backend <command>
docker-compose exec frontend <command>

# Database access
docker-compose exec postgres psql -U sharkfin -d shark_fin

# Stop environment
docker-compose down

# Reset environment (removes volumes)
docker-compose down -v
```

**Container Ports:**
- Frontend: http://localhost:3001
- Backend API: http://localhost:8001
- API Docs: http://localhost:8001/docs
- PostgreSQL: localhost:5433
- Redis: localhost:6380

**Never:**
- Install dependencies locally outside Docker
- Run tests outside Docker containers
- Modify host system dependencies
- Commit .env file (use .env.example)

### 5. Database Migrations

**Always use Alembic for database changes:**

```bash
# Create a new migration
docker-compose exec backend alembic revision --autogenerate -m "Description"

# Review the generated migration file carefully!
# Edit if needed: backend/alembic/versions/xxx_description.py

# Apply migrations
docker-compose exec backend alembic upgrade head

# Rollback one migration
docker-compose exec backend alembic downgrade -1

# View migration history
docker-compose exec backend alembic history
```

**Migration Best Practices:**
- Always review auto-generated migrations
- Test migrations with upgrade AND downgrade
- Never modify existing migrations after merging to main
- Include data migrations when needed
- Add indexes for foreign keys and frequently queried columns

### 6. Seed Data and Test Data

**Maintain seed data for development and test data for tests:**

**Seed Data Location:**
- `backend/app/db/seeds/` - Development seed data
- Keep seed data realistic and comprehensive
- Update seed data when models change
- Include variety of scenarios (edge cases, typical cases)

**Test Data:**
- Use pytest fixtures for test data
- Keep test data in `backend/app/tests/fixtures/`
- Use factories (Factory Boy) for generating test objects
- Isolate test data between tests (use transactions)

**Running Seeds:**
```bash
# Create seed script
docker-compose exec backend python -m app.db.seeds.run_seeds

# Reset database and re-seed
docker-compose exec backend alembic downgrade base
docker-compose exec backend alembic upgrade head
docker-compose exec backend python -m app.db.seeds.run_seeds
```

**Test Data Example:**
```python
# backend/app/tests/conftest.py
import pytest
from app.core.database import Base, engine, SessionLocal

@pytest.fixture(scope="function")
def db_session():
    """Create a new database session for a test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = SessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()
```

### 7. Code Quality Standards

**Backend (Python):**
- Follow PEP 8 style guide
- Use type hints for all functions
- Maximum line length: 100 characters
- Use Black for formatting: `docker-compose exec backend black app/`
- Use isort for imports: `docker-compose exec backend isort app/`
- Use flake8 for linting: `docker-compose exec backend flake8 app/`

**Frontend (TypeScript):**
- Follow Airbnb React Style Guide
- Use functional components with hooks
- Avoid `any` type - use proper TypeScript types
- Use ESLint: `docker-compose exec frontend npm run lint`
- Use Prettier: `docker-compose exec frontend npm run format`

**Documentation:**
- Add docstrings to all functions and classes
- Use Google-style docstrings for Python
- Add JSDoc comments for TypeScript functions
- Update README when adding major features

### 8. Git Workflow

**Commit Messages:**
Follow Conventional Commits format:
```
type(scope): subject

body

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `test`: Adding tests
- `refactor`: Code refactoring
- `docs`: Documentation changes
- `chore`: Maintenance tasks

**Before Committing:**
1. Run all tests and ensure they pass
2. Run linters and formatters
3. Review your changes
4. Update relevant documentation
5. Ensure no sensitive data (secrets, .env)

**Example:**
```bash
# Stage changes
git add .

# Run tests
docker-compose exec backend pytest
docker-compose exec frontend npm test

# Commit
git commit -m "feat(accounts): add account CRUD endpoints

- Create Account model and schema
- Implement GET, POST, PUT, DELETE endpoints
- Add tests for all account operations
- Update API documentation

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# Push
git push
```

### 9. Security Practices

**Never commit:**
- `.env` file (use `.env.example` template)
- API keys or secrets
- Database credentials
- JWT secret keys

**Security Checklist:**
- Validate all user inputs with Pydantic
- Use parameterized queries (SQLAlchemy handles this)
- Hash passwords with bcrypt
- Use JWT tokens with expiration
- Implement rate limiting on auth endpoints
- Validate email addresses
- Sanitize user-generated content
- Use HTTPS in production
- Keep dependencies updated

### 10. Development Workflow

**Starting a new feature:**

1. **Review the plan:**
   - Check [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md) for specifications
   - Review [ARCHITECTURE.md](ARCHITECTURE.md) for patterns
   - Understand the data model requirements

2. **Write tests first (TDD):**
   ```bash
   # Create test file
   touch backend/app/tests/test_feature.py

   # Write failing tests
   # Run tests to confirm they fail
   docker-compose exec backend pytest backend/app/tests/test_feature.py
   ```

3. **Implement the feature:**
   - Create models if needed
   - Create Pydantic schemas
   - Implement service layer logic
   - Create API endpoints
   - Run tests frequently

4. **Verify tests pass:**
   ```bash
   docker-compose exec backend pytest
   docker-compose exec backend pytest --cov=app
   ```

5. **Update seed data:**
   - Add examples for new feature
   - Test with realistic data

6. **Update documentation:**
   - Add API endpoint docs
   - Update README if needed
   - Add inline code comments

7. **Commit and push:**
   ```bash
   git add .
   git commit -m "feat(feature): description"
   git push
   ```

### 11. Troubleshooting

**Common Issues:**

**Database connection errors:**
```bash
# Check if PostgreSQL is running
docker-compose ps

# View PostgreSQL logs
docker-compose logs postgres

# Restart PostgreSQL
docker-compose restart postgres
```

**Migration conflicts:**
```bash
# Check migration status
docker-compose exec backend alembic current

# View migration history
docker-compose exec backend alembic history

# If needed, reset to specific revision
docker-compose exec backend alembic downgrade <revision>
```

**Test failures:**
```bash
# Run specific test file
docker-compose exec backend pytest app/tests/test_file.py

# Run with verbose output
docker-compose exec backend pytest -v

# Run specific test
docker-compose exec backend pytest app/tests/test_file.py::test_function -v
```

**Container build issues:**
```bash
# Rebuild containers from scratch
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## Quick Reference

**Most Common Commands:**
```bash
# Start development environment
docker-compose up -d

# View all logs
docker-compose logs -f

# Run backend tests
docker-compose exec backend pytest

# Run frontend tests
docker-compose exec frontend npm test

# Create database migration
docker-compose exec backend alembic revision --autogenerate -m "description"

# Apply migrations
docker-compose exec backend alembic upgrade head

# Access database
docker-compose exec postgres psql -U sharkfin -d shark_fin

# Format backend code
docker-compose exec backend black app/

# Lint backend code
docker-compose exec backend flake8 app/

# Check backend test coverage
docker-compose exec backend pytest --cov=app --cov-report=html
```

## Resources

- **Project Documentation**: Root directory .md files
- **API Documentation**: http://localhost:8001/docs
- **GitHub Repository**: https://github.com/willgillen/sharkfin

## Remember

- **Test first, code second**
- **Run tests after every change**
- **Follow the architecture plan**
- **Use Docker for everything**
- **Keep seed and test data updated**
- **Document as you go**
- **Commit early and often**

---

*Last Updated: 2026-01-11*
