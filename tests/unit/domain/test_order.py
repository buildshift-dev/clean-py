from decimal import Decimal
from uuid import uuid4

import pytest

from src.domain.entities.order import (
    Order,
    OrderCancelled,
    OrderCreated,
    OrderStatus,
    OrderStatusChanged,
)
from src.shared_kernel import BusinessRuleViolationError, CustomerId, Money, OrderId


class TestOrder:
    def test_order_creation_with_factory(self):
        """Test creating an order using the factory method"""
        order_id = OrderId(uuid4())
        customer_id = CustomerId(uuid4())
        total_amount = Money(Decimal("99.99"), "USD")

        order = Order.create(
            order_id=order_id,
            customer_id=customer_id,
            total_amount=total_amount,
            details={"product": "laptop"},
        )

        assert order.order_id == order_id
        assert order.customer_id == customer_id
        assert order.total_amount == total_amount
        assert order.status == OrderStatus.PENDING
        assert order.details == {"product": "laptop"}

        # Check domain events
        events = order.collect_domain_events()
        assert len(events) == 1
        assert isinstance(events[0], OrderCreated)
        assert events[0].order_id == order_id
        assert events[0].customer_id == customer_id

    def test_order_creation_with_zero_amount_raises_error(self):
        """Test that creating order with zero amount raises error"""
        order_id = OrderId(uuid4())
        customer_id = CustomerId(uuid4())
        total_amount = Money(Decimal("0.00"), "USD")

        with pytest.raises(BusinessRuleViolationError, match="greater than zero"):
            Order.create(order_id=order_id, customer_id=customer_id, total_amount=total_amount)

    def test_can_be_cancelled_when_pending(self):
        """Test that pending orders can be cancelled"""
        order_id = OrderId(uuid4())
        customer_id = CustomerId(uuid4())
        total_amount = Money(Decimal("50.00"), "USD")

        order = Order.create(order_id=order_id, customer_id=customer_id, total_amount=total_amount)

        assert order.can_be_cancelled() is True

    def test_can_be_cancelled_when_confirmed(self):
        """Test that confirmed orders can be cancelled"""
        order_id = OrderId(uuid4())
        customer_id = CustomerId(uuid4())
        total_amount = Money(Decimal("50.00"), "USD")

        order = Order.create(order_id=order_id, customer_id=customer_id, total_amount=total_amount)

        confirmed_order = order.confirm()
        assert confirmed_order.can_be_cancelled() is True

    def test_cannot_be_cancelled_when_shipped(self):
        """Test that shipped orders cannot be cancelled"""
        order_id = OrderId(uuid4())
        customer_id = CustomerId(uuid4())
        total_amount = Money(Decimal("50.00"), "USD")

        order = Order.create(order_id=order_id, customer_id=customer_id, total_amount=total_amount)

        confirmed_order = order.confirm()
        shipped_order = confirmed_order.ship()

        assert shipped_order.can_be_cancelled() is False

    def test_cancel_pending_order(self):
        """Test cancelling a pending order"""
        order_id = OrderId(uuid4())
        customer_id = CustomerId(uuid4())
        total_amount = Money(Decimal("50.00"), "USD")

        order = Order.create(order_id=order_id, customer_id=customer_id, total_amount=total_amount)

        # Clear creation event for cleaner testing
        order.collect_domain_events()

        cancelled = order.cancel("Customer request")

        # Original order unchanged (immutable)
        assert order.status == OrderStatus.PENDING

        # New order is cancelled
        assert cancelled.status == OrderStatus.CANCELLED
        assert cancelled.order_id == order.order_id
        assert cancelled.total_amount == order.total_amount

        # Check domain events
        events = cancelled.collect_domain_events()
        assert len(events) == 1
        assert isinstance(events[0], OrderCancelled)
        assert events[0].order_id == order_id
        assert events[0].reason == "Customer request"

    def test_cancel_shipped_order_raises_error(self):
        """Test that cancelling shipped order raises error"""
        order_id = OrderId(uuid4())
        customer_id = CustomerId(uuid4())
        total_amount = Money(Decimal("50.00"), "USD")

        order = Order.create(order_id=order_id, customer_id=customer_id, total_amount=total_amount)

        confirmed_order = order.confirm()
        shipped_order = confirmed_order.ship()

        with pytest.raises(BusinessRuleViolationError, match="cannot be cancelled"):
            shipped_order.cancel()

    def test_order_status_progression(self):
        """Test the complete order status progression"""
        order_id = OrderId(uuid4())
        customer_id = CustomerId(uuid4())
        total_amount = Money(Decimal("100.00"), "USD")

        # Create order (PENDING)
        order = Order.create(order_id=order_id, customer_id=customer_id, total_amount=total_amount)
        assert order.status == OrderStatus.PENDING

        # Confirm order
        confirmed_order = order.confirm()
        assert confirmed_order.status == OrderStatus.CONFIRMED

        # Ship order
        shipped_order = confirmed_order.ship()
        assert shipped_order.status == OrderStatus.SHIPPED

        # Deliver order
        delivered_order = shipped_order.deliver()
        assert delivered_order.status == OrderStatus.DELIVERED

        # Check domain events for status changes
        events = delivered_order.collect_domain_events()
        status_change_events = [e for e in events if isinstance(e, OrderStatusChanged)]
        assert len(status_change_events) == 3  # PENDING->CONFIRMED, CONFIRMED->SHIPPED, SHIPPED->DELIVERED

    def test_invalid_status_transitions_raise_errors(self):
        """Test that invalid status transitions raise business rule violations"""
        order_id = OrderId(uuid4())
        customer_id = CustomerId(uuid4())
        total_amount = Money(Decimal("50.00"), "USD")

        order = Order.create(order_id=order_id, customer_id=customer_id, total_amount=total_amount)

        # Can't ship a pending order
        with pytest.raises(BusinessRuleViolationError, match="Only confirmed orders can be shipped"):
            order.ship()

        # Can't deliver a pending order
        with pytest.raises(BusinessRuleViolationError, match="Only shipped orders can be delivered"):
            order.deliver()

        # Can't confirm an already confirmed order
        confirmed_order = order.confirm()
        with pytest.raises(BusinessRuleViolationError, match="Only pending orders can be confirmed"):
            confirmed_order.confirm()
