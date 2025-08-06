"""Tests for GetCustomerOrdersQuery use case."""

from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.application.use_cases.queries.get_customer_orders import GetCustomerOrdersQuery
from src.domain.entities.order import Order
from src.domain.repositories.order_repository import OrderRepository
from src.shared_kernel import CustomerId, Money, OrderId


@pytest.fixture
def mock_order_repository() -> OrderRepository:
    """Create a mock order repository."""
    return AsyncMock(spec=OrderRepository)


@pytest.fixture
def get_customer_orders_query(mock_order_repository: OrderRepository) -> GetCustomerOrdersQuery:
    """Create GetCustomerOrdersQuery instance."""
    return GetCustomerOrdersQuery(mock_order_repository)


@pytest.mark.asyncio
class TestGetCustomerOrdersQuery:
    """Test cases for GetCustomerOrdersQuery."""

    async def test_execute_returns_customer_orders(
        self, get_customer_orders_query: GetCustomerOrdersQuery, mock_order_repository: OrderRepository
    ) -> None:
        """Test that execute returns orders for the specified customer."""
        # Arrange
        customer_id = uuid4()
        expected_orders = [
            Order.create(
                order_id=OrderId(uuid4()),
                customer_id=CustomerId(customer_id),
                total_amount=Money(Decimal("100"), "USD"),
                details={},
            ),
            Order.create(
                order_id=OrderId(uuid4()),
                customer_id=CustomerId(customer_id),
                total_amount=Money(Decimal("200"), "USD"),
                details={},
            ),
        ]
        mock_order_repository.find_by_customer.return_value = expected_orders

        # Act
        result = await get_customer_orders_query.execute(customer_id)

        # Assert
        assert result == expected_orders
        mock_order_repository.find_by_customer.assert_called_once_with(customer_id)

    async def test_execute_returns_empty_list_when_no_orders(
        self, get_customer_orders_query: GetCustomerOrdersQuery, mock_order_repository: OrderRepository
    ) -> None:
        """Test that execute returns empty list when customer has no orders."""
        # Arrange
        customer_id = uuid4()
        mock_order_repository.find_by_customer.return_value = []

        # Act
        result = await get_customer_orders_query.execute(customer_id)

        # Assert
        assert result == []
        mock_order_repository.find_by_customer.assert_called_once_with(customer_id)

    async def test_execute_raises_error_for_empty_customer_id(
        self, get_customer_orders_query: GetCustomerOrdersQuery
    ) -> None:
        """Test that execute raises ValueError for empty customer ID."""
        # Act & Assert
        with pytest.raises(ValueError, match="Customer ID cannot be empty"):
            await get_customer_orders_query.execute(None)  # type: ignore
