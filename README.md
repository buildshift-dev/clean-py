# Clean Architecture Python

A demonstration of Clean Architecture principles and Domain-Driven Design patterns implemented in Python with FastAPI and PostgreSQL.

> **⚠️ Disclaimer:** The CloudFormation templates in this project are designed specifically for A Cloud Guru learning environments and demo purposes. They include workarounds for A Cloud Guru's sandbox restrictions and are intended for educational use only. 
>
> While the sample application demonstrates clean architecture best practices, **authentication has been intentionally omitted** as implementation varies significantly between projects and requirements. The primary goal is to showcase clean architecture patterns using Python, not production deployment strategies.

## 🏗️ Architecture Overview

This project demonstrates:
- **Clean Architecture** with domain-driven design
- **PostgreSQL Hybrid** approach (relational + JSONB)
- **Strong typing** with comprehensive linting
- **Repository pattern** for data abstraction
- **Use case** driven business logic
- **FastAPI** for modern Python APIs
- **Streamlit** for interactive demo

### 🚀 AWS Deployment
For AWS deployment using CloudFormation, see the [CloudFormation Deployment Guide](cloudformation/README.md).

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Make (see [installation guide](docs/make-installation-guide.md))
- VS Code (recommended)  
- Git

**For A Cloud Guru environments:** Run `scripts/setup-cloud9.sh` to automatically configure the Cloud9 environment with all required dependencies.

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd clean-py
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # On macOS/Linux
   source venv/bin/activate
   
   # On Windows
   venv\Scripts\activate
   ```

3. **Install dependencies and setup development environment**
   ```bash
   make setup-dev
   # This runs:
   # - pip install -r requirements-dev.txt (includes production deps)
   # - pip install -e . (installs package in editable mode)
   ```

4. **Open VS Code workspace**
   ```bash
   code clean-py.code-workspace
   ```

5. **Run the demo**
   ```bash
   make run-streamlit
   ```

## 🛠️ Makefile Commands

The project includes a comprehensive Makefile for development tasks:

### Development Commands

| Command | Description | Usage |
|---------|-------------|-------|
| `make help` | Show all available commands | `make help` |
| `make install` | Install production dependencies only | `make install` |
| `make install-dev` | Install development dependencies (includes production) | `make install-dev` |
| `make setup-dev` | Install dev dependencies + editable package | `make setup-dev` |
| `make clean` | Clean cache and temporary files | `make clean` |

### Code Quality Commands

| Command | Description | Usage |
|---------|-------------|-------|
| `make format` | Format code with Ruff | `make format` |
| `make lint` | Run all linting tools (Ruff, Pylint, Pyright) | `make lint` |
| `make type-check` | Run strict type checking with Pyright | `make type-check` |
| `make check-types` | Check for missing type annotations | `make check-types` |
| `make security` | Run security analysis with Bandit | `make security` |
| `make dependency-audit` | Check dependencies for vulnerabilities | `make dependency-audit` |

### Testing Commands

| Command | Description | Usage |
|---------|-------------|-------|
| `make test` | Run all tests | `make test` |
| `make test-unit` | Run unit tests only | `make test-unit` |
| `make test-integration` | Run integration tests only | `make test-integration` |
| `make test-coverage` | Run tests with coverage report | `make test-coverage` |

### Application Commands

| Command | Description | Usage |
|---------|-------------|-------|
| `make run-streamlit` | Run Streamlit demo app | `make run-streamlit` |
| `make run-api` | Run FastAPI development server | `make run-api` |
| `make test-api` | Test FastAPI application imports | `make test-api` |

### Workflow Commands

| Command | Description | Usage |
|---------|-------------|-------|
| `make pre-commit` | Run all pre-commit checks | `make pre-commit` |
| `make ci` | Simulate full CI pipeline | `make ci` |
| `make troubleshoot` | Comprehensive troubleshooting guide | `make troubleshoot` |

## 📋 Common Development Workflows

### Daily Development
```bash
# Start development
make clean
make setup-dev
code clean-py.code-workspace

# Before committing changes
make pre-commit
```

### Adding New Features
```bash
# 1. Write tests first
make test-unit

# 2. Implement feature
# 3. Format and check code quality
make format
make lint
make type-check

# 4. Run all tests
make test

# 5. Commit changes
git add .
git commit -m "Add new feature"
```

### Code Quality Checks
```bash
# Check code formatting
make format

# Run comprehensive linting
make lint
# This runs:
# - ruff check src tests
# - pylint src  
# - pyright src tests

# Strict type checking
make type-check
make check-types  # Specifically check for missing type annotations
```

### Testing Workflows
```bash
# Run all tests
make test

# Run only fast unit tests during development
make test-unit

# Run integration tests (slower)
make test-integration

# Generate coverage report
make test-coverage
# Opens htmlcov/index.html in browser
```

## 🎯 Demo Applications

### Streamlit Demo
Interactive demo showing Clean Architecture patterns:

```bash
make run-streamlit
```

**Features:**
- Create customers with JSONB preferences
- Create orders with order details
- View customer-order relationships and business logic
- Sample data pre-loaded

**Sample Customers:**
- Alice Johnson (active, light theme)
- Bob Smith (active, dark theme)  
- Carol Davis (inactive - test business logic)

### FastAPI Server
RESTful API demonstrating the backend architecture:

```bash
make run-api
```

- **API Docs:** http://localhost:8000/docs (local development)
- **Endpoints:** `/api/v1/customers`, `/api/v1/orders`

## 🧪 Testing Strategy

The project follows a comprehensive testing strategy:

### Test Structure
```
tests/
├── unit/                    # Fast unit tests (80%)
│   ├── domain/             # Domain entity tests
│   └── application/        # Use case tests with mocks
├── integration/            # Integration tests (15%)
└── conftest.py            # Shared test fixtures
```

### Test Types

**Unit Tests (80% of tests)**
- Domain entity business logic
- Use cases with mocked repositories
- Pure Python, no external dependencies
- Fast execution (< 1 second)

```bash
# Run unit tests
make test-unit

# Example: Test customer deactivation
pytest tests/unit/domain/test_customer.py::TestCustomer::test_customer_deactivate -v
```

**Integration Tests (15% of tests)**
- Repository implementations with real database
- PostgreSQL with JSONB operations
- End-to-end API testing

```bash
# Run integration tests  
make test-integration
```

**Test Coverage**
```bash
# Generate coverage report
make test-coverage

# View coverage in browser
open htmlcov/index.html
```

## 🔧 Development Notes

### Editable Installation
The project uses `pip install -e .` for development, which means:
- Code changes are immediately reflected without reinstalling
- Import statements like `from src.domain.entities.customer import Customer` work properly
- VS Code test discovery and IntelliSense work correctly

**When to run `make setup-dev` again:**
- After adding new dependencies to `pyproject.toml`
- After creating new top-level packages
- After cloning the repository on a new machine
- If imports stop working for any reason

## 🏛️ Architecture Patterns

This demo demonstrates several architectural patterns:

### Clean Architecture Layers
```
src/
├── domain/                 # Pure business logic
│   ├── entities/          # Domain models (Customer, Order)
│   └── repositories/      # Repository interfaces
├── application/           # Use cases and orchestration
│   └── use_cases/         # Business logic coordination
├── infrastructure/        # External concerns
│   └── database/          # PostgreSQL implementations
└── presentation/          # API and user interfaces
    ├── api/               # FastAPI routes
    └── schemas/           # Pydantic models
```

### Key Patterns Demonstrated

1. **Repository Pattern**: Abstract data access
2. **Use Case Pattern**: Single responsibility business operations
3. **Entity Pattern**: Rich domain models with behavior
4. **Factory Pattern**: Complex object creation
5. **Dependency Injection**: Loose coupling

### PostgreSQL Hybrid Approach
- **Structured data**: Relational columns (id, name, email)
- **Flexible data**: JSONB columns (preferences, order details)
- **Query capabilities**: SQL + JSONB operators
- **Type safety**: Pydantic validation for structured data

## 🔧 Development Tools

### Code Quality Tools
- **Ruff**: Fast Python linter and formatter
- **Pylint**: Code quality analysis
- **Pyright**: Strict type checking
- **pytest**: Testing framework
- **Bandit**: Security vulnerability scanning
- **Safety**: Dependency vulnerability checking

### Configuration Files
- `pyproject.toml`: Python project configuration
- `pyrightconfig.json`: Strict type checking settings
- `pytest.ini`: Test configuration
- `clean-py.code-workspace`: VS Code workspace settings

### Linting Rules
- **ANN rules**: Enforce type annotations on all functions
- **Security checks**: Detect potential security issues
- **Import organization**: Automatic import sorting
- **Complexity limits**: Max McCabe complexity of 10

## 🚨 Troubleshooting

### Common Issues

**Import Errors**
```bash
# Add src to Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Or use the workspace which configures this automatically
code clean-py.code-workspace
```

**Type Checking Issues**
```bash
# Check for missing type annotations
make check-types

# Run strict type checking
make type-check
```

**Test Failures**
```bash
# Run specific test with verbose output
pytest tests/unit/domain/test_customer.py -v

# Run with debugging
pytest tests/unit/domain/test_customer.py -s --pdb
```

**Linting Issues**
```bash
# Auto-fix many issues
make format

# Check what would be fixed
ruff check src tests --diff
```

### Performance Issues

**Slow Tests**
```bash
# Run only fast unit tests
make test-unit

# Skip slow integration tests during development
pytest -m "not slow"
```

**VS Code Performance**
- Ensure Python interpreter is set to `./venv/bin/python`
- Restart Python language server: `Ctrl+Shift+P` → "Python: Restart Language Server"

## 📚 Documentation

### Setup Guides
- `docs/make-installation-guide.md` - How to install and use Make command
- `docs/vscode-test-discovery.md` - Configure VS Code test discovery and debugging
- `docs/windows-powershell-commands.md` - PowerShell equivalents for Windows users

### Pattern Documentation
- `docs/patterns/clean-architecture-patterns.md` - Generic architecture patterns
- `docs/patterns/domain-driven-design.md` - DDD concepts (Entities, Value Objects, Aggregates)
- `docs/patterns/shared-kernel-guide.md` - Shared kernel implementation guide
- `docs/patterns/implementation-roadmap.md` - Roadmap for implementing DDD patterns
- `docs/patterns/clean-architecture.md` - E-commerce specific implementation
- `docs/patterns/python-development-setup.md` - Development environment setup
- `docs/patterns/advanced-patterns.md` - Production-ready patterns
- `docs/patterns/python-security-patterns.md` - Security best practices and tools
- `docs/patterns/factory-pattern-testing-strategy.md` - Factory pattern and testing

## 🎯 Next Steps

### Immediate Improvements
1. Add PostgreSQL integration with Docker
2. Implement FastAPI dependency injection
3. Add integration tests with test containers
4. Create Alembic migrations

### Production Readiness
1. Add authentication and authorization
2. Implement comprehensive error handling
3. Add logging and monitoring
4. Create deployment configurations
5. Add performance optimizations

## 🤝 Contributing

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/amazing-feature`
3. **Run quality checks**: `make pre-commit`
4. **Commit changes**: `git commit -m 'Add amazing feature'`
5. **Push to branch**: `git push origin feature/amazing-feature`
6. **Open Pull Request**

### Code Standards
- All code must pass `make ci` checks
- 100% type coverage required
- Unit tests for all business logic
- Follow Clean Architecture principles

## 📄 License

This project is a proof of concept for educational and evaluation purposes.

---

## Quick Command Reference

```bash
# Setup
make setup-dev           # Install dev dependencies + editable package
code clean-py.code-workspace

# Development
make run-streamlit       # Interactive demo
make format              # Format code
make lint                # Quality checks
make test-unit           # Fast tests
make security            # Security scan

# Pre-commit
make pre-commit          # All quality checks

# Full pipeline
make ci                  # Simulate CI/CD

# Troubleshooting
make troubleshoot        # Comprehensive diagnostics
```

## 📚 Additional Documentation

### Development Guides
- **[Make Installation Guide](docs/make-installation-guide.md)** - How to install and use Make command on different platforms
- **[Windows PowerShell Commands](docs/windows-powershell-commands.md)** - PowerShell equivalents for all Make commands
- **[VS Code Test Discovery](docs/vscode-test-discovery.md)** - Configure VS Code test discovery and debugging
- **[VS Code Problems Panel](docs/vscode-problems-panel-management.md)** - Managing VS Code problems and diagnostics
- **[Coding Standards](docs/coding-standards.md)** - Project coding standards and conventions

### Deployment
- **[CloudFormation Deployment Guide](cloudformation/README.md)** - AWS deployment with ECS Fargate (A Cloud Guru compatible)

For detailed information about architecture patterns and implementation details, see the documentation in the `docs/` directory.