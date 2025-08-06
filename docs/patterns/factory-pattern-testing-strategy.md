# Factory Pattern and Testing Strategy

## Factory Pattern Implementation

### Overview
The Factory pattern provides a clean way to create complex domain objects while encapsulating creation logic, validation, and initialization rules.

### Benefits
1. **Centralized Creation Logic**: All object creation rules in one place
2. **Type Safety**: Return specific types based on input parameters
3. **Testability**: Easy to mock and test creation logic
4. **Flexibility**: Switch implementations without changing client code

### Factory Implementations

#### Customer Factory
```python
# domain/factories/customer_factory.py
from typing import Dict, Any, Optional
from uuid import uuid4
from datetime import datetime

from domain.entities.customer import Customer
from domain.value_objects.email import Email

class CustomerFactory:
    """Factory for creating Customer instances with validation"""
    
    @staticmethod
    def create(
        name: str,
        email: str,
        preferences: Optional[Dict[str, Any]] = None
    ) -> Customer:
        """Create a new customer with validation"""
        # Validate and create email value object
        email_vo = Email(email)
        
        # Set default preferences if not provided
        if preferences is None:
            preferences = {
                "newsletter": True,
                "notifications": {"email": True, "sms": False}
            }
        
        return Customer(
            id=uuid4(),
            name=name,
            email=email_vo,
            is_active=True,
            preferences=preferences,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    @staticmethod
    def create_from_dict(data: Dict[str, Any]) -> Customer:
        """Create customer from dictionary (e.g., API request)"""
        return CustomerFactory.create(
            name=data["name"],
            email=data["email"],
            preferences=data.get("preferences")
        )
```

#### Order Factory
```python
# domain/factories/order_factory.py
from typing import List, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime
from decimal import Decimal

from domain.entities.order import Order, OrderItem, OrderStatus
from domain.entities.customer import Customer

class OrderFactory:
    """Factory for creating Order instances"""
    
    @staticmethod
    def create(
        customer: Customer,
        items: List[Dict[str, Any]]
    ) -> Order:
        """Create a new order with validation"""
        if not customer.is_active:
            raise ValueError("Cannot create order for inactive customer")
        
        if not items:
            raise ValueError("Order must contain at least one item")
        
        # Create order items
        order_items = []
        total_amount = Decimal("0.00")
        
        for item_data in items:
            order_item = OrderItem(
                product_id=item_data["product_id"],
                product_name=item_data["product_name"],
                quantity=item_data["quantity"],
                unit_price=Decimal(str(item_data["unit_price"])),
                total_price=Decimal(str(item_data["unit_price"])) * item_data["quantity"]
            )
            order_items.append(order_item)
            total_amount += order_item.total_price
        
        return Order(
            id=uuid4(),
            customer_id=customer.id,
            items=order_items,
            total_amount=total_amount,
            status=OrderStatus.PENDING,
            catalog={"source": "web", "ip_address": "127.0.0.1"},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
```

### Test Data Builders

```python
# tests/builders/customer_builder.py
from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime

from domain.entities.customer import Customer
from domain.value_objects.email import Email

class CustomerBuilder:
    """Builder for creating test Customer instances"""
    
    def __init__(self):
        self._id = uuid4()
        self._name = "Test Customer"
        self._email = "test@example.com"
        self._is_active = True
        self._preferences = {"newsletter": True}
        self._created_at = datetime.utcnow()
    
    def with_name(self, name: str) -> 'CustomerBuilder':
        self._name = name
        return self
    
    def with_email(self, email: str) -> 'CustomerBuilder':
        self._email = email
        return self
    
    def inactive(self) -> 'CustomerBuilder':
        self._is_active = False
        return self
    
    def with_preferences(self, preferences: Dict[str, Any]) -> 'CustomerBuilder':
        self._preferences = preferences
        return self
    
    def build(self) -> Customer:
        return Customer(
            id=self._id,
            name=self._name,
            email=Email(self._email),
            is_active=self._is_active,
            preferences=self._preferences,
            created_at=self._created_at,
            updated_at=self._created_at
        )
```

## Testing Strategy

### Test Pyramid

```
         /\
        /E2E\        (5% - Critical user journeys)
       /------\
      /  API   \     (15% - Contract & integration)
     /----------\
    / Integration \  (20% - Repository tests)
   /--------------\
  /     Unit       \ (60% - Business logic)
 /------------------\
```

### 1. Unit Tests

#### Domain Entity Tests
```python
# tests/unit/domain/test_customer.py
import pytest
from uuid import uuid4

from domain.entities.customer import Customer
from domain.value_objects.email import Email

class TestCustomer:
    """Unit tests for Customer entity"""
    
    def test_customer_creation(self):
        """Test creating a customer"""
        # Arrange
        customer_id = uuid4()
        email = Email("test@example.com")
        
        # Act
        customer = Customer(
            id=customer_id,
            name="John Doe",
            email=email,
            is_active=True
        )
        
        # Assert
        assert customer.id == customer_id
        assert customer.name == "John Doe"
        assert customer.email.value == "test@example.com"
        assert customer.is_active is True
    
    def test_customer_deactivate(self):
        """Test deactivating a customer"""
        # Arrange
        customer = Customer(
            id=uuid4(),
            name="Jane Doe",
            email=Email("jane@example.com"),
            is_active=True
        )
        
        # Act
        customer.deactivate()
        
        # Assert
        assert customer.is_active is False
```

#### Factory Tests
```python
# tests/unit/domain/factories/test_customer_factory.py
import pytest
from domain.factories.customer_factory import CustomerFactory

class TestCustomerFactory:
    """Unit tests for CustomerFactory"""
    
    def test_create_customer_with_defaults(self):
        """Test creating customer with default preferences"""
        # Act
        customer = CustomerFactory.create(
            name="John Doe",
            email="john@example.com"
        )
        
        # Assert
        assert customer.name == "John Doe"
        assert customer.email.value == "john@example.com"
        assert customer.is_active is True
        assert customer.preferences["newsletter"] is True
    
    def test_create_customer_with_custom_preferences(self):
        """Test creating customer with custom preferences"""
        # Arrange
        preferences = {
            "newsletter": False,
            "language": "es"
        }
        
        # Act
        customer = CustomerFactory.create(
            name="Maria Garcia",
            email="maria@example.com",
            preferences=preferences
        )
        
        # Assert
        assert customer.preferences["newsletter"] is False
        assert customer.preferences["language"] == "es"
```

### 2. Integration Tests

#### Repository Tests
```python
# tests/integration/test_customer_repository.py
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.customer import Customer
from domain.value_objects.email import Email
from infrastructure.repositories.customer_repository import SQLCustomerRepository

@pytest.mark.asyncio
class TestCustomerRepository:
    """Integration tests for Customer repository"""
    
    async def test_save_and_retrieve_customer(self, db_session: AsyncSession):
        """Test saving and retrieving customer with JSONB preferences"""
        # Arrange
        repository = SQLCustomerRepository(db_session)
        customer = Customer(
            name="Test User",
            email=Email("test@example.com"),
            is_active=True,
            preferences={"theme": "dark", "language": "en"}
        )
        
        # Act
        saved = await repository.save(customer)
        retrieved = await repository.find_by_email("test@example.com")
        
        # Assert
        assert retrieved is not None
        assert retrieved.id == saved.id
        assert retrieved.preferences["theme"] == "dark"
```

### 3. API Tests

```python
# tests/api/test_customer_endpoints.py
import pytest
from fastapi.testclient import TestClient

class TestCustomerAPI:
    """API contract tests"""
    
    def test_create_customer_success(self, client: TestClient):
        """Test creating customer via API"""
        # Arrange
        customer_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "preferences": {"newsletter": True}
        }
        
        # Act
        response = client.post("/api/v1/customers", json=customer_data)
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "John Doe"
        assert data["email"] == "john@example.com"
        assert "id" in data
```


### 4. End-to-End Tests

#### Critical User Journeys
```python
# tests/e2e/test_order_lifecycle.py
import pytest
from decimal import Decimal
from playwright.async_api import async_playwright

@pytest.mark.e2e
class TestOrderLifecycle:
    """End-to-end tests for complete order lifecycle"""
    
    @pytest.mark.asyncio
    async def test_create_customer_and_place_order(self, api_base_url, test_data_factory):
        """Test complete flow: create customer → place order → process payment"""
        async with async_playwright() as p:
            # Use API client for setup
            api_client = ApiTestClient(api_base_url)
            
            # Step 1: Create customer
            customer_data = test_data_factory.create_customer_data(
                name="E2E Test User",
                email="e2e@example.com"
            )
            customer_response = await api_client.create_customer(customer_data)
            customer_id = customer_response["id"]
            
            # Step 2: Create order
            order_data = test_data_factory.create_order_data(
                customer_id=customer_id,
                items=[
                    {"product_id": "PROD-001", "quantity": 2, "unit_price": "29.99"},
                    {"product_id": "PROD-002", "quantity": 1, "unit_price": "49.99"}
                ]
            )
            order_response = await api_client.create_order(order_data)
            order_id = order_response["id"]
            
            # Step 3: Process payment
            payment_response = await api_client.process_payment(
                order_id=order_id,
                payment_method="credit_card",
                amount=Decimal("109.97")
            )
            
            # Assert order completed
            assert payment_response["status"] == "completed"
            assert payment_response["order_status"] == "PAID"
            assert payment_response["total_amount"] == "109.97"
    
    @pytest.mark.asyncio
    async def test_customer_order_history(self, api_base_url):
        """Test retrieving customer order history"""
        # Test implementation
        pass
```

### 5. Test Data Builders

#### Order Builder
```python
# tests/builders/order_builder.py
from datetime import datetime
from typing import List
from uuid import UUID, uuid4
from decimal import Decimal

from domain.entities.order import Order, OrderItem, OrderStatus
from tests.builders.customer_builder import CustomerBuilder

class OrderBuilder:
    """Builder for creating test Order instances"""
    
    def __init__(self):
        self._id = uuid4()
        self._customer_id = uuid4()
        self._items = []
        self._total_amount = Decimal("0.00")
        self._status = OrderStatus.PENDING
        self._catalog = {"source": "test"}
        self._created_at = datetime.utcnow()
    
    def for_customer(self, customer_id: UUID) -> 'OrderBuilder':
        self._customer_id = customer_id
        return self
    
    def with_item(
        self, 
        product_id: str, 
        product_name: str,
        quantity: int,
        unit_price: Decimal
    ) -> 'OrderBuilder':
        """Add an item to the order"""
        item = OrderItem(
            product_id=product_id,
            product_name=product_name,
            quantity=quantity,
            unit_price=unit_price,
            total_price=unit_price * quantity
        )
        self._items.append(item)
        self._total_amount += item.total_price
        return self
    
    def with_status(self, status: OrderStatus) -> 'OrderBuilder':
        self._status = status
        return self
    
    def build(self) -> Order:
        """Build the Order instance"""
        return Order(
            id=self._id,
            customer_id=self._customer_id,
            items=self._items,
            total_amount=self._total_amount,
            status=self._status,
            catalog=self._catalog,
            created_at=self._created_at,
            updated_at=self._created_at
        )
```

#### Test Fixtures
```python
# tests/fixtures/e_commerce_fixtures.py
import pytest
from datetime import datetime
from typing import Dict, Any
from decimal import Decimal

from tests.builders.customer_builder import CustomerBuilder
from tests.builders.order_builder import OrderBuilder

@pytest.fixture
def test_customer():
    """Create test customer"""
    return (
        CustomerBuilder()
        .with_name("Test Customer")
        .with_email("test@example.com")
        .with_preferences({"newsletter": True, "theme": "light"})
        .build()
    )

@pytest.fixture
def test_order(test_customer):
    """Create test order with items"""
    return (
        OrderBuilder()
        .for_customer(test_customer.id)
        .with_item("PROD-001", "Widget", 2, Decimal("19.99"))
        .with_item("PROD-002", "Gadget", 1, Decimal("49.99"))
        .build()
    )

@pytest.fixture
def order_test_data():
    """Common test data for orders"""
    return {
        'products': [
            {'id': 'PROD-001', 'name': 'Widget', 'price': Decimal('19.99')},
            {'id': 'PROD-002', 'name': 'Gadget', 'price': Decimal('49.99')},
            {'id': 'PROD-003', 'name': 'Doohickey', 'price': Decimal('9.99')}
        ],
        'customers': [
            {'name': 'Alice Johnson', 'email': 'alice@example.com'},
            {'name': 'Bob Smith', 'email': 'bob@example.com'}
        ]
    }
```

### Testing Best Practices

#### 1. Test Naming Convention
```python
def test_should_create_customer_when_valid_email_provided():
    """Use descriptive names following: test_should_[expected]_when_[condition]"""
    pass

def test_should_raise_error_when_inactive_customer_places_order():
    """Clear indication of expected behavior"""
    pass
```

#### 2. Arrange-Act-Assert Pattern
```python
def test_order_total_calculation():
    # Arrange - Set up test data
    customer = CustomerBuilder().with_name("TEST").build()
    order = OrderBuilder().for_customer(customer.id).build()
    
    # Act - Execute the behavior
    order.add_item("PROD-001", "Widget", 2, Decimal("19.99"))
    
    # Assert - Verify the outcome
    assert order.total_amount == Decimal("39.98")
    assert len(order.items) == 1
```

#### 3. Test Isolation
```python
@pytest.fixture(autouse=True)
async def cleanup_database(db_session):
    """Ensure each test has clean database state"""
    yield
    # Rollback any changes
    await db_session.rollback()
```

### Performance Testing

```python
# tests/performance/test_order_query_performance.py
import pytest
import time
from decimal import Decimal

@pytest.mark.performance
class TestOrderQueryPerformance:
    """Performance tests for order queries"""
    
    @pytest.mark.asyncio
    async def test_customer_order_history_performance(self, repository, large_dataset):
        """Test order history lookup performance with many orders"""
        # Create customer with 1000 orders
        customer = CustomerBuilder().with_name("PERF TEST").build()
        await repository.save(customer)
        
        for i in range(1000):
            order = (
                OrderBuilder()
                .for_customer(customer.id)
                .with_item(f"PROD-{i}", f"Product {i}", 1, Decimal("10.00"))
                .build()
            )
            await repository.save_order(order)
        
        # Measure lookup time
        start_time = time.time()
        for _ in range(100):
            orders = await repository.find_orders_by_customer(customer.id)
        
        elapsed = time.time() - start_time
        
        # Assert performance threshold
        assert elapsed < 2.0  # 100 lookups in under 2 seconds
```

## Database Mocking Strategy

### Overview
Different testing levels require different database strategies. The key principle is to mock at the appropriate abstraction level, not always at the database level.

### Testing Levels and Database Strategies

#### 1. Unit Tests - Mock Repository Interfaces
```python
# tests/unit/application/use_cases/test_create_customer.py
@pytest.mark.asyncio
async def test_create_customer_use_case():
    """Unit test with mocked repository - NO database needed"""
    # Mock the repository interface, not the database
    mock_customer_repo = AsyncMock(spec=CustomerRepository)
    mock_customer_repo.find_by_email.return_value = None
    mock_customer_repo.save.return_value = Customer(...)
    
    # Test use case with mocked repository
    use_case = CreateCustomerUseCase(mock_customer_repo)
    result = await use_case.execute(command)
    
    # Verify interactions
    mock_customer_repo.save.assert_called_once()
```

**Why**: Domain and application layers should not know about database implementation details.

#### 2. Repository Tests - Real Database in Docker
```python
# tests/integration/infrastructure/repositories/test_customer_repository.py
@pytest.fixture
async def db_session(postgres_container):
    """Use real PostgreSQL in Docker container"""
    engine = create_async_engine(
        f"postgresql+asyncpg://test:test@localhost:{postgres_container.port}/test"
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.catalog.create_all)
    
    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()

@pytest.mark.integration
async def test_repository_with_jsonb(db_session):
    """Test real PostgreSQL JSONB functionality"""
    repo = PostgresCustomerRepository(db_session)
    # Test actual JSONB queries for customer preferences
```

**Why**: Need to test actual PostgreSQL features like JSONB operators, indexes, and complex queries.

#### 3. Fast Repository Tests - SQLite In-Memory (Limited Use)
```python
# tests/integration/infrastructure/repositories/test_basic_crud.py
@pytest.fixture
async def sqlite_session():
    """Fast in-memory database for simple CRUD tests"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False}
    )
    
    # Note: JSONB columns will be TEXT in SQLite
    async with engine.begin() as conn:
        await conn.run_sync(Base.catalog.create_all)
    
    async with AsyncSessionLocal() as session:
        yield session

@pytest.mark.fast
async def test_basic_crud_operations(sqlite_session):
    """Test basic operations without PostgreSQL-specific features"""
    repo = ProductRepository(sqlite_session)
    # Only test basic CRUD, not JSONB operations
```

**Why**: 10x faster than PostgreSQL for basic CRUD tests, but limited functionality.

#### 4. API Tests - Mock Use Cases
```python
# tests/api/test_customer_endpoints.py
@pytest.fixture
def mock_create_customer_use_case():
    """Mock at the use case level for API tests"""
    mock = AsyncMock(spec=CreateCustomerUseCase)
    mock.execute.return_value = Customer(...)
    return mock

def test_create_customer_endpoint(client, mock_create_customer_use_case):
    """Test API contract without database"""
    with patch('presentation.dependencies.get_create_customer_use_case', 
               return_value=mock_create_customer_use_case):
        response = client.post("/api/v1/customers", json={...})
        assert response.status_code == 201
```

**Why**: API tests should focus on HTTP contract, not database operations.

#### 5. End-to-End Tests - Real Database
```python
# tests/e2e/test_complete_workflows.py
@pytest.mark.e2e
async def test_complete_order_workflow(real_api_url, postgres_db):
    """Full E2E test with real database"""
    # No mocking - test the complete system
    async with httpx.AsyncClient() as client:
        # Create customer
        response = await client.post(f"{real_api_url}/api/v1/customers", ...)
        # Create order
        response = await client.post(f"{real_api_url}/api/v1/orders", ...)
```

**Why**: E2E tests verify the complete system works together.

### Database Test Fixtures

#### PostgreSQL Test Container
```python
# tests/fixtures/database.py
import pytest
from testcontainers.postgres import PostgresContainer

@pytest.fixture(scope="session")
def postgres_container():
    """Shared PostgreSQL container for integration tests"""
    with PostgresContainer("postgres:15-alpine") as postgres:
        postgres.start()
        yield postgres

@pytest.fixture
async def db_url(postgres_container):
    """Database URL for test container"""
    return postgres_container.get_connection_url()
```

#### Transaction Rollback Pattern
```python
# tests/fixtures/session.py
@pytest.fixture
async def transactional_session(db_url):
    """Session that rolls back after each test"""
    engine = create_async_engine(db_url)
    connection = await engine.connect()
    transaction = await connection.begin()
    
    # Create session bound to the transaction
    async_session = async_sessionmaker(
        bind=connection,
        expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
    
    # Rollback the transaction
    await transaction.rollback()
    await connection.close()
```

### Mocking Decision Tree

```
Is it a unit test?
├─ YES → Mock repository interfaces (AsyncMock)
└─ NO → Is it testing repository implementation?
    ├─ YES → Use real PostgreSQL in Docker
    └─ NO → Is it testing API contracts?
        ├─ YES → Mock use cases
        └─ NO → Is it E2E test?
            ├─ YES → Use real database, no mocks
            └─ NO → Is JSONB functionality needed?
                ├─ YES → Use PostgreSQL
                └─ NO → Can use SQLite for speed
```

### Common Pitfalls to Avoid

1. **Don't Mock What You Don't Own**
   ```python
   # BAD - Mocking SQLAlchemy internals
   mock_query = Mock()
   mock_query.filter.return_value.first.return_value = ...
   
   # GOOD - Mock repository interface
   mock_repo = AsyncMock(spec=ProductRepository)
   mock_repo.find_by_id.return_value = Product(...)
   ```

2. **Don't Use SQLite for JSONB Tests**
   ```python
   # BAD - JSONB operators won't work in SQLite
   query = session.query(Model).filter(
       Model.catalog['key'] == 'value'  # PostgreSQL specific
   )
   
   # GOOD - Use PostgreSQL for JSONB tests
   # Or mock at repository level
   ```

3. **Don't Over-Mock**
   ```python
   # BAD - Mocking every single dependency
   mock_db = Mock()
   mock_session = Mock()
   mock_query = Mock()
   
   # GOOD - Mock at appropriate boundaries
   mock_repo = AsyncMock(spec=ProductRepository)
   ```

### JSONB Testing Strategy

JSONB fields require special consideration due to PostgreSQL-specific operators and functionality.

#### 1. Domain Logic Tests (Recommended for Most Cases)
```python
# Test JSONB data as Python dictionaries - no database needed
def test_customer_preferences_logic():
    """Test business logic on JSONB data as Python dicts"""
    customer = Customer(
        name="Test User",
        email=Email("test@example.com"),
        preferences={"theme": "dark", "language": "en", "newsletter": True}
    )
    
    # Test preference access
    assert customer.preferences["theme"] == "dark"
    assert customer.preferences.get("newsletter", False) is True
    
    # Test preference updates
    customer.update_preference("theme", "light")
    assert customer.preferences["theme"] == "light"
```

#### 2. Repository Mock Tests (Fast Unit Tests)
```python
# Mock repository methods that return JSONB data as dicts
@pytest.mark.asyncio
async def test_find_customers_by_preference():
    """Test use case with mocked repository - JSONB as dict"""
    mock_repo = AsyncMock(spec=CustomerRepository)
    mock_repo.find_by_preference.return_value = [
        Customer(
            id=uuid4(),
            name="Dark Theme User",
            email=Email("user@example.com"),
            preferences={"theme": "dark", "newsletter": True}
        )
    ]
    
    service = CustomerService(mock_repo)
    results = await service.get_customers_by_theme("dark")
    
    assert len(results) == 1
    assert results[0].preferences["theme"] == "dark"
```

#### 3. PostgreSQL Integration Tests (JSONB-Specific Operations)
```python
# Only test actual JSONB database operations when needed
@pytest.mark.integration
async def test_jsonb_query_operations(postgres_session):
    """Test PostgreSQL JSONB operators and indexes"""
    repo = PostgresCustomerRepository(postgres_session)
    
    # Create test data with JSONB
    customer = Customer(
        name="Test User",
        email=Email("test@example.com"),
        preferences={"theme": "dark", "language": "en", "catalog": {"source": "web"}}
    )
    await repo.save(customer)
    
    # Test JSONB operators
    # -> operator (get JSON object field)
    results = await repo.find_by_jsonb_path("preferences->>'theme'", "dark")
    assert len(results) == 1
    
    # @> operator (contains)
    results = await repo.find_containing_jsonb({"theme": "dark"})
    assert len(results) == 1
    
    # ? operator (key exists)
    results = await repo.find_with_jsonb_key("preferences", "theme")
    assert len(results) == 1
```

#### 4. JSONB Query Examples
```python
# infrastructure/database/repositories/customer_repository_impl.py
class PostgresCustomerRepository(CustomerRepository):
    
    async def find_by_jsonb_path(self, json_path: str, value: Any) -> List[Customer]:
        """Query using JSONB path operators"""
        stmt = select(CustomerModel).where(
            text(f"preferences->>'{json_path}' = :value")
        ).params(value=value)
        
        result = await self._session.execute(stmt)
        return [self._model_to_entity(model) for model in result.scalars()]
    
    async def find_containing_jsonb(self, contains: Dict[str, Any]) -> List[Customer]:
        """Query using JSONB @> (contains) operator"""
        stmt = select(CustomerModel).where(
            CustomerModel.preferences.op('@>')(contains)
        )
        
        result = await self._session.execute(stmt)
        return [self._model_to_entity(model) for model in result.scalars()]
```

### Performance Considerations

| Test Type | Database Strategy | Execution Time | Use When |
|-----------|------------------|----------------|----------|
| Unit | Mocked repos | <1ms | Business logic, JSONB as dicts |
| Integration (SQLite) | In-memory SQLite | ~10ms | Basic CRUD (no JSONB) |
| Integration (PG) | Docker PostgreSQL | ~100ms | JSONB operators, complex queries |
| E2E | Real PostgreSQL | ~500ms | Complete workflows |

### Recommended Testing Distribution

```python
# 80% - Fast unit tests with mocked repositories
def test_validation_business_logic():
    # Test JSONB data as Python dicts
    pass

# 15% - Integration tests for database-specific operations  
@pytest.mark.integration
async def test_jsonb_database_operations():
    # Test actual PostgreSQL JSONB features
    pass

# 5% - End-to-end tests
@pytest.mark.e2e
async def test_complete_validation_workflow():
    # Test full system integration
    pass
```

### Test Environment Configuration

```python
# tests/conftest.py
import os
import pytest

@pytest.fixture(scope="session")
def test_settings():
    """Override settings for testing"""
    return {
        "TESTING": True,
        "DATABASE_URL": os.getenv(
            "TEST_DATABASE_URL",
            "postgresql+asyncpg://test:test@localhost:5433/test_db"
        ),
        "REDIS_URL": "redis://localhost:6379/1",  # Use different DB
    }

# Mark slow tests
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as end-to-end test"
    )

# Run different test suites
# pytest -m "not integration and not e2e"  # Fast unit tests only
# pytest -m integration  # Integration tests only
# pytest  # All tests
```

## Testing Infrastructure

### Docker Test Environment
```yaml
# docker-compose.test.yml
version: '3.8'

services:
  test-db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: test_catalog
      POSTGRES_USER: test_user
      POSTGRES_PASSWORD: test_pass
    ports:
      - "5433:5432"
    
  test-runner:
    build:
      context: .
      dockerfile: Dockerfile.test
    environment:
      DATABASE_URL: postgresql://test_user:test_pass@test-db:5432/test_catalog
      TESTING: "true"
    volumes:
      - .:/app
    depends_on:
      - test-db
    command: pytest -v
```

### CI/CD Pipeline
```yaml
# .github/workflows/test.yml
name: Test Pipeline

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run unit tests
        run: |
          pytest tests/unit -v --cov=domain --cov-report=xml
  
  integration-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v3
      - name: Run integration tests
        run: |
          pytest tests/integration -v
  
  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run E2E tests
        run: |
          docker-compose -f docker-compose.test.yml up --exit-code-from test-runner
```

## Summary

### Factory Pattern Benefits
1. **Encapsulation**: Complex creation logic in one place
2. **Validation**: Centralized validation during object creation
3. **Flexibility**: Easy to add new types without changing client code
4. **Testing**: Factories can be mocked for isolated testing

### Testing Strategy Benefits
1. **Confidence**: Comprehensive coverage from unit to E2E
2. **Fast Feedback**: Most tests run quickly (unit/integration)
3. **Real-World Validation**: E2E tests verify actual user workflows
4. **Maintainability**: Test builders reduce duplication

---
*Document Version: 1.0*
*Last Updated: 2025-08-01*
*Status: Testing Strategy Guide*