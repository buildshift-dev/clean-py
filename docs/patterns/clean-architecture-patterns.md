# Clean Architecture and DDD Patterns Guide

## Overview
This document outlines the architectural patterns and coding standards for building applications using Domain-Driven Design (DDD) and Clean Architecture principles with Python, FastAPI, and PostgreSQL.

## Related Documentation

- [Domain-Driven Design Patterns](./domain-driven-design.md) - Detailed DDD concepts (Entities, Value Objects, Aggregates, etc.)
- [Shared Kernel Guide](./shared-kernel-guide.md) - Implementation guide for shared domain concepts
- [Advanced Patterns](./advanced-patterns.md) - CQRS, Event Sourcing, and other advanced patterns

## Core Principles

### 1. Dependency Rule
Dependencies must point inward. Inner layers know nothing about outer layers.

```
[External World] → [Infrastructure] → [Application] → [Domain] ← (no dependencies)
```

### 2. Layer Responsibilities

- **Domain Layer**: Business logic and rules
- **Application Layer**: Use case orchestration
- **Infrastructure Layer**: External concerns (DB, APIs, etc.)
- **Presentation Layer**: User interface (REST API, CLI, etc.)

## Generic E-Commerce Example

### Domain Layer

#### Entities
```python
# domain/entities/customer.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from domain.value_objects import Email, Address

@dataclass(frozen=True)
class Customer:
    """Customer aggregate root"""
    id: UUID
    email: Email
    name: str
    address: Optional[Address]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    def deactivate(self) -> 'Customer':
        """Business rule: deactivate customer"""
        return Customer(
            id=self.id,
            email=self.email,
            name=self.name,
            address=self.address,
            is_active=False,
            created_at=self.created_at,
            updated_at=datetime.utcnow()
        )
```

```python
# domain/entities/order.py
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List
from uuid import UUID

class OrderStatus(Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"

@dataclass(frozen=True)
class OrderItem:
    """Order line item"""
    product_id: UUID
    quantity: int
    unit_price: Decimal
    
    @property
    def total_price(self) -> Decimal:
        return self.quantity * self.unit_price

@dataclass(frozen=True)
class Order:
    """Order aggregate"""
    id: UUID
    customer_id: UUID
    items: List[OrderItem]
    status: OrderStatus
    created_at: datetime
    updated_at: datetime
    
    @property
    def total_amount(self) -> Decimal:
        """Calculate total order amount"""
        return sum(item.total_price for item in self.items)
    
    def can_be_cancelled(self) -> bool:
        """Business rule: only pending/confirmed orders can be cancelled"""
        return self.status in [OrderStatus.PENDING, OrderStatus.CONFIRMED]
    
    def cancel(self) -> 'Order':
        """Cancel order if allowed"""
        if not self.can_be_cancelled():
            raise ValueError(f"Order in {self.status} status cannot be cancelled")
        
        return Order(
            id=self.id,
            customer_id=self.customer_id,
            items=self.items,
            status=OrderStatus.CANCELLED,
            created_at=self.created_at,
            updated_at=datetime.utcnow()
        )
```

#### Value Objects
```python
# domain/value_objects/email.py
from dataclasses import dataclass
import re

@dataclass(frozen=True)
class Email:
    """Email value object with validation"""
    value: str
    
    def __post_init__(self):
        if not self._is_valid_email(self.value):
            raise ValueError(f"Invalid email format: {self.value}")
    
    @staticmethod
    def _is_valid_email(email: str) -> bool:
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

# domain/value_objects/address.py
@dataclass(frozen=True)
class Address:
    """Address value object"""
    street: str
    city: str
    state: str
    zip_code: str
    country: str
    
    def __post_init__(self):
        if not all([self.street, self.city, self.state, self.zip_code, self.country]):
            raise ValueError("All address fields are required")
```

#### Repository Interfaces
```python
# domain/repositories/customer_repository.py
from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from src.domain.entities.customer import Customer

class CustomerRepository(ABC):
    """Repository interface for Customer aggregate"""
    
    @abstractmethod
    async def find_by_id(self, customer_id: UUID) -> Optional[Customer]:
        """Find customer by ID"""
        pass
    
    @abstractmethod
    async def find_by_email(self, email: str) -> Optional[Customer]:
        """Find customer by email"""
        pass
    
    @abstractmethod
    async def save(self, customer: Customer) -> Customer:
        """Save customer (create or update)"""
        pass
    
    @abstractmethod
    async def list_all(self) -> List[Customer]:
        """List all customers"""
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
        """Search customers with optional filters"""
        pass
```

```python
# domain/repositories/order_repository.py
from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from src.domain.entities.order import Order

class OrderRepository(ABC):
    """Repository interface for Order aggregate"""
    
    @abstractmethod
    async def find_by_id(self, order_id: UUID) -> Optional[Order]:
        """Find order by ID"""
        pass
    
    @abstractmethod
    async def save(self, order: Order) -> Order:
        """Save order"""
        pass
    
    @abstractmethod
    async def find_by_customer(self, customer_id: UUID) -> List[Order]:
        """Find all orders for a customer"""
        pass
    
    @abstractmethod
    async def list_all(self) -> List[Order]:
        """List all orders"""
        pass
```

#### Domain Services
```python
# domain/services/pricing_service.py
from decimal import Decimal
from typing import List
from uuid import UUID

from domain.entities.order import OrderItem
from domain.repositories.product_repository import ProductRepository

class PricingService:
    """Domain service for pricing calculations"""
    
    def __init__(self, product_repository: ProductRepository):
        self._product_repo = product_repository
    
    async def calculate_order_total(self, items: List[OrderItem]) -> Decimal:
        """Calculate total with current prices and discounts"""
        total = Decimal('0')
        
        for item in items:
            product = await self._product_repo.find_by_id(item.product_id)
            if not product:
                raise ValueError(f"Product {item.product_id} not found")
            
            # Apply business rules for pricing
            item_total = product.price * item.quantity
            
            # Apply bulk discount if applicable
            if item.quantity >= 10:
                item_total *= Decimal('0.9')  # 10% discount
            
            total += item_total
        
        return total
```

### Application Layer

The application layer orchestrates use cases and implements the CQRS pattern by separating Commands (write operations) from Queries (read operations).

#### Directory Structure
```
application/
├── use_cases/
│   ├── commands/          # Write operations
│   │   ├── create_customer.py
│   │   ├── create_order.py
│   │   └── update_customer.py
│   └── queries/           # Read operations
│       ├── get_customer_orders.py
│       ├── search_customers.py
│       └── list_orders.py
```

#### Commands (Write Operations)
```python
# application/use_cases/commands/create_order.py
from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from src.domain.entities.order import Order
from src.domain.repositories.customer_repository import CustomerRepository
from src.domain.repositories.order_repository import OrderRepository
from src.shared_kernel import CustomerId, OrderId, Money

@dataclass
class CreateOrderCommand:
    """Command for creating an order"""
    customer_id: UUID
    total_amount: Decimal
    currency: str = "USD"
    catalog: dict = None

class CreateOrderUseCase:
    """Use case for creating a new order"""
    
    def __init__(
        self,
        order_repository: OrderRepository,
        customer_repository: CustomerRepository
    ):
        self._order_repo = order_repository
        self._customer_repo = customer_repository
    
    async def execute(self, command: CreateOrderCommand) -> Order:
        # Verify customer exists and is active
        customer = await self._customer_repo.find_by_id(command.customer_id)
        if not customer:
            raise ValueError("Customer not found")
        if not customer.is_active:
            raise ValueError("Cannot create order for inactive customer")
        
        # Create order using factory method
        order = Order.create(
            order_id=OrderId(uuid4()),
            customer_id=CustomerId(command.customer_id),
            total_amount=Money(command.total_amount, command.currency),
            catalog=command.catalog or {}
        )
        
        # Save and return
        return await self._order_repo.save(order)
```

```python
# application/use_cases/commands/create_customer.py
from dataclasses import dataclass
from typing import Dict, Any

from src.domain.entities.customer import Customer
from src.domain.repositories.customer_repository import CustomerRepository
from src.shared_kernel import CustomerId, Email

@dataclass
class CreateCustomerCommand:
    """Command for creating a customer"""
    name: str
    email: str
    preferences: Dict[str, Any] = None

class CreateCustomerUseCase:
    """Use case for creating a new customer"""
    
    def __init__(self, customer_repository: CustomerRepository):
        self._customer_repo = customer_repository
    
    async def execute(self, command: CreateCustomerCommand) -> Customer:
        # Check if customer already exists
        existing = await self._customer_repo.find_by_email(command.email)
        if existing:
            raise ValueError(f"Customer with email {command.email} already exists")
        
        # Create customer using factory method
        customer = Customer.create(
            customer_id=CustomerId(uuid4()),
            name=command.name,
            email=Email(command.email),
            preferences=command.preferences or {}
        )
        
        # Save and return
        return await self._customer_repo.save(customer)
```

#### Queries (Read Operations)
```python
# application/use_cases/queries/get_customer_orders.py
from typing import List
from uuid import UUID

from src.domain.entities.order import Order
from src.domain.repositories.order_repository import OrderRepository

class GetCustomerOrdersQuery:
    """Query to retrieve all orders for a specific customer"""
    
    def __init__(self, order_repository: OrderRepository):
        self._order_repository = order_repository
    
    async def execute(self, customer_id: UUID) -> List[Order]:
        """Execute the query to get customer orders"""
        if not customer_id:
            raise ValueError("Customer ID cannot be empty")
        
        return await self._order_repository.find_by_customer(customer_id)
```

```python
# application/use_cases/queries/search_customers.py
from dataclasses import dataclass
from typing import List, Optional

from src.domain.entities.customer import Customer
from src.domain.repositories.customer_repository import CustomerRepository

@dataclass(frozen=True)
class SearchCustomersQuery:
    """Query parameters for searching customers"""
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
    """Use case for searching customers with filters"""
    
    def __init__(self, customer_repository: CustomerRepository):
        self._customer_repository = customer_repository
    
    async def execute(self, query: SearchCustomersQuery) -> List[Customer]:
        """Execute the search query"""
        return await self._customer_repository.search(
            name_contains=query.name_contains,
            email_contains=query.email_contains,
            is_active=query.is_active,
            limit=query.limit,
            offset=query.offset
        )
```

```python
# application/use_cases/cancel_order.py
from dataclasses import dataclass
from uuid import UUID

from domain.repositories.order_repository import OrderRepository

@dataclass
class CancelOrderCommand:
    """Command for cancelling an order"""
    order_id: UUID
    reason: str

class CancelOrderUseCase:
    """Use case for cancelling an order"""
    
    def __init__(self, order_repository: OrderRepository):
        self._order_repo = order_repository
    
    async def execute(self, command: CancelOrderCommand) -> Order:
        # Get order
        order = await self._order_repo.find_by_id(command.order_id)
        if not order:
            raise ValueError("Order not found")
        
        # Apply business rule through domain entity
        cancelled_order = order.cancel()
        
        # Save and return
        return await self._order_repo.save(cancelled_order)
```

### Infrastructure Layer

#### PostgreSQL Implementation
```python
# infrastructure/database/models.py
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Numeric, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class CustomerModel(Base):
    __tablename__ = "customers"
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    
    # JSONB for flexible data
    address = Column(JSONB)
    preferences = Column(JSONB, default={})
    
    # Relationships
    orders = relationship("OrderModel", back_populates="customer")

class OrderModel(Base):
    __tablename__ = "orders"
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"))
    status = Column(String(20), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    
    # JSONB for flexible order catalog
    catalog = Column(JSONB, default={})
    
    # Relationships
    customer = relationship("CustomerModel", back_populates="orders")
    items = relationship("OrderItemModel", back_populates="order")

class OrderItemModel(Base):
    __tablename__ = "order_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"))
    product_id = Column(UUID(as_uuid=True), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    
    # Relationships
    order = relationship("OrderModel", back_populates="items")
```

#### Repository Implementation
```python
# infrastructure/database/repositories/customer_repository_impl.py
from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from domain.entities.customer import Customer
from domain.repositories.customer_repository import CustomerRepository
from domain.value_objects import Email, Address
from infrastructure.database.models import CustomerModel

class PostgresCustomerRepository(CustomerRepository):
    """PostgreSQL implementation of CustomerRepository"""
    
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def find_by_id(self, customer_id: UUID) -> Optional[Customer]:
        stmt = select(CustomerModel).where(CustomerModel.id == customer_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            return None
        
        return self._model_to_entity(model)
    
    async def find_by_email(self, email: Email) -> Optional[Customer]:
        stmt = select(CustomerModel).where(CustomerModel.email == email.value)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            return None
        
        return self._model_to_entity(model)
    
    async def save(self, customer: Customer) -> Customer:
        model = self._entity_to_model(customer)
        self._session.add(model)
        await self._session.commit()
        return customer
    
    def _model_to_entity(self, model: CustomerModel) -> Customer:
        """Convert database model to domain entity"""
        address = None
        if model.address:
            address = Address(**model.address)
        
        return Customer(
            id=model.id,
            email=Email(model.email),
            name=model.name,
            address=address,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
    
    def _entity_to_model(self, entity: Customer) -> CustomerModel:
        """Convert domain entity to database model"""
        address_data = None
        if entity.address:
            address_data = {
                "street": entity.address.street,
                "city": entity.address.city,
                "state": entity.address.state,
                "zip_code": entity.address.zip_code,
                "country": entity.address.country
            }
        
        return CustomerModel(
            id=entity.id,
            email=entity.email.value,
            name=entity.name,
            address=address_data,
            is_active=entity.is_active,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )
```

### Presentation Layer

#### FastAPI Application
```python
# presentation/api/v1/orders.py
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status

from application.use_cases.create_order import CreateOrderUseCase, CreateOrderCommand
from presentation.schemas.order_schemas import CreateOrderRequest, OrderResponse
from presentation.dependencies import get_create_order_use_case

router = APIRouter(prefix="/api/v1/orders", tags=["orders"])

@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    request: CreateOrderRequest,
    use_case: CreateOrderUseCase = Depends(get_create_order_use_case)
) -> OrderResponse:
    """Create a new order"""
    try:
        command = CreateOrderCommand(
            customer_id=request.customer_id,
            items=request.items
        )
        order = await use_case.execute(command)
        
        return OrderResponse.from_domain(order)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
```

#### Pydantic Schemas
```python
# presentation/schemas/order_schemas.py
from datetime import datetime
from decimal import Decimal
from typing import List
from uuid import UUID

from pydantic import BaseModel, Field, validator

class OrderItemRequest(BaseModel):
    product_id: UUID
    quantity: int = Field(..., gt=0)

class CreateOrderRequest(BaseModel):
    customer_id: UUID
    items: List[OrderItemRequest] = Field(..., min_items=1)
    
    @validator('items')
    def validate_unique_products(cls, v):
        product_ids = [item.product_id for item in v]
        if len(product_ids) != len(set(product_ids)):
            raise ValueError("Duplicate products in order")
        return v

class OrderItemResponse(BaseModel):
    product_id: UUID
    quantity: int
    unit_price: Decimal
    total_price: Decimal

class OrderResponse(BaseModel):
    id: UUID
    customer_id: UUID
    items: List[OrderItemResponse]
    status: str
    total_amount: Decimal
    created_at: datetime
    updated_at: datetime
    
    @classmethod
    def from_domain(cls, order: Order) -> 'OrderResponse':
        """Convert domain entity to response model"""
        items = [
            OrderItemResponse(
                product_id=item.product_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
                total_price=item.total_price
            )
            for item in order.items
        ]
        
        return cls(
            id=order.id,
            customer_id=order.customer_id,
            items=items,
            status=order.status.value,
            total_amount=order.total_amount,
            created_at=order.created_at,
            updated_at=order.updated_at
        )
```

### Dependency Injection Configuration
```python
# presentation/dependencies.py
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from fastapi import Depends

from domain.repositories.customer_repository import CustomerRepository
from domain.repositories.order_repository import OrderRepository
from domain.services.pricing_service import PricingService
from infrastructure.database.repositories.customer_repository_impl import PostgresCustomerRepository
from infrastructure.database.repositories.order_repository_impl import PostgresOrderRepository
from application.use_cases.create_order import CreateOrderUseCase

# Database configuration
DATABASE_URL = "postgresql+asyncpg://user:password@localhost/ecommerce_db"
engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

# Database session
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

# Repositories
async def get_customer_repository(
    session: AsyncSession = Depends(get_db_session)
) -> CustomerRepository:
    return PostgresCustomerRepository(session)

async def get_order_repository(
    session: AsyncSession = Depends(get_db_session)
) -> OrderRepository:
    return PostgresOrderRepository(session)

# Domain services
async def get_pricing_service(
    product_repo: ProductRepository = Depends(get_product_repository)
) -> PricingService:
    return PricingService(product_repo)

# Use cases
async def get_create_order_use_case(
    customer_repo: CustomerRepository = Depends(get_customer_repository),
    order_repo: OrderRepository = Depends(get_order_repository),
    pricing_service: PricingService = Depends(get_pricing_service)
) -> CreateOrderUseCase:
    return CreateOrderUseCase(customer_repo, order_repo, pricing_service)
```

## Testing Patterns

### Unit Tests - Domain Layer
```python
# tests/domain/entities/test_order.py
import pytest
from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from domain.entities.order import Order, OrderItem, OrderStatus

def test_order_total_calculation():
    """Test order total amount calculation"""
    items = [
        OrderItem(
            product_id=uuid4(),
            quantity=2,
            unit_price=Decimal('10.00')
        ),
        OrderItem(
            product_id=uuid4(),
            quantity=1,
            unit_price=Decimal('25.00')
        )
    ]
    
    order = Order(
        id=uuid4(),
        customer_id=uuid4(),
        items=items,
        status=OrderStatus.PENDING,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    assert order.total_amount == Decimal('45.00')

def test_order_cancellation_rules():
    """Test order cancellation business rules"""
    order = Order(
        id=uuid4(),
        customer_id=uuid4(),
        items=[],
        status=OrderStatus.SHIPPED,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    # Cannot cancel shipped order
    assert not order.can_be_cancelled()
    
    with pytest.raises(ValueError, match="cannot be cancelled"):
        order.cancel()
```

### Integration Tests - Repository Layer
```python
# tests/infrastructure/repositories/test_customer_repository.py
import pytest
from uuid import uuid4

from domain.entities.customer import Customer
from domain.value_objects import Email
from infrastructure.database.repositories.customer_repository_impl import PostgresCustomerRepository

@pytest.mark.asyncio
async def test_customer_repository_save_and_find(db_session):
    """Test saving and retrieving customer"""
    repo = PostgresCustomerRepository(db_session)
    
    # Create customer
    customer = Customer(
        id=uuid4(),
        email=Email("test@example.com"),
        name="Test Customer",
        address=None,
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    # Save
    saved = await repo.save(customer)
    assert saved.id == customer.id
    
    # Find by ID
    found = await repo.find_by_id(customer.id)
    assert found is not None
    assert found.email.value == "test@example.com"
    
    # Find by email
    found_by_email = await repo.find_by_email(Email("test@example.com"))
    assert found_by_email is not None
    assert found_by_email.id == customer.id
```

## Key Patterns Summary

### 1. CQRS (Command Query Responsibility Segregation)
Separate write operations (Commands) from read operations (Queries):
- **Commands**: Modify state, return entities, live in `commands/` folder
- **Queries**: Read data only, optimized for specific views, live in `queries/` folder
- **Benefits**: Optimized read/write models, clearer intent, easier scaling

### 2. Immutable Domain Entities
Use frozen dataclasses for entities to ensure immutability and prevent accidental mutations.

### 3. Repository Pattern
Abstract data access behind interfaces for flexibility and testability.

### 4. Use Case Pattern
Each use case is a single class with one public method (`execute`).

### 5. Value Objects with Validation
Encapsulate validation and business logic for values like Email, Money, etc.

### 6. Factory Methods
Use static factory methods (`create()`) for complex entity construction with domain events.

### 7. Dependency Injection
Use constructor injection for loose coupling and testability.

### 8. Pure Domain Logic
Keep business rules in the domain layer with no external dependencies.

## Benefits

1. **Testability**: Domain logic can be tested without infrastructure
2. **Flexibility**: Easy to swap implementations (e.g., PostgreSQL to DynamoDB)
3. **Maintainability**: Clear separation of concerns
4. **Type Safety**: Full type hints throughout the codebase
5. **Business Focus**: Domain model reflects business language

---
*Document Version: 1.1*
*Last Updated: 2025-08-03*
*Status: Architecture Patterns Guide - Updated with CQRS Implementation*