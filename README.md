# Shark Fin

> An open-source, self-hosted financial planning, budgeting, and management application

[![Backend Tests](https://github.com/willgillen/sharkfin/actions/workflows/backend-tests.yml/badge.svg)](https://github.com/willgillen/sharkfin/actions/workflows/backend-tests.yml)
[![License](https://img.shields.io/badge/license-TBD-blue.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/docker-ready-brightgreen.svg)](docker-compose.yml)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](docs/CONTRIBUTING.md)
[![Coverage](https://img.shields.io/badge/coverage-91%25-brightgreen.svg)](https://github.com/willgillen/sharkfin)

## Overview

Shark Fin is a comprehensive personal finance management application designed to give you complete control over your financial data. Built with modern technologies and privacy in mind, it provides all the features you need to track expenses, manage budgets, and achieve your financial goals - without sacrificing your data to third-party services.

**Status**: 🚧 Currently in planning phase. Development starting soon!

## Why Shark Fin?

### 🔒 Privacy First
- **Self-hosted**: Your data stays on your server
- **No tracking**: No analytics, no ads, no data mining
- **Complete control**: Export your data anytime

### 💰 Free Forever
- **Open source**: No subscription fees
- **No limits**: Unlimited accounts, transactions, budgets
- **Community driven**: Transparent development

### 🚀 Modern & Fast
- **Next.js frontend**: Fast, responsive, modern UI
- **FastAPI backend**: High-performance async API
- **PostgreSQL**: Reliable, robust database

### 🎯 Feature Complete
- Account management across multiple types
- Transaction tracking and categorization
- Flexible budgeting system
- Financial goals and savings tracking
- Reports and analytics
- Bank account aggregation (optional)
- And much more!

## Features

### Current Phase: Planning ✅

We've completed comprehensive research and planning:
- ✅ Feature research (Mint, Firefly III, YNAB, etc.)
- ✅ Technology stack selection
- ✅ Architecture design
- ✅ Development roadmap
- ✅ Documentation framework

### Coming in MVP (Phase 1)

- 🔐 User authentication and authorization
- 💳 Account management (checking, savings, credit cards, loans, investments)
- 💸 Transaction entry and management
- 🏷️ Categorization and tagging
- 📊 Budgeting system with alerts
- 📁 CSV import for transactions
- 📈 Dashboard with key financial metrics
- 📑 Basic reports (spending by category, income vs expenses)

### Planned Features

See [DEVELOPMENT_PLAN.md](docs/DEVELOPMENT_PLAN.md) for the complete feature roadmap including:
- Automated categorization rules
- Recurring transactions
- Bill tracking and reminders
- Advanced reporting (cash flow, net worth trends)
- Bank account aggregation via Plaid
- Investment tracking
- Mobile application

## Tech Stack

- **Frontend**: Next.js 14, React 18, TypeScript, Tailwind CSS
- **Backend**: Python 3.11, FastAPI, SQLAlchemy, Pydantic
- **Database**: PostgreSQL 15
- **Cache**: Redis 7
- **Deployment**: Docker & Docker Compose

## Documentation

📚 Comprehensive documentation is available:

- **[Getting Started](docs/GETTING_STARTED.md)** - Setup and development guide
- **[Development Plan](docs/DEVELOPMENT_PLAN.md)** - Detailed roadmap and architecture
- **[Feature Research](docs/FEATURE_RESEARCH.md)** - Complete feature analysis
- **[Contributing](docs/CONTRIBUTING.md)** - How to contribute to the project
- **[Project Summary](docs/PROJECT_SUMMARY.md)** - High-level project overview

## Quick Start (Coming Soon)

Once development begins, getting started will be as simple as:

```bash
# Clone the repository
git clone https://github.com/your-username/shark-fin.git
cd shark-fin

# Copy and configure environment variables
cp .env.example .env
# Edit .env with your settings

# Start the application
docker-compose up -d

# Access the application
# Frontend: http://localhost:3000
# API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

## Development Status

### Phase 1: Planning ✅ Complete
- [x] Feature research
- [x] Technology selection
- [x] Architecture design
- [x] Documentation structure
- [x] Contribution guidelines

### Phase 2: Foundation 🚧 Next
- [ ] Project initialization
- [ ] Docker setup
- [ ] Authentication system
- [ ] Database models
- [ ] Basic API endpoints

### Phase 3: MVP Development 📅 Planned
Target: 8 weeks from development start
- [ ] Core features implementation
- [ ] Testing suite
- [ ] User documentation
- [ ] Deployment guides

## Contributing

We welcome contributions from the community! Whether you're:
- 💻 A developer wanting to contribute code
- 📝 A writer improving documentation
- 🎨 A designer enhancing UI/UX
- 🧪 A tester finding bugs
- 💡 Someone with feature ideas

Please read our [Contributing Guide](docs/CONTRIBUTING.md) to get started.

### Good First Issues

Once development starts, we'll label issues as `good first issue` for newcomers. Check out:
- Documentation improvements
- UI enhancements
- Test coverage
- Bug fixes

## Roadmap

### Q1 2026: Foundation & MVP
- Initialize project structure
- Implement authentication
- Build core features (accounts, transactions, budgets)
- Create basic dashboard
- Launch public beta

### Q2 2026: Advanced Features
- Rules engine for automation
- Recurring transactions
- Goals and savings tracking
- Advanced reporting
- Data import/export

### Q3 2026: Premium Features
- Bank account aggregation (Plaid)
- Investment tracking
- ML-powered insights
- Credit score monitoring

### Q4 2026: Mobile & Expansion
- React Native mobile app
- Multi-user support
- Additional integrations
- Enhanced analytics

## Comparison

| Feature | Shark Fin | Mint | Firefly III | YNAB |
|---------|------------------|------|-------------|------|
| Self-Hosted | ✅ | ❌ | ✅ | ❌ |
| Open Source | ✅ | ❌ | ✅ | ❌ |
| Free | ✅ | ⚠️ Discontinued | ✅ | ❌ |
| Modern UI | ✅ | ✅ | ⚠️ | ✅ |
| Bank Sync | ✅ Planned | ✅ | ⚠️ Limited | ✅ |
| Mobile App | 📅 Planned | ✅ | ❌ | ✅ |
| API Access | ✅ | ❌ | ✅ | ❌ |
| Privacy | ✅ | ❌ | ✅ | ⚠️ |

## License

License to be determined. Options being considered:
- **AGPL-3.0**: Strong copyleft (like Firefly III)
- **MIT**: Permissive open source

## Community

- **GitHub Issues**: [Bug reports and feature requests](../../issues)
- **GitHub Discussions**: [Questions and discussions](../../discussions)
- **Discord**: Coming soon
- **Email**: Coming soon

## Support

This project is in early development. Once launched, support will be available through:
- Documentation and guides
- GitHub Issues for bugs
- Community discussions
- Video tutorials

## Acknowledgments

Inspired by:
- [Firefly III](https://firefly-iii.org/) - Excellent self-hosted personal finance manager
- Mint - Pioneer in automated personal finance (discontinued March 2024)
- [YNAB](https://www.youneedabudget.com/) - Strong budgeting methodology
- [Actual Budget](https://actualbudget.org/) - Open-source alternative

Built with amazing open-source technologies:
- [Next.js](https://nextjs.org/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [PostgreSQL](https://www.postgresql.org/)
- [Docker](https://www.docker.com/)

## Star History

If you find this project useful, please consider giving it a star ⭐

## Stay Updated

- ⭐ Star this repository
- 👀 Watch for updates
- 🗣️ Join discussions
- 🤝 Contribute

---

**Project Status**: Planning Complete - Development Starting Soon
**Last Updated**: January 2026

**Questions?** Open an issue or start a discussion. We're happy to help!

Made with ❤️ by the open-source community
