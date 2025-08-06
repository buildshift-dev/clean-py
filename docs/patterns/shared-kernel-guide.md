# Shared Kernel Implementation Guide

## Overview

The Shared Kernel contains common domain concepts, value objects, and base classes that are shared across all bounded contexts in our application. This ensures consistency and reduces duplication while maintaining clear boundaries.

## When to Use Shared Kernel

### ✅ Include in Shared Kernel

1. **Truly Universal Concepts**
   - Email addresses
   - Money/Currency
   - Physical addresses
   - Phone numbers
   - Date ranges

2. **Base Technical Constructs**
   - Entity base class
   - Value object base class
   - Domain event base class
   - Specification pattern

3. **Cross-Cutting Domain Types**
   - Common identifiers (CustomerId, OrderId)
   - Audit fields (created_at, updated_at, created_by)
   - Status enumerations used across contexts

### ❌ Exclude from Shared Kernel

1. **Context-Specific Business Logic**
   - Order processing rules
   - Customer tier calculations
   - Pricing algorithms

2. **Aggregate-Specific Value Objects**
   - OrderLineItem (belongs to Order context)
   - CustomerPreferences (specific to Customer context)

3. **Infrastructure Concerns**
   - Database models
   - API schemas
   - External service integrations

## Current Implementation

### Directory Structure

```
src/
├── shared_kernel/
│   ├── __init__.py
│   ├── base/
│   │   ├── __init__.py
│   │   ├── entity.py
│   │   ├── value_object.py
│   │   ├── aggregate_root.py
│   │   ├── domain_event.py
│   │   └── specification.py
│   ├── value_objects/
│   │   ├── __init__.py
│   │   ├── email.py
│   │   ├── money.py
│   │   ├── address.py
│   │   └── phone_number.py
│   ├── types/
│   │   ├── __init__.py
│   │   └── identifiers.py
│   └── exceptions/
│       ├── __init__.py
│       └── domain_exceptions.py
```

### Base Classes Implementation

```python
# src/shared_kernel/base/entity.py
from abc import ABC
from dataclasses import dataclass, field
from typing import List
from uuid import UUID

from .domain_event import DomainEvent


@dataclass
class Entity(ABC):
    """Base class for all entities"""
    id: UUID
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Entity):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        return hash(self.id)


# src/shared_kernel/base/aggregate_root.py
@dataclass
class AggregateRoot(Entity):
    """Base class for aggregate roots"""
    _events: List[DomainEvent] = field(default_factory=list, init=False)
    
    def add_event(self, event: DomainEvent) -> None:
        """Add a domain event"""
        self._events.append(event)
    
    def collect_events(self) -> List[DomainEvent]:
        """Collect and clear events"""
        events = self._events.copy()
        self._events.clear()
        return events


# src/shared_kernel/base/value_object.py
from abc import ABC
from dataclasses import dataclass


@dataclass(frozen=True)
class ValueObject(ABC):
    """Base class for value objects - immutable by default"""
    
    def __post_init__(self):
        """Override in subclasses for validation"""
        self.validate()
    
    def validate(self) -> None:
        """Override to add validation logic"""
        pass
```

### Common Value Objects

```python
# src/shared_kernel/value_objects/email.py
import re
from dataclasses import dataclass
from typing import Pattern

from ..base.value_object import ValueObject


@dataclass(frozen=True)
class Email(ValueObject):
    """Email address value object"""
    value: str
    
    EMAIL_PATTERN: Pattern = re.compile(r'^[\w\.-]+@[\w\.-]+\.\w+$')
    
    def validate(self) -> None:
        if not self.value:
            raise ValueError("Email cannot be empty")
        
        if not self.EMAIL_PATTERN.match(self.value):
            raise ValueError(f"Invalid email format: {self.value}")
        
        if len(self.value) > 255:
            raise ValueError("Email too long")
    
    @property
    def domain(self) -> str:
        """Extract domain from email"""
        return self.value.split('@')[1]
    
    @property
    def local_part(self) -> str:
        """Extract local part from email"""
        return self.value.split('@')[0]
    
    def __str__(self) -> str:
        return self.value


# src/shared_kernel/value_objects/money.py
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict

from ..base.value_object import ValueObject


@dataclass(frozen=True)
class Money(ValueObject):
    """Money value object with currency"""
    amount: Decimal
    currency: str
    
    # Could be loaded from configuration
    SUPPORTED_CURRENCIES = ["USD", "EUR", "GBP", "JPY", "CAD"]
    CURRENCY_DECIMALS: Dict[str, int] = {
        "USD": 2, "EUR": 2, "GBP": 2, "JPY": 0, "CAD": 2
    }
    
    def validate(self) -> None:
        if self.currency not in self.SUPPORTED_CURRENCIES:
            raise ValueError(f"Unsupported currency: {self.currency}")
        
        # Ensure correct decimal places
        decimals = self.CURRENCY_DECIMALS[self.currency]
        quantized = self.amount.quantize(
            Decimal(10) ** -decimals,
            rounding=ROUND_HALF_UP
        )
        
        if self.amount != quantized:
            raise ValueError(
                f"{self.currency} requires {decimals} decimal places"
            )
    
    def add(self, other: 'Money') -> 'Money':
        """Add two money values"""
        if self.currency != other.currency:
            raise ValueError(
                f"Cannot add {self.currency} and {other.currency}"
            )
        return Money(self.amount + other.amount, self.currency)
    
    def subtract(self, other: 'Money') -> 'Money':
        """Subtract money values"""
        if self.currency != other.currency:
            raise ValueError(
                f"Cannot subtract {other.currency} from {self.currency}"
            )
        return Money(self.amount - other.amount, self.currency)
    
    def multiply(self, factor: Decimal) -> 'Money':
        """Multiply by a factor"""
        return Money(
            (self.amount * factor).quantize(
                Decimal(10) ** -self.CURRENCY_DECIMALS[self.currency],
                rounding=ROUND_HALF_UP
            ),
            self.currency
        )
    
    def is_positive(self) -> bool:
        """Check if amount is positive"""
        return self.amount > 0
    
    def is_zero(self) -> bool:
        """Check if amount is zero"""
        return self.amount == 0
    
    def __str__(self) -> str:
        return f"{self.currency} {self.amount}"
```

### Type Definitions

```python
# src/shared_kernel/types/custom_types.py
from typing import NewType
from uuid import UUID

# Type aliases for better type safety
CustomerId = NewType('CustomerId', UUID)
OrderId = NewType('OrderId', UUID)
ProductId = NewType('ProductId', UUID)
WarehouseId = NewType('WarehouseId', UUID)

# For e-commerce platform
DatasetId = NewType('DatasetId', UUID)
FieldId = NewType('FieldId', UUID)
BusinessRuleId = NewType('BusinessRuleId', UUID)
PipelineId = NewType('PipelineId', UUID)
```

### Domain Exceptions

```python
# src/shared_kernel/exceptions/domain_exceptions.py
from typing import Optional
from uuid import UUID


class DomainException(Exception):
    """Base exception for domain errors"""
    pass


class EntityNotFoundException(DomainException):
    """Raised when entity not found"""
    def __init__(self, entity_type: str, entity_id: UUID):
        super().__init__(f"{entity_type} with ID {entity_id} not found")
        self.entity_type = entity_type
        self.entity_id = entity_id


class BusinessRuleViolationException(DomainException):
    """Raised when business rule is violated"""
    def __init__(self, message: str, rule_name: Optional[str] = None):
        super().__init__(message)
        self.rule_name = rule_name


class InvalidStateTransitionException(DomainException):
    """Raised when state transition is invalid"""
    def __init__(
        self, 
        entity_type: str, 
        current_state: str, 
        target_state: str
    ):
        message = (
            f"Cannot transition {entity_type} "
            f"from {current_state} to {target_state}"
        )
        super().__init__(message)
        self.entity_type = entity_type
        self.current_state = current_state
        self.target_state = target_state
```

## Usage Examples

### Using Base Classes

```python
# In domain/entities/customer.py
from dataclasses import dataclass
from typing import List
from uuid import UUID

from shared_kernel.base import AggregateRoot
from shared_kernel.value_objects import Email, Address
from shared_kernel.types import CustomerId


@dataclass
class Customer(AggregateRoot):
    """Customer aggregate root using shared kernel"""
    id: CustomerId  # Typed UUID
    email: Email    # Value object
    shipping_addresses: List[Address]
    is_active: bool
    
    def change_email(self, new_email: Email) -> None:
        """Change email with event"""
        old_email = self.email
        self.email = new_email
        
        self.add_event(
            CustomerEmailChanged(
                customer_id=self.id,
                old_email=old_email,
                new_email=new_email
            )
        )
```

### Creating New Value Objects

```python
# For e-commerce platform
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from shared_kernel.base import ValueObject


@dataclass(frozen=True)
class Price(ValueObject):
    """Value object for product pricing"""
    amount: Decimal
    currency: str
    discount_percentage: Optional[Decimal] = None
    
    def validate(self) -> None:
        if self.amount < 0:
            raise ValueError("Price amount cannot be negative")
        
        if self.discount_percentage is not None:
            if not (0 <= self.discount_percentage <= 100):
                raise ValueError("Discount percentage must be between 0 and 100")
    
    def calculate_discounted_amount(self) -> Decimal:
        """Calculate final price after discount"""
        if self.discount_percentage is None:
            return self.amount
        
        discount_amount = self.amount * (self.discount_percentage / 100)
        return self.amount - discount_amount
    
    def __str__(self) -> str:
        return f"{self.currency} {self.amount}"
```

## Maintenance Guidelines

### Shared Kernel Rules

1. **Stability**: Changes should be rare and well-coordinated
2. **Backward Compatibility**: Never break existing contracts
3. **Documentation**: All shared kernel code must be well-documented
4. **Testing**: 100% test coverage required
5. **Review**: Changes require review from all teams using it

### Evolution Strategy

1. **Addition is Safe**: Adding new value objects or methods is generally safe
2. **Modification is Dangerous**: Changing existing behavior requires coordination
3. **Deletion is Forbidden**: Never remove public APIs without deprecation cycle
4. **Versioning**: Consider versioning shared kernel if major changes needed

## Implementation Checklist

- [ ] Create shared_kernel directory structure
- [ ] Implement base classes (Entity, ValueObject, AggregateRoot)
- [ ] Add common value objects (Email, Money, Address)
- [ ] Define custom types for type safety
- [ ] Add domain exceptions
- [ ] Write comprehensive tests for all shared kernel code
- [ ] Document all public APIs
- [ ] Set up import shortcuts in `__init__.py` files
- [ ] Update existing code to use shared kernel

## Benefits

1. **Consistency**: Same concepts implemented identically everywhere
2. **Type Safety**: Strong typing with custom types
3. **Reusability**: No duplication of common logic
4. **Maintainability**: Single source of truth for shared concepts
5. **Domain Focus**: Developers focus on business logic, not infrastructure

---
*Document Version: 1.1*
*Last Updated: 2025-08-03*
*Status: Shared Kernel Guide - Updated to reflect current implementation*