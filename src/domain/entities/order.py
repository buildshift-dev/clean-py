from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from src.shared_kernel import (
    AggregateRoot,
    BusinessRuleViolationError,
    CustomerId,
    DomainEvent,
    Money,
    OrderId,
)


class OrderStatus(Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True)
class OrderCreated(DomainEvent):
    """Domain event raised when an order is created."""

    event_id: UUID
    occurred_at: datetime
    order_id: OrderId
    customer_id: CustomerId
    total_amount: Money


@dataclass(frozen=True)
class OrderCancelled(DomainEvent):
    """Domain event raised when an order is cancelled."""

    event_id: UUID
    occurred_at: datetime
    order_id: OrderId
    customer_id: CustomerId
    previous_status: OrderStatus
    reason: str


@dataclass(frozen=True)
class OrderStatusChanged(DomainEvent):
    """Domain event raised when order status changes."""

    event_id: UUID
    occurred_at: datetime
    order_id: OrderId
    customer_id: CustomerId
    old_status: OrderStatus
    new_status: OrderStatus


@dataclass
class Order(AggregateRoot):
    """Order aggregate root with enhanced value objects and domain events."""

    order_id: OrderId
    customer_id: CustomerId
    total_amount: Money
    status: OrderStatus = OrderStatus.PENDING
    details: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        """Initialize the aggregate and validate business rules."""
        # Set the entity ID from order_id for base Entity class
        object.__setattr__(self, "id", self.order_id.value)

        self._validate_business_rules()

    def _validate_business_rules(self) -> None:
        """Validate order business rules."""
        if self.total_amount.amount <= Decimal("0"):
            raise BusinessRuleViolationError(
                "Order total amount must be greater than zero",
                rule_name="MinimumOrderAmount",
            )

    @classmethod
    def create(
        cls,
        order_id: OrderId,
        customer_id: CustomerId,
        total_amount: Money,
        details: dict[str, Any] | None = None,
    ) -> "Order":
        """Factory method to create a new order with domain event."""
        order = cls(
            id=order_id.value,
            order_id=order_id,
            customer_id=customer_id,
            total_amount=total_amount,
            details=details or {},
        )

        # Raise domain event
        order.add_domain_event(
            OrderCreated(
                event_id=uuid4(),
                occurred_at=datetime.now(UTC),
                order_id=order_id,
                customer_id=customer_id,
                total_amount=total_amount,
            )
        )

        return order

    def can_be_cancelled(self) -> bool:
        """Check if order can be cancelled based on business rules."""
        return self.status in [OrderStatus.PENDING, OrderStatus.CONFIRMED]

    def cancel(self, reason: str = "Customer request") -> "Order":
        """Cancel the order and raise domain event."""
        if not self.can_be_cancelled():
            raise BusinessRuleViolationError(
                f"Order in {self.status.value} status cannot be cancelled",
                rule_name="OrderCancellationRule",
            )

        cancelled_order = Order(
            id=self.order_id.value,
            order_id=self.order_id,
            customer_id=self.customer_id,
            total_amount=self.total_amount,
            status=OrderStatus.CANCELLED,
            details=self.details,
            created_at=self.created_at,
            updated_at=datetime.now(UTC),
        )

        # Copy domain events and add cancellation event
        cancelled_order._domain_events = self._domain_events.copy()
        cancelled_order.add_domain_event(
            OrderCancelled(
                event_id=uuid4(),
                occurred_at=datetime.now(UTC),
                order_id=self.order_id,
                customer_id=self.customer_id,
                previous_status=self.status,
                reason=reason,
            )
        )

        return cancelled_order

    def confirm(self) -> "Order":
        """Confirm a pending order."""
        if self.status != OrderStatus.PENDING:
            raise BusinessRuleViolationError(
                f"Only pending orders can be confirmed. Current status: {self.status.value}",
                rule_name="OrderConfirmationRule",
            )

        return self._change_status(OrderStatus.CONFIRMED)

    def ship(self) -> "Order":
        """Ship a confirmed order."""
        if self.status != OrderStatus.CONFIRMED:
            raise BusinessRuleViolationError(
                f"Only confirmed orders can be shipped. Current status: {self.status.value}",
                rule_name="OrderShippingRule",
            )

        return self._change_status(OrderStatus.SHIPPED)

    def deliver(self) -> "Order":
        """Mark a shipped order as delivered."""
        if self.status != OrderStatus.SHIPPED:
            raise BusinessRuleViolationError(
                f"Only shipped orders can be delivered. Current status: {self.status.value}",
                rule_name="OrderDeliveryRule",
            )

        return self._change_status(OrderStatus.DELIVERED)

    def _change_status(self, new_status: OrderStatus) -> "Order":
        """Internal method to change order status and raise domain event."""
        updated_order = Order(
            id=self.order_id.value,
            order_id=self.order_id,
            customer_id=self.customer_id,
            total_amount=self.total_amount,
            status=new_status,
            details=self.details,
            created_at=self.created_at,
            updated_at=datetime.now(UTC),
        )

        # Copy domain events and add status change event
        updated_order._domain_events = self._domain_events.copy()
        updated_order.add_domain_event(
            OrderStatusChanged(
                event_id=uuid4(),
                occurred_at=datetime.now(UTC),
                order_id=self.order_id,
                customer_id=self.customer_id,
                old_status=self.status,
                new_status=new_status,
            )
        )

        return updated_order
