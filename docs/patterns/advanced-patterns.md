# Advanced Patterns for Production-Ready Applications

## CQRS (Command Query Responsibility Segregation)

CQRS separates read and write operations to optimize each for their specific purpose. This pattern is particularly valuable in complex domains where read and write models have different requirements.

### 1. Basic CQRS Implementation

#### Directory Structure
```
application/
├── use_cases/
│   ├── commands/          # Write operations (state changes)
│   │   ├── create_customer.py
│   │   ├── update_customer.py
│   │   └── delete_customer.py
│   └── queries/           # Read operations (data retrieval)
│       ├── get_customer_orders.py
│       ├── search_customers.py
│       └── customer_analytics.py
```

#### Command Pattern
```python
# application/use_cases/commands/create_customer.py
from dataclasses import dataclass
from typing import Dict, Any
from uuid import uuid4

from src.domain.entities.customer import Customer
from src.domain.repositories.customer_repository import CustomerRepository
from src.shared_kernel import CustomerId, Email

@dataclass
class CreateCustomerCommand:
    """Command to create a new customer"""
    name: str
    email: str
    preferences: Dict[str, Any] = None

class CreateCustomerUseCase:
    """Command handler for creating customers"""
    
    def __init__(self, customer_repository: CustomerRepository):
        self._customer_repo = customer_repository
    
    async def execute(self, command: CreateCustomerCommand) -> Customer:
        """Execute the command - returns the created entity"""
        # Business rule validation
        existing = await self._customer_repo.find_by_email(command.email)
        if existing:
            raise ValueError(f"Customer with email {command.email} already exists")
        
        # Create using domain factory
        customer = Customer.create(
            customer_id=CustomerId(uuid4()),
            name=command.name,
            email=Email(command.email),
            preferences=command.preferences or {}
        )
        
        # Persist and return
        return await self._customer_repo.save(customer)
```

#### Query Pattern
```python
# application/use_cases/queries/search_customers.py
from dataclasses import dataclass
from typing import List, Optional

from src.domain.entities.customer import Customer
from src.domain.repositories.customer_repository import CustomerRepository

@dataclass(frozen=True)
class SearchCustomersQuery:
    """Query parameters for customer search"""
    name_contains: Optional[str] = None
    email_contains: Optional[str] = None
    is_active: Optional[bool] = None
    limit: int = 50
    offset: int = 0
    
    def __post_init__(self) -> None:
        """Validate query parameters"""
        if self.limit <= 0:
            raise ValueError("Limit must be positive")
        if self.limit > 100:
            raise ValueError("Limit cannot exceed 100")
        if self.offset < 0:
            raise ValueError("Offset cannot be negative")

class SearchCustomersUseCase:
    """Query handler for customer search"""
    
    def __init__(self, customer_repository: CustomerRepository):
        self._customer_repository = customer_repository
    
    async def execute(self, query: SearchCustomersQuery) -> List[Customer]:
        """Execute the query - returns list of matching customers"""
        return await self._customer_repository.search(
            name_contains=query.name_contains,
            email_contains=query.email_contains,
            is_active=query.is_active,
            limit=query.limit,
            offset=query.offset
        )
```

### 2. Advanced CQRS with Read Models

For complex reporting scenarios, create dedicated read models optimized for specific views:

```python
# application/read_models/customer_summary.py
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

@dataclass(frozen=True)
class CustomerSummary:
    """Optimized read model for customer overview"""
    customer_id: UUID
    name: str
    email: str
    total_orders: int
    total_spent: Decimal
    last_order_date: Optional[datetime]
    is_active: bool
    preferred_category: Optional[str]

# application/use_cases/queries/get_customer_summary.py
class GetCustomerSummaryQuery:
    """Query for customer summary with aggregated data"""
    
    def __init__(
        self,
        customer_repository: CustomerRepository,
        order_repository: OrderRepository
    ):
        self._customer_repo = customer_repository
        self._order_repo = order_repository
    
    async def execute(self, customer_id: UUID) -> Optional[CustomerSummary]:
        """Get customer summary with aggregated order data"""
        customer = await self._customer_repo.find_by_id(customer_id)
        if not customer:
            return None
        
        # Get aggregated order data
        orders = await self._order_repo.find_by_customer(customer_id)
        
        total_orders = len(orders)
        total_spent = sum(order.total_amount.amount for order in orders)
        last_order_date = max(order.created_at for order in orders) if orders else None
        
        # Analyze preferences (business logic for read model)
        preferred_category = self._analyze_preferred_category(orders)
        
        return CustomerSummary(
            customer_id=customer.id,
            name=customer.name,
            email=str(customer.email),
            total_orders=total_orders,
            total_spent=total_spent,
            last_order_date=last_order_date,
            is_active=customer.is_active,
            preferred_category=preferred_category
        )
    
    def _analyze_preferred_category(self, orders: List[Order]) -> Optional[str]:
        """Business logic for determining preferred category"""
        if not orders:
            return None
        
        # Example: analyze order catalog to find most common category
        categories = [
            order.catalog.get('category') 
            for order in orders 
            if 'category' in order.catalog
        ]
        
        if not categories:
            return None
        
        # Return most common category
        return max(set(categories), key=categories.count)
```

### 3. Repository Extensions for CQRS

Extend repository interfaces to support both command and query operations:

```python
# domain/repositories/customer_repository.py
from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from src.domain.entities.customer import Customer

class CustomerRepository(ABC):
    """Repository supporting both commands and queries"""
    
    # Command operations (write)
    @abstractmethod
    async def save(self, customer: Customer) -> Customer:
        """Save customer (create or update)"""
        pass
    
    @abstractmethod
    async def delete(self, customer_id: UUID) -> None:
        """Delete customer"""
        pass
    
    # Query operations (read)
    @abstractmethod
    async def find_by_id(self, customer_id: UUID) -> Optional[Customer]:
        """Find customer by ID"""
        pass
    
    @abstractmethod
    async def find_by_email(self, email: str) -> Optional[Customer]:
        """Find customer by email"""
        pass
    
    @abstractmethod
    async def search(
        self,
        name_contains: Optional[str] = None,
        email_contains: Optional[str] = None,
        is_active: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Customer]:
        """Advanced search with filters and pagination"""
        pass
    
    @abstractmethod
    async def list_all(self) -> List[Customer]:
        """List all customers"""
        pass
    
    @abstractmethod
    async def count_active(self) -> int:
        """Count active customers (for analytics)"""
        pass
```

### 4. CQRS Benefits and Trade-offs

#### Benefits:
- **Optimized Models**: Read and write models can be optimized independently
- **Performance**: Queries can use denormalized data, indices, and caching
- **Scalability**: Read and write sides can scale independently
- **Clear Intent**: Commands show what changes, queries show what's retrieved
- **Complex Queries**: Support complex reporting without affecting write model

#### Trade-offs:
- **Complexity**: More code and concepts to manage
- **Eventual Consistency**: Read models may lag behind write models
- **Data Duplication**: May require maintaining multiple representations
- **Testing Overhead**: Need to test both command and query sides

### 5. Testing CQRS Patterns

```python
# tests/unit/application/commands/test_create_customer.py
import pytest
from unittest.mock import AsyncMock
from uuid import uuid4

from src.application.use_cases.commands.create_customer import (
    CreateCustomerCommand,
    CreateCustomerUseCase,
)

@pytest.mark.asyncio
class TestCreateCustomerUseCase:
    async def test_create_customer_success(self):
        """Test successful customer creation"""
        # Arrange
        mock_repo = AsyncMock()
        mock_repo.find_by_email.return_value = None  # No existing customer
        mock_repo.save.side_effect = lambda c: c
        
        use_case = CreateCustomerUseCase(mock_repo)
        command = CreateCustomerCommand(
            name="John Doe",
            email="john@example.com",
            preferences={"theme": "dark"}
        )
        
        # Act
        result = await use_case.execute(command)
        
        # Assert
        assert result.name == "John Doe"
        assert str(result.email) == "john@example.com"
        assert result.preferences == {"theme": "dark"}
        mock_repo.find_by_email.assert_called_once_with("john@example.com")
        mock_repo.save.assert_called_once()

# tests/unit/application/queries/test_search_customers.py
@pytest.mark.asyncio
class TestSearchCustomersUseCase:
    async def test_search_with_filters(self):
        """Test customer search with filters"""
        # Arrange
        mock_repo = AsyncMock()
        expected_customers = [
            # Mock customer objects
        ]
        mock_repo.search.return_value = expected_customers
        
        use_case = SearchCustomersUseCase(mock_repo)
        query = SearchCustomersQuery(
            name_contains="John",
            is_active=True,
            limit=10
        )
        
        # Act
        result = await use_case.execute(query)
        
        # Assert
        assert result == expected_customers
        mock_repo.search.assert_called_once_with(
            name_contains="John",
            email_contains=None,
            is_active=True,
            limit=10,
            offset=0
        )
```

### 6. API Integration with CQRS

```python
# presentation/api/v1/customers.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from src.application.use_cases.commands.create_customer import (
    CreateCustomerCommand,
    CreateCustomerUseCase,
)
from src.application.use_cases.queries.search_customers import (
    SearchCustomersQuery,
    SearchCustomersUseCase,
)

router = APIRouter(prefix="/api/v1/customers", tags=["customers"])

# Command endpoint (write)
@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_customer(
    request: CreateCustomerRequest,
    use_case: CreateCustomerUseCase = Depends(get_create_customer_use_case),
) -> CustomerResponse:
    """Create a new customer"""
    command = CreateCustomerCommand(
        name=request.name,
        email=request.email,
        preferences=request.preferences
    )
    
    try:
        customer = await use_case.execute(command)
        return CustomerResponse.from_domain(customer)
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))

# Query endpoint (read)
@router.get("/search")
async def search_customers(
    name: Optional[str] = None,
    email: Optional[str] = None,
    is_active: Optional[bool] = None,
    limit: int = 50,
    offset: int = 0,
    use_case: SearchCustomersUseCase = Depends(get_search_customers_use_case),
) -> List[CustomerResponse]:
    """Search customers with filters"""
    query = SearchCustomersQuery(
        name_contains=name,
        email_contains=email,
        is_active=is_active,
        limit=limit,
        offset=offset
    )
    
    customers = await use_case.execute(query)
    return [CustomerResponse.from_domain(c) for c in customers]
```

## Error Handling Patterns

### 1. Domain-Specific Exception Hierarchy
```python
# domain/exceptions.py
class CatalogError(Exception):
    """Base exception for all catalog operations"""
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}

class ProductNotFoundError(CatalogError):
    """Product does not exist"""
    pass

class InvalidProductCodeError(CatalogError):
    """Product version configuration is invalid"""
    pass

class OverlappingDateRangeError(CatalogError):
    """Date ranges overlap between product versions"""
    pass

class BusinessRuleError(CatalogError):
    """Validation rule execution failed"""
    pass

class BusinessRuleViolationError(CatalogError):
    """Business rule constraint violated"""
    pass
```

### 2. Result Pattern for Use Cases
```python
# application/common/result.py
from typing import Generic, TypeVar, Union
from dataclasses import dataclass

T = TypeVar('T')
E = TypeVar('E', bound=Exception)

@dataclass(frozen=True)
class Success(Generic[T]):
    value: T
    
    def is_success(self) -> bool:
        return True
    
    def is_failure(self) -> bool:
        return False

@dataclass(frozen=True)
class Failure(Generic[E]):
    error: E
    
    def is_success(self) -> bool:
        return False
    
    def is_failure(self) -> bool:
        return True

Result = Union[Success[T], Failure[E]]

# application/use_cases/create_product.py
from application.common.result import Result, Success, Failure

class CreateProductUseCase:
    async def execute(self, command: CreateProductCommand) -> Result[Product, CatalogError]:
        try:
            # Check if product already exists
            existing = await self._product_repo.find_by_mnemonic(
                ProductCode(command.mnemonic)
            )
            if existing:
                return Failure(ProductAlreadyExistsError(
                    f"Product with mnemonic {command.mnemonic} already exists",
                    details={"mnemonic": command.mnemonic}
                ))
            
            # Create and save product
            product = Product(...)
            saved_product = await self._product_repo.save(product)
            
            return Success(saved_product)
            
        except DatabaseError as e:
            return Failure(CatalogError(
                "Database operation failed",
                error_code="DATABASE_ERROR",
                details={"original_error": str(e)}
            ))
        except Exception as e:
            return Failure(CatalogError(
                "Unexpected error occurred",
                error_code="INTERNAL_ERROR",
                details={"original_error": str(e)}
            ))
```

### 3. FastAPI Error Handler
```python
# presentation/api/error_handlers.py
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

class ErrorResponse:
    def __init__(self, error_code: str, message: str, details: dict = None):
        self.error_code = error_code
        self.message = message
        self.details = details or {}

async def catalog_error_handler(request: Request, exc: CatalogError) -> JSONResponse:
    """Handle domain-specific errors"""
    status_code = get_status_code_for_error(exc)
    
    logger.warning(
        f"Catalog error: {exc.error_code}",
        extra={
            "error_code": exc.error_code,
            "message": exc.message,
            "details": exc.details,
            "path": request.url.path
        }
    )
    
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details
            }
        }
    )

def get_status_code_for_error(error: CatalogError) -> int:
    """Map domain errors to HTTP status codes"""
    mapping = {
        ProductNotFoundError: 404,
        ProductAlreadyExistsError: 409,
        InvalidProductCodeError: 400,
        BusinessRuleError: 422,
        BusinessRuleViolationError: 400,
    }
    return mapping.get(type(error), 500)

# presentation/main.py
from fastapi import FastAPI
from presentation.api.error_handlers import catalog_error_handler

app = FastAPI()
app.add_exception_handler(CatalogError, catalog_error_handler)
```

### 4. Route Handler with Result Pattern
```python
# presentation/api/v1/product.py
@router.post("/", response_model=ProductResponse)
async def create_product(
    request: CreateProductRequest,
    use_case: CreateProductUseCase = Depends(get_create_product_use_case)
):
    """Create product with proper error handling"""
    command = CreateProductCommand(...)
    result = await use_case.execute(command)
    
    if result.is_failure():
        # Error handler will catch and format this
        raise result.error
    
    return ProductResponse.from_domain(result.value)
```

## Logging and Monitoring Patterns

### 1. Structured Logging
```python
# infrastructure/logging/logger.py
import logging
import sys
from typing import Any, Dict
import json
from datetime import datetime

class StructuredLogger:
    def __init__(self, name: str, level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        
        # JSON formatter for structured logs
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        self.logger.addHandler(handler)
    
    def info(self, message: str, **kwargs):
        self._log("INFO", message, **kwargs)
    
    def error(self, message: str, **kwargs):
        self._log("ERROR", message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        self._log("WARNING", message, **kwargs)
    
    def _log(self, level: str, message: str, **kwargs):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message,
            "service": "catalog-api",
            **kwargs
        }
        
        self.logger.log(
            getattr(logging, level),
            json.dumps(log_data)
        )

class JsonFormatter(logging.Formatter):
    def format(self, record):
        return record.getMessage()
```

### 2. Application Logging Patterns
```python
# application/use_cases/create_product.py
from infrastructure.logging.logger import StructuredLogger

class CreateProductUseCase:
    def __init__(self, product_repository: ProductRepository):
        self._product_repo = product_repository
        self._logger = StructuredLogger(__name__)
    
    async def execute(self, command: CreateProductCommand) -> Result[Product, CatalogError]:
        self._logger.info(
            "Creating product",
            operation="create_product",
            mnemonic=command.mnemonic,
            user_id=command.user_id
        )
        
        try:
            result = await self._create_product_internal(command)
            
            if result.is_success():
                self._logger.info(
                    "Product created successfully",
                    operation="create_product",
                    product_id=str(result.value.id),
                    mnemonic=command.mnemonic
                )
            else:
                self._logger.warning(
                    "Product creation failed",
                    operation="create_product",
                    error_code=result.error.error_code,
                    mnemonic=command.mnemonic
                )
            
            return result
            
        except Exception as e:
            self._logger.error(
                "Unexpected error in product creation",
                operation="create_product",
                error=str(e),
                mnemonic=command.mnemonic,
                exc_info=True
            )
            raise
```

### 3. Database Operation Logging
```python
# infrastructure/database/repositories/base_repository.py
from infrastructure.logging.logger import StructuredLogger
import time

class BaseRepository:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._logger = StructuredLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def _execute_with_logging(
        self, 
        operation: str, 
        query_func, 
        **context
    ):
        """Execute database operation with logging"""
        start_time = time.time()
        
        self._logger.info(
            f"Executing {operation}",
            operation=f"db_{operation}",
            **context
        )
        
        try:
            result = await query_func()
            duration = time.time() - start_time
            
            self._logger.info(
                f"{operation} completed",
                operation=f"db_{operation}",
                duration_ms=round(duration * 1000, 2),
                **context
            )
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            
            self._logger.error(
                f"{operation} failed",
                operation=f"db_{operation}",
                error=str(e),
                duration_ms=round(duration * 1000, 2),
                **context
            )
            raise
```

### 4. Monitoring Integration
```python
# infrastructure/monitoring/metrics.py
from typing import Dict, Any
import time
from functools import wraps

class MetricsCollector:
    def __init__(self):
        self.counters: Dict[str, int] = {}
        self.timers: Dict[str, list] = {}
    
    def increment(self, metric_name: str, tags: Dict[str, str] = None):
        """Increment a counter metric"""
        key = self._make_key(metric_name, tags)
        self.counters[key] = self.counters.get(key, 0) + 1
    
    def timing(self, metric_name: str, duration: float, tags: Dict[str, str] = None):
        """Record timing metric"""
        key = self._make_key(metric_name, tags)
        if key not in self.timers:
            self.timers[key] = []
        self.timers[key].append(duration)
    
    def _make_key(self, metric_name: str, tags: Dict[str, str] = None) -> str:
        if not tags:
            return metric_name
        tag_str = ",".join(f"{k}:{v}" for k, v in sorted(tags.items()))
        return f"{metric_name}[{tag_str}]"

metrics = MetricsCollector()

def measure_time(metric_name: str, tags: Dict[str, str] = None):
    """Decorator to measure execution time"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                metrics.timing(
                    metric_name, 
                    time.time() - start_time,
                    tags
                )
                return result
            except Exception as e:
                metrics.increment(
                    f"{metric_name}.error",
                    {**(tags or {}), "error_type": type(e).__name__}
                )
                raise
        return wrapper
    return decorator

# Usage in use cases
class CreateProductUseCase:
    @measure_time("use_case.create_product", {"operation": "create"})
    async def execute(self, command: CreateProductCommand):
        # Implementation
        pass
```

## Configuration Management Patterns

### 1. Environment-Based Configuration
```python
# infrastructure/config/settings.py
from pydantic import BaseSettings, Field
from typing import Optional, List
import os

class DatabaseSettings(BaseSettings):
    url: str = Field(..., env="DATABASE_URL")
    pool_size: int = Field(20, env="DB_POOL_SIZE")
    max_overflow: int = Field(10, env="DB_MAX_OVERFLOW")
    echo: bool = Field(False, env="DB_ECHO")
    
    class Config:
        env_prefix = "DB_"

class LoggingSettings(BaseSettings):
    level: str = Field("INFO", env="LOG_LEVEL")
    format: str = Field("json", env="LOG_FORMAT")
    
    class Config:
        env_prefix = "LOG_"

class APISettings(BaseSettings):
    title: str = Field("Catalog API", env="API_TITLE")
    version: str = Field("1.0.0", env="API_VERSION")
    debug: bool = Field(False, env="DEBUG")
    cors_origins: List[str] = Field(["*"], env="CORS_ORIGINS")
    
    class Config:
        env_prefix = "API_"

class Settings(BaseSettings):
    environment: str = Field("development", env="ENVIRONMENT")
    database: DatabaseSettings = DatabaseSettings()
    logging: LoggingSettings = LoggingSettings()
    api: APISettings = APISettings()
    
    # Feature flags
    enable_metrics: bool = Field(True, env="ENABLE_METRICS")
    enable_validation_caching: bool = Field(False, env="ENABLE_VALIDATION_CACHING")
    
    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        return self.environment.lower() == "development"

# Singleton pattern for settings
_settings: Optional[Settings] = None

def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
```

### 2. Configuration Validation
```python
# infrastructure/config/validation.py
from pydantic import validator
import sqlalchemy

class DatabaseSettings(BaseSettings):
    url: str = Field(..., env="DATABASE_URL")
    
    @validator('url')
    def validate_database_url(cls, v):
        """Validate database URL format"""
        try:
            # Test URL parsing
            engine = sqlalchemy.create_engine(v, strategy='mock', executor=lambda sql, *_: None)
            return v
        except Exception:
            raise ValueError("Invalid database URL format")
    
    @validator('pool_size')
    def validate_pool_size(cls, v):
        if v < 1 or v > 100:
            raise ValueError("Pool size must be between 1 and 100")
        return v

class Settings(BaseSettings):
    @validator('environment')
    def validate_environment(cls, v):
        allowed = ['development', 'staging', 'production']
        if v.lower() not in allowed:
            raise ValueError(f"Environment must be one of: {allowed}")
        return v.lower()
```

### 3. Configuration per Environment
```python
# config/development.py
DATABASE_URL = "postgresql://user:pass@localhost:5432/catalog_dev"
LOG_LEVEL = "DEBUG"
API_DEBUG = True
ENABLE_METRICS = False

# config/production.py  
DATABASE_URL = "${DATABASE_URL}"  # From environment
LOG_LEVEL = "INFO"
API_DEBUG = False
ENABLE_METRICS = True
CORS_ORIGINS = ["https://catalog-ui.company.com"]

# Load configuration based on environment
def load_config():
    env = os.getenv("ENVIRONMENT", "development")
    if env == "production":
        from config import production as config
    else:
        from config import development as config
    
    return config
```

## Standardized API Response Pattern

### 1. Unified Response Template
All API endpoints return responses using a consistent template to provide predictable structure for frontend developers and consistent user experience.

```python
# presentation/schemas/common.py
from typing import Generic, TypeVar, Optional, Literal
from pydantic import BaseModel

T = TypeVar('T')

class ApiResponse(BaseModel, Generic[T]):
    """Standardized API response template"""
    statusCode: int
    message: str
    type: Literal['success', 'error', 'warning', 'neutral']
    data: Optional[T] = None
    
    @classmethod
    def success(
        cls, 
        data: T, 
        message: str = "Operation completed successfully",
        status_code: int = 200
    ) -> 'ApiResponse[T]':
        """Create successful response"""
        return cls(
            statusCode=status_code, 
            message=message, 
            type="success", 
            data=data
        )
    
    @classmethod
    def created(
        cls, 
        data: T, 
        message: str = "Resource created successfully"
    ) -> 'ApiResponse[T]':
        """Create resource created response"""
        return cls(
            statusCode=201, 
            message=message, 
            type="success", 
            data=data
        )
    
    @classmethod
    def error(
        cls, 
        message: str, 
        status_code: int = 400,
        data: Optional[T] = None
    ) -> 'ApiResponse[Optional[T]]':
        """Create error response"""
        return cls(
            statusCode=status_code, 
            message=message, 
            type="error", 
            data=data
        )
    
    @classmethod
    def warning(
        cls, 
        data: T, 
        message: str,
        status_code: int = 200
    ) -> 'ApiResponse[T]':
        """Create warning response (operation succeeded with warnings)"""
        return cls(
            statusCode=status_code, 
            message=message, 
            type="warning", 
            data=data
        )
    
    @classmethod
    def neutral(
        cls, 
        data: T, 
        message: str,
        status_code: int = 200
    ) -> 'ApiResponse[T]':
        """Create neutral response (informational)"""
        return cls(
            statusCode=status_code, 
            message=message, 
            type="neutral", 
            data=data
        )
```

### 2. Response Examples
```json
// Success Response
{
  "statusCode": 201,
  "message": "Product 'BANKING_DATA' created successfully",
  "type": "success",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "mnemonic": "BANKING_DATA",
    "overview": "Banking transaction data product",
    "is_confidential": false,
    "created_at": "2024-01-15"
  }
}

// Error Response
{
  "statusCode": 409,
  "message": "Product with mnemonic 'BANKING_DATA' already exists",
  "type": "error",
  "data": null
}

// Warning Response (partial success)
{
  "statusCode": 200,
  "message": "Data processed with 3 validation warnings",
  "type": "warning",
  "data": {
    "processed_count": 1000,
    "warning_count": 3,
    "warnings": ["Missing optional field 'category' in 3 records"]
  }
}

// List Response
{
  "statusCode": 200,
  "message": "Found 15 product matching criteria",
  "type": "success",
  "data": {
    "items": [...],
    "total_count": 15,
    "page": 1,
    "page_size": 10
  }
}
```

### 3. Route Implementation
```python
# presentation/api/v1/product.py
from presentation.schemas.common import ApiResponse

@router.post("/", response_model=ApiResponse[ProductResponse])
async def create_product(
    request: CreateProductRequest,
    use_case: CreateProductUseCase = Depends(get_create_product_use_case)
) -> ApiResponse[ProductResponse]:
    """Create new product with standardized response"""
    command = CreateProductCommand(...)
    result = await use_case.execute(command)
    
    if result.is_success():
        product_data = ProductResponse.from_domain(result.value)
        return ApiResponse.created(
            data=product_data,
            message=f"Product '{request.mnemonic}' created successfully"
        )
    else:
        return ApiResponse.error(
            message=result.error.message,
            status_code=get_status_code_for_error(result.error)
        )

@router.get("/{product_id}", response_model=ApiResponse[ProductResponse])
async def get_product(
    product_id: UUID,
    product_repo: ProductRepository = Depends(get_product_repository)
) -> ApiResponse[ProductResponse]:
    """Get product by ID with standardized response"""
    product = await product_repo.find_by_id(product_id)
    
    if not product:
        return ApiResponse.error(
            message=f"Product with ID '{product_id}' not found",
            status_code=404
        )
    
    return ApiResponse.success(
        data=ProductResponse.from_domain(product),
        message="Product retrieved successfully"
    )

@router.get("/", response_model=ApiResponse[List[ProductResponse]])
async def list_product(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    product_repo: ProductRepository = Depends(get_product_repository)
) -> ApiResponse[dict]:
    """List product with pagination"""
    product_list = await product_repo.list_paginated(page, page_size)
    total_count = await product_repo.count_all()
    
    return ApiResponse.success(
        data={
            "items": [ProductResponse.from_domain(s) for s in product_list],
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "has_more": (page * page_size) < total_count
        },
        message=f"Found {len(product_list)} product (page {page})"
    )
```

### 4. Error Handler Integration
```python
# presentation/api/error_handlers.py
async def catalog_error_handler(request: Request, exc: CatalogError) -> JSONResponse:
    """Handle domain-specific errors with standardized response"""
    status_code = get_status_code_for_error(exc)
    
    response = ApiResponse.error(
        message=exc.message,
        status_code=status_code,
        data=exc.details if exc.details else None
    )
    
    return JSONResponse(
        status_code=status_code,
        content=response.dict()
    )

async def validation_error_handler(request: Request, exc: BusinessRuleError) -> JSONResponse:
    """Handle Pydantic validation errors"""
    error_details = []
    for error in exc.errors():
        error_details.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    response = ApiResponse.error(
        message="Request validation failed",
        status_code=422,
        data={"validation_errors": error_details}
    )
    
    return JSONResponse(
        status_code=422,
        content=response.dict()
    )
```

### 5. Frontend Integration Benefits
```typescript
// TypeScript interface matching API response
interface ApiResponse<T> {
  statusCode: number;
  message: string;
  type: 'success' | 'error' | 'warning' | 'neutral';
  data: T | null;
}

// Generic API client
class ApiClient {
  async handleResponse<T>(response: Response): Promise<T> {
    const apiResponse: ApiResponse<T> = await response.json();
    
    // Automatically show user messages
    this.showToast(apiResponse.message, apiResponse.type);
    
    // Throw error for failed responses
    if (apiResponse.type === 'error') {
      throw new ApiError(apiResponse.message, apiResponse.statusCode);
    }
    
    // Return the actual data
    return apiResponse.data;
  }
  
  showToast(message: string, type: string) {
    // Show appropriate toast notification
    const toastClass = {
      'success': 'toast-success',
      'error': 'toast-error', 
      'warning': 'toast-warning',
      'neutral': 'toast-info'
    }[type];
    
    showToast(message, toastClass);
  }
}

// Usage in components
const productApi = {
  async createProduct(data: CreateProductRequest): Promise<Product> {
    const response = await fetch('/api/v1/product', {
      method: 'POST',
      body: JSON.stringify(data)
    });
    
    // Automatically handles messages and errors
    return apiClient.handleResponse<Product>(response);
  }
};
```

### 6. Message Generation Guidelines
```python
# Message templates for consistency
class MessageTemplates:
    # Success messages
    CREATED = "{resource} '{identifier}' created successfully"
    UPDATED = "{resource} '{identifier}' updated successfully"  
    DELETED = "{resource} '{identifier}' deleted successfully"
    RETRIEVED = "{resource} retrieved successfully"
    LISTED = "Found {count} {resource}(s)"
    
    # Error messages
    NOT_FOUND = "{resource} with {field} '{value}' not found"
    ALREADY_EXISTS = "{resource} with {field} '{value}' already exists"
    VALIDATION_FAILED = "{field} validation failed: {reason}"
    UNAUTHORIZED = "Insufficient permissions to {action} {resource}"
    
    # Warning messages
    PARTIAL_SUCCESS = "{action} completed with {warning_count} warning(s)"
    DEPRECATED = "This endpoint is deprecated. Please use {alternative}"

# Usage in routes
return ApiResponse.created(
    data=product_data,
    message=MessageTemplates.CREATED.format(
        resource="Product",
        identifier=request.mnemonic
    )
)
```

### 7. Benefits Summary

**For Frontend Developers:**
- Consistent response structure across all endpoints
- Automatic user message handling
- Predictable error structures
- Type safety with TypeScript interfaces

**For Users:**
- Consistent messaging throughout the application
- Clear success/error/warning indicators
- Contextual feedback for all operations

**For API Developers:**
- Standardized response creation
- Consistent error handling
- Reduced boilerplate code
- Better API documentation

**For Testing:**
- Predictable response structures
- Easier assertion writing
- Consistent error scenarios

## API Versioning Strategy

### 1. URL-Based Versioning
```python
# presentation/api/v1/product.py
from fastapi import APIRouter

router_v1 = APIRouter(prefix="/api/v1", tags=["v1"])

@router_v1.post("/product")
async def create_product_v1(request: CreateProductRequestV1):
    # V1 implementation
    pass

# presentation/api/v2/product.py
router_v2 = APIRouter(prefix="/api/v2", tags=["v2"])

@router_v2.post("/product")
async def create_product_v2(request: CreateProductRequestV2):
    # V2 implementation with new fields
    pass

# presentation/main.py
app.include_router(router_v1)
app.include_router(router_v2)
```

### 2. Schema Evolution
```python
# presentation/schemas/v1/product_schemas.py
class CreateProductRequestV1(BaseModel):
    mnemonic: str
    overview: str
    is_confidential: bool = False

# presentation/schemas/v2/product_schemas.py
class CreateProductRequestV2(BaseModel):
    mnemonic: str
    overview: str
    is_confidential: bool = False
    # New fields in V2
    category: Optional[str] = None
    tags: List[str] = []
    
    # Backward compatibility
    @classmethod
    def from_v1(cls, v1_request: CreateProductRequestV1) -> 'CreateProductRequestV2':
        return cls(
            mnemonic=v1_request.mnemonic,
            overview=v1_request.overview,
            is_confidential=v1_request.is_confidential,
            category=None,
            tags=[]
        )
```

### 3. Version Deprecation Strategy
```python
# presentation/api/v1/product.py
from fastapi import Header
import warnings

@router_v1.post("/product")
async def create_product_v1(
    request: CreateProductRequestV1,
    user_agent: str = Header(None)
):
    """
    Create product - V1 (DEPRECATED)
    
    **This version is deprecated. Please migrate to /api/v2/product**
    
    Deprecation Date: 2024-06-01
    Removal Date: 2024-12-01
    """
    warnings.warn(
        "API v1 is deprecated. Please use v2.",
        DeprecationWarning,
        stacklevel=2
    )
    
    # Log usage for monitoring
    logger.warning(
        "Deprecated API v1 used",
        endpoint="/api/v1/product",
        user_agent=user_agent,
        deprecation_date="2024-06-01"
    )
    
    # Convert to v2 internally
    v2_request = CreateProductRequestV2.from_v1(request)
    return await create_product_v2_internal(v2_request)
```

## Security Patterns

### 1. Authentication & Authorization
```python
# infrastructure/security/auth.py
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from typing import Optional

security = HTTPBearer()

class User:
    def __init__(self, user_id: str, roles: List[str]):
        self.user_id = user_id
        self.roles = roles
    
    def has_role(self, role: str) -> bool:
        return role in self.roles

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Optional[User]:
    """Extract user from JWT token"""
    try:
        payload = jwt.decode(
            credentials.credentials,
            get_settings().jwt_secret,
            algorithms=["HS256"]
        )
        user_id = payload.get("sub")
        roles = payload.get("roles", [])
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        return User(user_id=user_id, roles=roles)
        
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

def require_role(required_role: str):
    """Decorator to require specific role"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            user = kwargs.get('current_user')
            if not user or not user.has_role(required_role):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role '{required_role}' required"
                )
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# Usage in routes
@router.post("/product")
async def create_product(
    request: CreateProductRequest,
    current_user: User = Depends(get_current_user)
):
    if not current_user.has_role("catalog_admin"):
        raise HTTPException(status.HTTP_403_FORBIDDEN)
    
    # Create product...
```

### 2. Input Validation & Sanitization
```python
# presentation/security/validation.py
from pydantic import validator, Field
import re

class CreateProductRequest(BaseModel):
    mnemonic: str = Field(..., min_length=1, max_length=50)
    overview: str = Field(..., max_length=1000)
    
    @validator('mnemonic')
    def validate_mnemonic(cls, v):
        # Only alphanumeric and underscores
        if not re.match(r'^[A-Z0-9_]+$', v):
            raise ValueError('Mnemonic must contain only uppercase letters, numbers, and underscores')
        return v
    
    @validator('overview')
    def sanitize_overview(cls, v):
        # Remove potential XSS
        import html
        return html.escape(v.strip())

# SQL Injection Prevention (SQLAlchemy handles this)
class ProductRepository:
    async def find_by_mnemonic_pattern(self, pattern: str) -> List[Product]:
        # Safe - SQLAlchemy handles parameterization
        stmt = select(ProductModel).where(
            ProductModel.mnemonic.like(f"%{pattern}%")
        )
        result = await self._session.execute(stmt)
        return [self._model_to_entity(model) for model in result.scalars()]
```

### 3. Rate Limiting
```python
# infrastructure/security/rate_limiting.py
from fastapi import HTTPException, Request
from collections import defaultdict
from datetime import datetime, timedelta
import asyncio

class RateLimiter:
    def __init__(self):
        self.requests = defaultdict(list)
        self.cleanup_task = None
    
    async def check_rate_limit(self, key: str, limit: int, window_seconds: int) -> bool:
        """Check if request is within rate limit"""
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=window_seconds)
        
        # Clean old requests
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if req_time > window_start
        ]
        
        # Check limit
        if len(self.requests[key]) >= limit:
            return False
        
        # Add current request
        self.requests[key].append(now)
        return True

rate_limiter = RateLimiter()

async def rate_limit_dependency(request: Request):
    """Rate limiting dependency"""
    client_ip = request.client.host
    
    # 100 requests per minute per IP
    if not await rate_limiter.check_rate_limit(client_ip, 100, 60):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded"
        )

# Usage
@router.post("/product", dependencies=[Depends(rate_limit_dependency)])
async def create_product(request: CreateProductRequest):
    # Implementation
    pass
```

## Performance Optimization Patterns

### 1. Caching Strategy
```python
# infrastructure/cache/redis_cache.py
import redis.asyncio as redis
import json
from typing import Optional, Any
import pickle

class RedisCache:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        value = await self.redis.get(key)
        if value:
            return pickle.loads(value)
        return None
    
    async def set(self, key: str, value: Any, expire_seconds: int = 3600):
        """Set value in cache"""
        await self.redis.set(
            key, 
            pickle.dumps(value),
            ex=expire_seconds
        )
    
    async def delete(self, key: str):
        """Delete key from cache"""
        await self.redis.delete(key)

# Caching decorator
def cache_result(cache_key_template: str, expire_seconds: int = 3600):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = cache_key_template.format(*args, **kwargs)
            
            # Try cache first
            cached = await cache.get(cache_key)
            if cached is not None:
                return cached
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            await cache.set(cache_key, result, expire_seconds)
            
            return result
        return wrapper
    return decorator

# Usage in repository
class ProductRepository:
    @cache_result("product:mnemonic:{}", expire_seconds=1800)
    async def find_by_mnemonic(self, mnemonic: str) -> Optional[Product]:
        # Database query
        pass
```

### 2. Database Query Optimization
```python
# infrastructure/database/repositories/optimized_product_repository.py
from sqlalchemy.orm import selectinload, joinedload

class OptimizedProductRepository:
    async def find_with_versions_and_items(self, product_id: UUID) -> Optional[Product]:
        """Optimized query to fetch product with related data"""
        stmt = (
            select(ProductModel)
            .options(
                selectinload(ProductModel.versions)
                .selectinload(ProductModel.items)
            )
            .where(ProductModel.id == product_id)
        )
        
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            return None
        
        return self._model_to_entity(model)
    
    async def find_product_for_date_range(
        self, 
        start_date: date, 
        end_date: date
    ) -> List[Product]:
        """Optimized date range query with indexes"""
        stmt = (
            select(ProductModel)
            .join(ProductModel)
            .where(
                and_(
                    ProductModel.start_date <= end_date,
                    or_(
                        ProductModel.end_date.is_(None),
                        ProductModel.end_date >= start_date
                    )
                )
            )
            .options(selectinload(ProductModel.versions))
        )
        
        result = await self._session.execute(stmt)
        return [self._model_to_entity(model) for model in result.scalars()]
```

### 3. Connection Pool Optimization
```python
# infrastructure/database/connection.py
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import QueuePool

def create_optimized_engine(database_url: str, is_production: bool = False):
    """Create optimized database engine"""
    if is_production:
        return create_async_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=20,           # Base connections
            max_overflow=30,        # Additional connections
            pool_pre_ping=True,     # Validate connections
            pool_recycle=3600,      # Recycle every hour
            echo=False
        )
    else:
        return create_async_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=5,
            pool_pre_ping=True,
            echo=True  # Show SQL in development
        )
```

## Data Migration Patterns

### 1. Alembic Migration Structure
```python
# migrations/versions/001_initial_schema.py
"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2024-01-15 10:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create product table
    op.create_table(
        'product',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('mnemonic', sa.String(50), unique=True, nullable=False),
        sa.Column('overview', sa.String(500)),
        sa.Column('is_confidential', sa.Boolean(), default=False),
        sa.Column('created_at', sa.Date(), nullable=False),
        sa.Column('updated_at', sa.Date(), nullable=False),
    )
    
    # Create indexes
    op.create_index('ix_product_mnemonic', 'product', ['mnemonic'])
    
    # Create product versions table
    op.create_table(
        'products',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), 
                 sa.ForeignKey('product.id'), nullable=False),
        sa.Column('version_label', sa.String(50), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date()),
    )
    
    # Create date range indexes for performance
    op.create_index('ix_versions_date_range', 'products', 
                   ['start_date', 'end_date'])

def downgrade():
    op.drop_table('products')
    op.drop_table('product')
```

### 2. Data Migration with Validation
```python
# migrations/versions/002_add_jsonb_validation_rules.py
"""Add JSONB validation rules

Revision ID: 002
Revises: 001
Create Date: 2024-01-20 10:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    # Add validation tables
    op.create_table(
        'validation_instances',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), 
                 sa.ForeignKey('product.id'), nullable=False),
        sa.Column('parameters', postgresql.JSONB, nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date()),
    )
    
    # Create JSONB indexes
    op.create_index(
        'ix_validation_parameters_gin',
        'validation_instances',
        ['parameters'],
        postgresql_using='gin'
    )

def downgrade():
    op.drop_table('validation_instances')

# Custom migration with data transformation
def migrate_existing_validation_data():
    """Custom migration to transform existing data"""
    connection = op.get_bind()
    
    # Get existing validation data
    result = connection.execute(
        "SELECT id, validation_config FROM old_validations"
    )
    
    for row in result:
        # Transform old format to new JSONB
        old_config = json.loads(row.validation_config)
        new_parameters = transform_validation_config(old_config)
        
        # Insert into new table
        connection.execute(
            "INSERT INTO validation_instances (id, parameters, ...) VALUES (%s, %s, ...)",
            (row.id, json.dumps(new_parameters))
        )
```

### 3. Zero-Downtime Migration Strategy
```python
# migrations/zero_downtime_pattern.py
"""
Zero-downtime migration pattern:
1. Add new column (nullable)
2. Deploy code that writes to both old and new
3. Backfill data
4. Deploy code that reads from new column
5. Remove old column
"""

# Step 1: Add new column
def upgrade_step_1():
    op.add_column('product', 
        sa.Column('new_catalog', postgresql.JSONB, nullable=True)
    )

# Step 2: Backfill data (separate script)
def backfill_catalog():
    """Run this after step 1 deployment"""
    connection = op.get_bind()
    
    # Batch process existing records
    batch_size = 1000
    offset = 0
    
    while True:
        result = connection.execute(f"""
            SELECT id, old_catalog_field
            FROM product
            WHERE new_catalog IS NULL
            LIMIT {batch_size} OFFSET {offset}
        """)
        
        rows = result.fetchall()
        if not rows:
            break
            
        for row in rows:
            new_value = transform_catalog(row.old_catalog_field)
            connection.execute(
                "UPDATE product SET new_catalog = %s WHERE id = %s",
                (json.dumps(new_value), row.id)
            )
        
        offset += batch_size

# Step 3: Make column non-nullable and remove old column
def upgrade_step_3():
    op.alter_column('product', 'new_catalog', nullable=False)
    op.drop_column('product', 'old_catalog_field')
```

---
*Document Version: 1.1*
*Last Updated: 2025-08-03*  
*Status: Advanced Patterns Guide - Added CQRS Implementation*