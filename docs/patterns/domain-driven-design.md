# Domain-Driven Design (DDD) Patterns

## Overview

This document outlines the Domain-Driven Design patterns used in our Clean Architecture implementation, with concrete examples from our codebase and guidance for future development.

## Core DDD Concepts

### 1. Entities

**Definition**: Objects with a unique identity that persists through state changes.

**Current Implementation**:
```python
@dataclass(frozen=True)
class Customer:
    id: UUID              # Identity
    name: str            
    email: str           
    is_active: bool      
    preferences: dict[str, Any]
    created_at: datetime
    updated_at: datetime
```

**Characteristics**:
- Has unique identity (`id`)
- Identity remains constant through updates
- Equality based on identity, not attributes
- Can have mutable state (though we use immutable objects with update methods)

### 2. Value Objects

**Definition**: Objects without identity, defined entirely by their attributes. Immutable and self-validating.

**Currently Missing - Should Implement**:

```python
# Email Value Object
@dataclass(frozen=True)
class Email:
    value: str
    
    def __post_init__(self):
        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', self.value):
            raise ValueError(f"Invalid email format: {self.value}")
    
    def domain(self) -> str:
        return self.value.split('@')[1]
    
    def __str__(self) -> str:
        return self.value


# Money Value Object
@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str = "USD"
    
    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("Money cannot be negative")
        if self.currency not in ["USD", "EUR", "GBP"]:
            raise ValueError(f"Unsupported currency: {self.currency}")
    
    def add(self, other: 'Money') -> 'Money':
        if self.currency != other.currency:
            raise ValueError("Cannot add different currencies")
        return Money(self.amount + other.amount, self.currency)
```

**Value Object Guidelines**:
- Always immutable (use `frozen=True`)
- Self-validating in `__post_init__`
- Rich behavior through methods
- No database IDs
- Equality based on all attributes

### 3. Aggregates

**Definition**: A cluster of domain objects treated as a single unit with one aggregate root.

**Example Implementation**:

```python
# Order Aggregate Root
@dataclass
class Order:
    # Identity
    id: UUID
    
    # Reference to other aggregates by ID only
    customer_id: UUID
    
    # Owned entities within aggregate
    line_items: List[OrderLineItem]
    
    # Value objects
    shipping_address: Address
    billing_address: Address
    
    # Aggregate state
    status: OrderStatus
    
    # Business methods enforce invariants
    def add_line_item(self, product_id: UUID, quantity: int, price: Money) -> None:
        """All modifications go through aggregate root"""
        if self.status != OrderStatus.PENDING:
            raise ValueError("Cannot modify confirmed order")
        
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        
        line_item = OrderLineItem(
            product_id=product_id,
            quantity=quantity,
            unit_price=price
        )
        self.line_items.append(line_item)
    
    def confirm(self) -> None:
        """State transitions with business rules"""
        if not self.line_items:
            raise ValueError("Cannot confirm empty order")
        
        if self.total_amount().amount < Decimal("1.00"):
            raise ValueError("Order total too small")
            
        self.status = OrderStatus.CONFIRMED


# Entity within Order aggregate (not accessible directly)
@dataclass
class OrderLineItem:
    product_id: UUID
    quantity: int
    unit_price: Money
    
    def subtotal(self) -> Money:
        return Money(
            self.unit_price.amount * self.quantity,
            self.unit_price.currency
        )
```

**Aggregate Design Rules**:
1. **Single entry point**: Access only through aggregate root
2. **Consistency boundary**: All invariants enforced within aggregate
3. **Reference by ID**: Reference other aggregates by ID only
4. **Transactional consistency**: Save aggregate as a whole
5. **Small aggregates**: Keep aggregates small for performance

### 4. Domain Services

**Definition**: Operations that don't naturally belong to any entity or value object.

**Examples**:

```python
class PricingService:
    """Domain service for complex pricing calculations"""
    
    def calculate_order_total(
        self, 
        order: Order, 
        customer: Customer,
        applicable_discounts: List[Discount]
    ) -> Money:
        """Complex logic involving multiple aggregates"""
        
        subtotal = order.subtotal()
        
        # Apply customer tier discount
        tier_discount = self._get_tier_discount(customer.tier)
        subtotal = subtotal.multiply(Decimal(1) - tier_discount)
        
        # Apply promotional discounts
        for discount in applicable_discounts:
            if discount.is_applicable_to(order, customer):
                subtotal = discount.apply(subtotal)
        
        # Apply tax based on shipping address
        tax = self._calculate_tax(subtotal, order.shipping_address)
        
        return subtotal.add(tax)


class InventoryAllocationService:
    """Coordinates between multiple aggregates"""
    
    async def allocate_inventory(
        self,
        order: Order,
        warehouses: List[Warehouse]
    ) -> List[InventoryAllocation]:
        """Complex allocation logic across warehouses"""
        
        allocations = []
        for line_item in order.line_items:
            allocation = await self._find_best_allocation(
                line_item,
                warehouses,
                order.shipping_address
            )
            allocations.append(allocation)
        
        return allocations
```

**When to Use Domain Services**:
- Logic doesn't belong to a single entity
- Orchestrating between multiple aggregates
- Complex calculations involving multiple domain objects
- External service integration (wrap in domain service)

### 5. Repositories

**Definition**: Abstraction for aggregate persistence, maintaining the illusion of in-memory collection.

**Current Implementation**:
```python
class CustomerRepository(ABC):
    @abstractmethod
    async def find_by_id(self, customer_id: UUID) -> Optional[Customer]:
        pass
    
    @abstractmethod
    async def save(self, customer: Customer) -> Customer:
        pass
```

**Advanced Repository Patterns**:

```python
# Repository with Specification pattern
class CustomerRepository(ABC):
    @abstractmethod
    async def find_by_specification(
        self, 
        spec: Specification[Customer]
    ) -> List[Customer]:
        pass
    
    @abstractmethod
    async def count_by_specification(
        self, 
        spec: Specification[Customer]
    ) -> int:
        pass


# Specification pattern for complex queries
@dataclass
class CustomerSpecification(Specification[Customer]):
    min_total_orders: Optional[int] = None
    in_regions: Optional[List[str]] = None
    created_after: Optional[datetime] = None
    tier_in: Optional[List[CustomerTier]] = None
    
    def to_sql_where(self) -> str:
        """Convert to SQL for infrastructure layer"""
        conditions = []
        
        if self.min_total_orders:
            conditions.append(f"total_orders >= {self.min_total_orders}")
        
        if self.in_regions:
            regions = "','".join(self.in_regions)
            conditions.append(f"region IN ('{regions}')")
        
        # ... more conditions
        
        return " AND ".join(conditions)
```

### 6. Domain Events

**Definition**: Something significant that happened in the domain.

**Implementation**:

```python
@dataclass(frozen=True)
class DomainEvent:
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class CustomerEmailChanged(DomainEvent):
    customer_id: UUID
    old_email: Email
    new_email: Email
    reason: str


@dataclass(frozen=True)
class OrderShipped(DomainEvent):
    order_id: UUID
    tracking_number: str
    carrier: str
    estimated_delivery: datetime


# Aggregate with events
@dataclass
class Customer:
    # ... fields ...
    events: List[DomainEvent] = field(default_factory=list)
    
    def change_email(self, new_email: Email, reason: str) -> None:
        old_email = self.email
        self.email = new_email
        
        # Record what happened
        self.events.append(
            CustomerEmailChanged(
                customer_id=self.id,
                old_email=old_email,
                new_email=new_email,
                reason=reason
            )
        )
```

## Shared Kernel

**Definition**: Shared code between bounded contexts that multiple teams agree to maintain together.

### Should We Have a Shared Kernel?

**Yes, we should create a shared kernel for**:

1. **Common Value Objects**:
   ```python
   # src/shared_kernel/value_objects/
   - Email
   - Money
   - Address
   - PhoneNumber
   - DateRange
   ```

2. **Base Classes and Interfaces**:
   ```python
   # src/shared_kernel/base/
   - Entity
   - ValueObject
   - AggregateRoot
   - DomainEvent
   - Specification
   ```

3. **Common Domain Concepts**:
   ```python
   # src/shared_kernel/types/
   - CustomerId (typed UUID)
   - OrderId (typed UUID)
   - ProductId (typed UUID)
   ```

### Proposed Shared Kernel Structure

```
src/
├── shared_kernel/              # Shared between all bounded contexts
│   ├── __init__.py
│   ├── base/                   # Base classes
│   │   ├── __init__.py
│   │   ├── entity.py
│   │   ├── value_object.py
│   │   ├── aggregate_root.py
│   │   ├── domain_event.py
│   │   └── specification.py
│   ├── value_objects/          # Common value objects
│   │   ├── __init__.py
│   │   ├── email.py
│   │   ├── money.py
│   │   ├── address.py
│   │   └── identifiers.py
│   └── types/                  # Type definitions
│       ├── __init__.py
│       └── custom_types.py
├── domain/                     # Domain layer uses shared kernel
│   ├── entities/
│   └── repositories/
└── ...
```

## E-Commerce Specific Patterns

For our e-commerce platform, these DDD patterns are especially relevant:

### Value Objects for E-Commerce Platform

```python
@dataclass(frozen=True)
class Money:
    """Value object for monetary amounts"""
    amount: Decimal
    currency: str = "USD"
    
    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("Money amount cannot be negative")
        
        if len(self.currency) != 3:
            raise ValueError("Currency must be 3-letter code")
    
    def add(self, other: 'Money') -> 'Money':
        """Add two money amounts"""
        if self.currency != other.currency:
            raise ValueError("Cannot add different currencies")
        return Money(self.amount + other.amount, self.currency)


@dataclass(frozen=True)
class ProductCode:
    """Value object for product identification"""
    code: str
    
    def __post_init__(self):
        if not re.match(r'^[A-Z]{2,3}-\d{3,4}$', self.code):
            raise ValueError(f"Invalid product code format: {self.code}")
    
    def category(self) -> str:
        """Extract category from product code"""
        return self.code.split('-')[0]


@dataclass(frozen=True)
class Address:
    """Value object for shipping addresses"""
    street: str
    city: str
    state: str
    zip_code: str
    country: str = "US"
    
    def __post_init__(self):
        if not all([self.street, self.city, self.state, self.zip_code]):
            raise ValueError("All address fields are required")
    
    def full_address(self) -> str:
        return f"{self.street}, {self.city}, {self.state} {self.zip_code}"
```

### Aggregates for E-Commerce Platform

```python
@dataclass
class Order:
    """Aggregate root for customer orders"""
    id: UUID
    customer_id: UUID
    items: List[OrderItem]
    total: Money
    status: OrderStatus
    shipping_address: Optional[Address] = None
    
    def add_item(self, product_code: ProductCode, quantity: int, unit_price: Money) -> None:
        """Add item with validation"""
        if any(item.product_code == product_code for item in self.items):
            raise ValueError(f"Product {product_code.code} already in order")
        
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        
        order_item = OrderItem(
            product_code=product_code,
            quantity=quantity,
            unit_price=unit_price
        )
        self.items.append(order_item)
        self._recalculate_total()
    
    def ship_to(self, address: Address) -> None:
        """Set shipping address"""
        if self.status != OrderStatus.PENDING:
            raise ValueError("Cannot change address after confirmation")
        self.shipping_address = address
    
    def _recalculate_total(self) -> None:
        """Recalculate order total"""
        total_amount = sum(item.total_price().amount for item in self.items)
        self.total = Money(total_amount, "USD")
```

## Best Practices

1. **Start with Anemic Domain Model**: Begin simple, add behavior as you understand the domain better
2. **Ubiquitous Language**: Use domain terms consistently in code
3. **Bounded Contexts**: Keep contexts small and focused
4. **Aggregate Design**: Keep aggregates small, reference others by ID
5. **Value Objects Everywhere**: Replace primitives with value objects for type safety
6. **Domain Events**: Record significant business occurrences
7. **Test Domain Logic**: Unit test all business rules in domain objects

## References

- [Domain-Driven Design by Eric Evans](https://www.domainlanguage.com/ddd/)
- [Implementing Domain-Driven Design by Vaughn Vernon](https://www.amazon.com/Implementing-Domain-Driven-Design-Vaughn-Vernon/dp/0321834577)
- [Domain-Driven Design Distilled by Vaughn Vernon](https://www.amazon.com/Domain-Driven-Design-Distilled-Vaughn-Vernon/dp/0134434420)