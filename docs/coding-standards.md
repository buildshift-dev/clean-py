# Coding Standards

## Python Development Standards

### Datetime Handling

**Always use timezone-aware datetimes to prevent deprecation warnings and ensure consistent behavior across different environments.**

#### ✅ Correct Usage
```python
from datetime import datetime, timezone

# For current UTC time
now = datetime.now(timezone.utc)

# For entity timestamps
created_at = datetime.now(timezone.utc)
updated_at = datetime.now(timezone.utc)
```

#### ❌ Deprecated Usage
```python
from datetime import datetime

# DEPRECATED - will show warnings in Python 3.12+
now = datetime.utcnow()  # Don't use this
```

#### Why This Matters
- `datetime.utcnow()` is deprecated in Python 3.12+ and will be removed in future versions
- Timezone-aware datetimes prevent ambiguity and ensure consistent behavior
- Explicit timezone handling makes code more maintainable and less error-prone

### Import Standards

**Use absolute imports from the `src` package root for all internal modules.**

#### ✅ Correct Usage
```python
from src.domain.entities.customer import Customer
from src.application.use_cases.create_customer import CreateCustomerUseCase
```

#### ❌ Incorrect Usage
```python
from domain.entities.customer import Customer  # Missing src prefix
from .customer import Customer  # Relative imports in tests
```

### Testing Standards

**Use the editable installation approach for development to ensure proper module resolution.**

#### Setup
```bash
# Install package in development mode
pip install -e .

# This enables:
# - Proper import resolution in tests
# - VS Code test discovery
# - IntelliSense support
```

### Type Hints and Strong Typing

**Always use explicit type hints for all function parameters, return values, and class attributes.**

#### ✅ Correct Usage
```python
from typing import List, Dict, Optional, Any
from uuid import UUID
from decimal import Decimal

# Function signatures
async def find_by_id(self, customer_id: UUID) -> Optional[Customer]:
    pass

async def list_all(self) -> List[Customer]:
    pass

# Generic collections with specific types
def process_order_details(self, order_details: Dict[str, Any]) -> Dict[str, str]:
    pass

# Dataclass with full type annotations
@dataclass(frozen=True)
class Customer:
    id: UUID
    name: str
    email: str
    is_active: bool
    preferences: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
```

#### ❌ Incorrect Usage
```python
# Missing type hints
def find_by_id(self, customer_id):
    pass

# Generic types without parameters
def process_orders(self, orders: list):  # Should be List[Order]
    pass

# Using 'dict' instead of Dict[K, V]
def get_config(self) -> dict:  # Should be Dict[str, Any]
    pass
```

### Async/Await Patterns

**Use consistent async patterns for all I/O operations and repository methods.**

#### ✅ Correct Usage
```python
# Repository methods should be async
async def save(self, entity: Customer) -> Customer:
    # Database operations
    pass

# Use case execution should be async
async def execute(self, command: CreateCustomerCommand) -> Customer:
    # Business logic with async calls
    customer = await self._customer_repo.find_by_email(command.email)
    return await self._customer_repo.save(new_customer)

# Proper async context handling
async with session.begin():
    result = await self._session.execute(stmt)
```

#### ❌ Incorrect Usage
```python
# Mixing sync and async without proper handling
def save(self, entity: Customer) -> Customer:
    # This should be async if it involves I/O
    pass

# Not awaiting async calls
async def execute(self, command):
    customer = self._customer_repo.find_by_email(command.email)  # Missing await
```

### Error Handling

**Use specific exceptions and provide meaningful error messages for business logic violations.**

#### ✅ Correct Usage
```python
# Domain-specific exceptions
class CustomerNotFoundError(ValueError):
    def __init__(self, customer_id: UUID):
        super().__init__(f"Customer with ID {customer_id} not found")

class InactiveCustomerError(ValueError):
    def __init__(self, customer_id: UUID):
        super().__init__(f"Cannot create order for inactive customer {customer_id}")

# Use specific validation in business logic
if not customer:
    raise CustomerNotFoundError(command.customer_id)

if not customer.is_active:
    raise InactiveCustomerError(command.customer_id)
```

#### ❌ Incorrect Usage
```python
# Generic exceptions with unclear messages
if not customer:
    raise Exception("Error")  # Too generic

# Using wrong exception types
if not customer.is_active:
    raise RuntimeError("Customer inactive")  # Should be ValueError for business logic
```

### Dataclass Standards

**Use frozen dataclasses for immutable entities and regular dataclasses for mutable DTOs.**

#### ✅ Correct Usage
```python
# Immutable domain entities
@dataclass(frozen=True)
class Customer:
    id: UUID
    name: str
    # ... other fields

# Mutable DTOs/Commands
@dataclass
class CreateCustomerCommand:
    name: str
    email: str
    preferences: Dict[str, Any] = None
```

### Dependency Injection

**Use constructor injection with explicit interface types for all dependencies.**

#### ✅ Correct Usage
```python
class CreateCustomerUseCase:
    def __init__(self, customer_repository: CustomerRepository):
        self._customer_repo = customer_repository  # Use interface type

    async def execute(self, command: CreateCustomerCommand) -> Customer:
        # Implementation uses injected dependency
        pass
```

### Naming Conventions

#### Classes
- Use PascalCase: `CustomerRepository`, `CreateOrderUseCase`
- Interfaces should be abstract base classes: `CustomerRepository` (not `ICustomerRepository`)
- Implementations should include technology: `PostgresCustomerRepository`

#### Functions and Variables
- Use snake_case: `find_by_id`, `customer_repository`, `created_at`
- Use descriptive names: `find_customer_by_email` over `find_by_email` when context isn't clear
- Private attributes use leading underscore: `self._customer_repo`

#### Constants
- Use SCREAMING_SNAKE_CASE: `DEFAULT_PAGE_SIZE`, `MAX_RETRY_ATTEMPTS`

### File Organization

**Follow Clean Architecture layering in directory structure.**

```
src/
├── domain/           # Business logic, entities, interfaces
│   ├── entities/     # Domain entities (Customer, Order)
│   └── repositories/ # Repository interfaces
├── application/      # Use cases, application services
│   └── use_cases/    # Business use cases
├── infrastructure/   # External concerns (database, API clients)
│   └── database/     # Database implementations
└── presentation/     # Controllers, schemas, API definitions
    └── api/          # REST API endpoints
```

### Function Design

**Keep functions focused on a single responsibility with clear inputs and outputs.**

#### ✅ Correct Usage
```python
# Single responsibility, clear signature
async def validate_customer_exists(
    self, 
    customer_id: UUID, 
    repository: CustomerRepository
) -> Customer:
    customer = await repository.find_by_id(customer_id)
    if not customer:
        raise CustomerNotFoundError(customer_id)
    return customer

# Pure functions when possible
def calculate_total_with_tax(base_amount: Decimal, tax_rate: Decimal) -> Decimal:
    return base_amount * (1 + tax_rate)
```

#### ❌ Incorrect Usage
```python
# Multiple responsibilities, unclear what it returns
async def process_customer(self, data):
    # Validates, saves, sends email, logs - too many responsibilities
    pass
```

### Code Comments

**Do not add unnecessary comments unless they explain complex business logic or non-obvious behavior.**

- Code should be self-documenting through clear naming
- Comments should explain "why", not "what"
- Avoid redundant comments that simply restate the code