# Python Development Setup and Code Quality

## Overview
This document outlines the Python development environment setup, code quality tools, and linting configuration for maintaining high code standards with strong typing enforcement.

## Development Environment

### VS Code Workspace Configuration
Use the `clean-py.code-workspace` file for consistent development settings across the team.

**Key Features:**
- Automatic Ruff formatting on save
- Strict type checking with Pyright
- Integrated testing with pytest
- Code quality enforcement with pylint

### Required VS Code Extensions
```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.pylint", 
    "charliermarsh.ruff",
    "ms-python.debugpy",
    "redhat.vscode-yaml",
    "tamasfe.even-better-toml"
  ]
}
```

## Code Quality Tools

### 1. Ruff - Fast Python Linter and Formatter

**Configuration in `pyproject.toml`:**
```toml
[tool.ruff]
target-version = "py39"
line-length = 88
src = ["src", "tests"]

[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "W",    # pycodestyle warnings  
    "F",    # Pyflakes
    "I",    # isort
    "B",    # flake8-bugbear
    "C4",   # flake8-comprehensions
    "UP",   # pyupgrade
    "ARG",  # flake8-unused-arguments
    "SIM",  # flake8-simplify
    "TCH",  # flake8-type-checking
    "ANN",  # flake8-annotations (enforce type hints)
    "N",    # pep8-naming
    "S",    # flake8-bandit (security)
]

ignore = [
    "E501",   # Line too long (handled by formatter)
    "B008",   # Do not perform function calls in argument defaults
    "ARG002", # Unused method argument
    "S101",   # Use of assert detected (allow in tests)
    "ANN101", # Missing type annotation for self
    "ANN102", # Missing type annotation for cls
]
```

**Key Features:**
- **ANN rules**: Enforce type annotations on all functions
- **Security checks**: S rules for security issues
- **Import sorting**: Automatic import organization
- **Code modernization**: UP rules for Python version upgrades

### 2. Pyright - Strict Type Checker

**Configuration in `pyrightconfig.json`:**
```json
{
  "include": ["src", "tests"],
  "typeCheckingMode": "strict",
  "reportMissingParameterType": true,
  "reportMissingReturnType": true,
  "reportUnknownParameterType": true,
  "reportUnknownArgumentType": true,
  "reportUnknownVariableType": true,
  "pythonVersion": "3.9"
}
```

**Strict Type Checking Enforces:**
- All function parameters must have type hints
- All return types must be specified
- No `Any` types without explicit annotation
- Proper generic type usage

### 3. Pylint - Code Quality Analysis

**Configuration in `pyproject.toml`:**
```toml
[tool.pylint.main]
py-version = "3.9"
source-roots = ["src"]

[tool.pylint.design]
max-args = 8
max-locals = 20
max-returns = 6
max-branches = 15
max-statements = 50
```

## Type Hint Enforcement

### Required Type Annotations
```python
# ✅ GOOD - Complete type annotations
from typing import List, Optional, Dict, Any
from uuid import UUID

async def create_customer(
    name: str,
    email: str,
    preferences: Dict[str, Any]
) -> Customer:
    """Create a new customer with validation"""
    # Implementation

# ❌ BAD - Missing type annotations
async def create_customer(name, email, preferences):
    # Will fail linting
```

### Generic Types
```python
# ✅ GOOD - Proper generic usage
from typing import TypeVar, Generic, List

T = TypeVar('T')

class Repository(Generic[T]):
    async def find_all(self) -> List[T]:
        pass

# ✅ GOOD - Repository implementation
class CustomerRepository(Repository[Customer]):
    async def find_all(self) -> List[Customer]:
        pass
```

### Optional and Union Types
```python
from typing import Optional, Union
from uuid import UUID

# ✅ GOOD - Explicit Optional
async def find_customer(customer_id: UUID) -> Optional[Customer]:
    pass

# ✅ GOOD - Union types when needed
def process_data(data: Union[str, bytes]) -> str:
    pass
```

## Development Workflow

### Makefile Commands
```bash
# Install dependencies
make install

# Format code
make format

# Run all linting
make lint

# Type checking only
make type-check

# Run tests
make test

# Pre-commit checks (format + lint + type-check + test)
make pre-commit

# CI pipeline simulation
make ci
```

### Git Hooks Integration
```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install
```

**`.pre-commit-config.yaml`:**
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.6
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format

  - repo: local
    hooks:
      - id: pyright
        name: pyright
        entry: pyright
        language: system
        types: [python]
        pass_filenames: false
```

## Code Quality Standards

### Mandatory Requirements
1. **100% Type Coverage**: Every function must have complete type annotations
2. **No `Any` Types**: Avoid `Any` unless absolutely necessary with comment explaining why
3. **Import Organization**: Ruff handles automatic import sorting
4. **Security Checks**: All security issues flagged by ruff must be addressed
5. **Complexity Limits**: Functions with McCabe complexity > 10 must be refactored

### Exception Handling
```python
# ✅ GOOD - Typed exceptions
from typing import NoReturn

class BusinessRuleError(Exception):
    def __init__(self, message: str, field: str) -> None:
        super().__init__(message)
        self.field = field

def validate_email(email: str) -> str:
    if not email:
        raise BusinessRuleError("Email is required", "email")
    return email
```

### Async/Await Patterns
```python
# ✅ GOOD - Proper async typing
from typing import AsyncGenerator
from contextlib import asynccontextmanager

@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
```

## Testing with Type Safety

### Test Type Annotations
```python
import pytest
from typing import AsyncGenerator
from unittest.mock import AsyncMock

@pytest.fixture
async def mock_repository() -> AsyncMock:
    return AsyncMock(spec=CustomerRepository)

@pytest.mark.asyncio
async def test_create_customer(
    mock_repository: AsyncMock
) -> None:
    # Test implementation with full typing
    pass
```

### Mock Type Safety
```python
from unittest.mock import AsyncMock
from typing import cast

# ✅ GOOD - Type-safe mocking
mock_repo = cast(CustomerRepository, AsyncMock(spec=CustomerRepository))
mock_repo.find_by_email.return_value = None
```

## CI/CD Integration

### GitHub Actions Type Checking
```yaml
name: Code Quality

on: [push, pull_request]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Format check
        run: |
          ruff format --check src tests
      
      - name: Lint
        run: |
          ruff check src tests
          pylint src
      
      - name: Type check
        run: |
          pyright src tests
      
      - name: Test
        run: |
          pytest
```

## Performance Considerations

### Ruff vs Other Tools
- **Ruff**: 10-100x faster than pylint/flake8
- **Pyright**: Faster than mypy for type checking
- **Combined**: Complete check in seconds vs minutes

### Development Speed
- **Format on save**: Immediate feedback
- **Incremental checking**: Only changed files
- **IDE integration**: Real-time error highlighting

## Troubleshooting

### Common Type Issues
```python
# ❌ PROBLEM: Implicit Any
def process_data(data):
    return data

# ✅ SOLUTION: Explicit typing
def process_data(data: Dict[str, Any]) -> Dict[str, Any]:
    return data
```

### Import Issues
```python
# ❌ PROBLEM: Circular imports
from domain.entities.customer import Customer
from domain.entities.order import Order  # May cause circular import

# ✅ SOLUTION: TYPE_CHECKING import
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from domain.entities.order import Order
```

### Generic Repository Issues
```python
# ❌ PROBLEM: Generic without bounds
T = TypeVar('T')

# ✅ SOLUTION: Bounded generic
from domain.entities.base import BaseEntity
T = TypeVar('T', bound=BaseEntity)
```

## Benefits

### Development Benefits
- **Immediate feedback**: Catch errors before runtime
- **Better IDE support**: Autocomplete and refactoring
- **Code consistency**: Enforced standards across team
- **Reduced debugging**: Type errors caught early

### Production Benefits
- **Fewer runtime errors**: Type safety prevents common bugs
- **Better performance**: No runtime type checking needed  
- **Easier maintenance**: Clear interfaces and contracts
- **Documentation**: Types serve as inline documentation

---
*Document Version: 1.0*
*Last Updated: 2025-08-01*
*Status: Python Development Standards*