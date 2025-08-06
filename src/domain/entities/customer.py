from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from src.shared_kernel import (
    Address,
    AggregateRoot,
    CustomerId,
    DomainEvent,
    Email,
    PhoneNumber,
)


@dataclass(frozen=True)
class CustomerCreated(DomainEvent):
    """Domain event raised when a customer is created."""

    event_id: UUID
    occurred_at: datetime
    customer_id: CustomerId
    customer_name: str
    customer_email: str


@dataclass(frozen=True)
class CustomerDeactivated(DomainEvent):
    """Domain event raised when a customer is deactivated."""

    event_id: UUID
    occurred_at: datetime
    customer_id: CustomerId
    reason: str


@dataclass
class Customer(AggregateRoot):
    """Customer aggregate root with enhanced value objects and domain events."""

    customer_id: CustomerId
    name: str
    email: Email
    address: Address | None = None
    phone: PhoneNumber | None = None
    is_active: bool = True
    preferences: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        """Initialize the aggregate and validate business rules."""
        # Set the entity ID from customer_id for base Entity class
        object.__setattr__(self, "id", self.customer_id.value)

        self._validate_business_rules()

    def _validate_business_rules(self) -> None:
        """Validate customer business rules."""
        if not self.name.strip():
            raise ValueError("Customer name cannot be empty")

        # Email validation is handled by the Email value object
        # Additional business rules can be added here

    @classmethod
    def create(
        cls,
        customer_id: CustomerId,
        name: str,
        email: Email,
        address: Address | None = None,
        phone: PhoneNumber | None = None,
        preferences: dict[str, Any] | None = None,
    ) -> "Customer":
        """Factory method to create a new customer with domain event."""
        customer = cls(
            id=customer_id.value,
            customer_id=customer_id,
            name=name,
            email=email,
            address=address,
            phone=phone,
            preferences=preferences or {},
        )

        # Raise domain event
        customer.add_domain_event(
            CustomerCreated(
                event_id=uuid4(),
                occurred_at=datetime.now(UTC),
                customer_id=customer_id,
                customer_name=name,
                customer_email=str(email),
            )
        )

        return customer

    def deactivate(self, reason: str = "Manual deactivation") -> "Customer":
        """Deactivate the customer and raise domain event."""
        if not self.is_active:
            raise ValueError("Customer is already deactivated")

        deactivated_customer = Customer(
            id=self.customer_id.value,
            customer_id=self.customer_id,
            name=self.name,
            email=self.email,
            address=self.address,
            phone=self.phone,
            is_active=False,
            preferences=self.preferences,
            created_at=self.created_at,
            updated_at=datetime.now(UTC),
        )

        # Copy domain events and add deactivation event
        deactivated_customer._domain_events = self._domain_events.copy()
        deactivated_customer.add_domain_event(
            CustomerDeactivated(
                event_id=uuid4(),
                occurred_at=datetime.now(UTC),
                customer_id=self.customer_id,
                reason=reason,
            )
        )

        return deactivated_customer

    def update_address(self, address: Address) -> "Customer":
        """Update customer address."""
        return Customer(
            id=self.customer_id.value,
            customer_id=self.customer_id,
            name=self.name,
            email=self.email,
            address=address,
            phone=self.phone,
            is_active=self.is_active,
            preferences=self.preferences,
            created_at=self.created_at,
            updated_at=datetime.now(UTC),
        )

    def update_phone(self, phone: PhoneNumber) -> "Customer":
        """Update customer phone number."""
        return Customer(
            id=self.customer_id.value,
            customer_id=self.customer_id,
            name=self.name,
            email=self.email,
            address=self.address,
            phone=phone,
            is_active=self.is_active,
            preferences=self.preferences,
            created_at=self.created_at,
            updated_at=datetime.now(UTC),
        )
