# Contributing to Shark Fin

Thank you for your interest in contributing to Shark Fin! This document provides guidelines and instructions for contributing to this open-source project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Coding Standards](#coding-standards)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Features](#suggesting-features)
- [Community](#community)

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for all contributors, regardless of age, body size, disability, ethnicity, gender identity and expression, level of experience, nationality, personal appearance, race, religion, or sexual identity and orientation.

### Our Standards

**Examples of behavior that contributes to a positive environment:**
- Using welcoming and inclusive language
- Being respectful of differing viewpoints and experiences
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

**Examples of unacceptable behavior:**
- The use of sexualized language or imagery and unwelcome sexual attention
- Trolling, insulting/derogatory comments, and personal or political attacks
- Public or private harassment
- Publishing others' private information without explicit permission
- Other conduct which could reasonably be considered inappropriate in a professional setting

## Getting Started

### Prerequisites

Before contributing, ensure you have:
- Basic knowledge of Git and GitHub
- Familiarity with Python and FastAPI (for backend contributions)
- Familiarity with TypeScript, React, and Next.js (for frontend contributions)
- Docker and Docker Compose installed
- Read the [Development Plan](DEVELOPMENT_PLAN.md) and [Getting Started](GETTING_STARTED.md) guides

### First-Time Contributors

If you're new to open source, consider starting with:
1. Issues labeled `good first issue`
2. Issues labeled `documentation`
3. Issues labeled `help wanted`

Don't hesitate to ask questions in the issue comments or discussions!

## Development Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then:
git clone https://github.com/YOUR_USERNAME/shark-fin.git
cd shark-fin

# Add upstream remote
git remote add upstream https://github.com/ORIGINAL_OWNER/shark-fin.git
```

### 2. Create Development Environment

```bash
# Copy environment file
cp .env.example .env

# Edit .env with your local settings
# Generate a secure SECRET_KEY:
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Start development environment
docker-compose up -d

# Verify everything is running
docker-compose ps
```

### 3. Create a Branch

```bash
# Ensure you're on main and it's up to date
git checkout main
git pull upstream main

# Create a new branch for your feature/fix
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

## How to Contribute

### Types of Contributions

#### 1. Code Contributions
- New features
- Bug fixes
- Performance improvements
- Refactoring
- Tests

#### 2. Documentation
- README improvements
- API documentation
- Code comments
- Tutorials and guides
- Translation

#### 3. Design
- UI/UX improvements
- Icons and graphics
- Accessibility enhancements

#### 4. Testing
- Writing tests
- Manual testing
- Reporting bugs
- Performance testing

#### 5. Community
- Answering questions
- Reviewing pull requests
- Helping with issue triage

## Coding Standards

### Backend (Python/FastAPI)

#### Code Style
- Follow [PEP 8](https://pep8.org/) style guide
- Use [Black](https://github.com/psf/black) for code formatting
- Use [isort](https://pycqa.github.io/isort/) for import sorting
- Use type hints for all function parameters and return values

```python
# Good
def create_transaction(
    db: Session,
    transaction: TransactionCreate,
    user_id: UUID
) -> Transaction:
    """Create a new transaction for a user."""
    db_transaction = Transaction(
        **transaction.dict(),
        user_id=user_id
    )
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

# Bad
def create_transaction(db, transaction, user_id):
    t = Transaction(**transaction.dict(), user_id=user_id)
    db.add(t)
    db.commit()
    db.refresh(t)
    return t
```

#### Running Linters

```bash
# Format code with Black
docker-compose exec backend black app/

# Sort imports
docker-compose exec backend isort app/

# Check for style issues
docker-compose exec backend flake8 app/

# Type checking with mypy
docker-compose exec backend mypy app/
```

#### Testing Requirements
- Write unit tests for all new functions
- Write integration tests for API endpoints
- Aim for >80% code coverage
- All tests must pass before PR approval

```bash
# Run tests
docker-compose exec backend pytest

# Run with coverage
docker-compose exec backend pytest --cov=app --cov-report=html

# Run specific test file
docker-compose exec backend pytest app/tests/test_transactions.py
```

### Frontend (TypeScript/Next.js/React)

#### Code Style
- Use TypeScript for all new files
- Follow [Airbnb React Style Guide](https://github.com/airbnb/javascript/tree/master/react)
- Use functional components with hooks (no class components)
- Use proper TypeScript types (avoid `any`)

```typescript
// Good
interface Transaction {
  id: string;
  amount: number;
  date: Date;
  category: string;
}

const TransactionList: React.FC<{ transactions: Transaction[] }> = ({
  transactions
}) => {
  return (
    <div>
      {transactions.map(tx => (
        <TransactionItem key={tx.id} transaction={tx} />
      ))}
    </div>
  );
};

// Bad
const TransactionList = ({ transactions }: any) => {
  return (
    <div>
      {transactions.map((tx: any) => (
        <div key={tx.id}>{tx.amount}</div>
      ))}
    </div>
  );
};
```

#### Running Linters

```bash
# Lint check
docker-compose exec frontend npm run lint

# Lint and fix
docker-compose exec frontend npm run lint -- --fix

# Type check
docker-compose exec frontend npx tsc --noEmit
```

#### Component Guidelines
- One component per file
- Use meaningful component and prop names
- Extract reusable components
- Keep components small and focused
- Use custom hooks for shared logic

### Database Migrations

When making database schema changes:

```bash
# Create migration
docker-compose exec backend alembic revision --autogenerate -m "Add transaction tags table"

# Review the generated migration file carefully!
# Edit backend/app/alembic/versions/xxx_add_transaction_tags_table.py if needed

# Test migration
docker-compose exec backend alembic upgrade head

# Test downgrade
docker-compose exec backend alembic downgrade -1

# Re-upgrade
docker-compose exec backend alembic upgrade head
```

**Important**: Always review auto-generated migrations before committing!

## Commit Guidelines

We follow [Conventional Commits](https://www.conventionalcommits.org/) specification.

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, missing semi-colons, etc.)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Adding or updating tests
- `build`: Changes to build process or dependencies
- `ci`: Changes to CI configuration
- `chore`: Other changes that don't modify src or test files

### Examples

```bash
# Feature
git commit -m "feat(transactions): add bulk import from CSV"

# Bug fix
git commit -m "fix(budgets): correct budget calculation for rollover budgets"

# Documentation
git commit -m "docs(api): add examples for transaction endpoints"

# Breaking change
git commit -m "feat(auth)!: change JWT token structure

BREAKING CHANGE: JWT tokens now include user permissions.
Existing tokens will be invalid and users must re-authenticate."
```

### Best Practices

- Write clear, descriptive commit messages
- Keep commits focused on a single change
- Reference issue numbers in commit messages: `Closes #123`
- Don't commit commented-out code
- Don't commit sensitive data (keys, passwords, etc.)

## Pull Request Process

### Before Submitting

1. **Ensure all tests pass**
   ```bash
   docker-compose exec backend pytest
   docker-compose exec frontend npm test
   ```

2. **Run linters**
   ```bash
   docker-compose exec backend black app/
   docker-compose exec backend flake8 app/
   docker-compose exec frontend npm run lint
   ```

3. **Update documentation** if needed

4. **Add tests** for new features

5. **Rebase on latest main**
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

### Submitting Pull Request

1. Push your branch to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

2. Go to GitHub and create a Pull Request

3. Fill out the PR template completely:
   - Clear description of changes
   - Link to related issues
   - Screenshots for UI changes
   - Testing steps
   - Checklist completion

### PR Template

```markdown
## Description
Brief description of what this PR does

## Related Issues
Closes #123
Relates to #456

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
How has this been tested?
- [ ] Unit tests
- [ ] Integration tests
- [ ] Manual testing

## Screenshots (if applicable)
Add screenshots for UI changes

## Checklist
- [ ] My code follows the style guidelines
- [ ] I have performed a self-review
- [ ] I have commented my code where needed
- [ ] I have updated the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective
- [ ] New and existing tests pass locally
```

### Review Process

1. **Automated checks** must pass (CI/CD)
2. **Code review** by at least one maintainer
3. **Address feedback** and push updates
4. **Approval** and merge by maintainer

### After Merge

1. Delete your feature branch:
   ```bash
   git branch -d feature/your-feature-name
   git push origin --delete feature/your-feature-name
   ```

2. Update your local main:
   ```bash
   git checkout main
   git pull upstream main
   ```

## Reporting Bugs

### Before Reporting

1. **Search existing issues** to avoid duplicates
2. **Use the latest version** to see if bug is fixed
3. **Gather information**:
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, Docker version, etc.)
   - Error messages and logs

### Bug Report Template

```markdown
## Bug Description
Clear and concise description of the bug

## Steps to Reproduce
1. Go to '...'
2. Click on '...'
3. See error

## Expected Behavior
What you expected to happen

## Actual Behavior
What actually happened

## Screenshots
If applicable, add screenshots

## Environment
- OS: [e.g., macOS 13.0]
- Docker Version: [e.g., 24.0.0]
- Browser: [e.g., Chrome 120]
- Version: [e.g., 0.1.0]

## Logs
Relevant logs or error messages

## Additional Context
Any other relevant information
```

## Suggesting Features

### Feature Request Template

```markdown
## Feature Description
Clear description of the feature

## Problem It Solves
What problem does this feature address?

## Proposed Solution
How do you envision this working?

## Alternatives Considered
Other approaches you've thought about

## Additional Context
Mockups, examples from other apps, etc.

## Priority
- [ ] Critical
- [ ] High
- [ ] Medium
- [ ] Low
```

## Project Structure

Understanding the project structure helps with contributions:

```
shark-fin/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/v1/         # API endpoints
│   │   ├── models/         # Database models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic
│   │   ├── core/           # Core configuration
│   │   └── tests/          # Test files
│   └── requirements.txt
├── frontend/               # Next.js frontend
│   ├── app/               # App router pages
│   ├── components/        # React components
│   ├── lib/              # Utilities and hooks
│   └── types/            # TypeScript types
└── docker-compose.yml
```

## Development Tips

### Debugging

#### Backend
```bash
# Add breakpoint in code
import pdb; pdb.set_trace()

# View logs
docker-compose logs -f backend

# Access Python shell
docker-compose exec backend python
```

#### Frontend
```bash
# View logs
docker-compose logs -f frontend

# Use browser DevTools
# Add console.log() statements

# Use React DevTools extension
```

### Database

```bash
# Access PostgreSQL
docker-compose exec postgres psql -U sharkfin -d shark_fin

# View tables
\dt

# Query data
SELECT * FROM users;

# Exit
\q
```

### Common Issues

1. **Port conflicts**: Change ports in docker-compose.yml
2. **Permission errors**: Check file permissions
3. **Database errors**: Reset database with `docker-compose down -v`
4. **Cache issues**: Rebuild with `docker-compose up -d --build`

## Community

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions and general discussion
- **Discord** (if set up): Real-time chat
- **Email**: [maintainer email]

### Getting Help

- Check existing issues and discussions
- Read the documentation
- Ask specific, clear questions
- Provide context and examples
- Be patient and respectful

## Recognition

Contributors will be recognized in:
- README.md contributors section
- GitHub contributors page
- Release notes for significant contributions

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (to be determined: AGPL-3.0 or MIT).

---

Thank you for contributing to Shark Fin! Your efforts help make financial management accessible and private for everyone.

**Questions?** Don't hesitate to ask in GitHub Discussions or open an issue!
