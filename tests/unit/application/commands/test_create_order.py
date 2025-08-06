from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.application.use_cases.commands.create_order import (
    CreateOrderCommand,
    CreateOrderUseCase,
)
from src.domain.entities.customer import Customer
from src.domain.entities.order import OrderStatus
from src.shared_kernel import CustomerId, Email


@pytest.mark.asyncio
class TestCreateOrderUseCase:
    async def test_create_order_success(self):
        """Test successful order creation"""
        # Mock customer
        customer_id = uuid4()
        customer = Customer.create(
            customer_id=CustomerId(customer_id),
            name="John Doe",
            email=Email("john@example.com"),
            preferences={},
        )

        # Mock repositories
        mock_customer_repo = AsyncMock()
        mock_customer_repo.find_by_id.return_value = customer

        mock_order_repo = AsyncMock()
        mock_order_repo.save.side_effect = lambda o: o

        # Create use case
        use_case = CreateOrderUseCase(mock_order_repo, mock_customer_repo)

        # Execute command
        command = CreateOrderCommand(
            customer_id=customer_id,
            total_amount=Decimal("99.99"),
            details={"product": "laptop"},
        )

        result = await use_case.execute(command)

        # Assertions
        assert result.customer_id.value == customer_id
        assert result.total_amount.amount == Decimal("99.99")
        assert result.total_amount.currency == "USD"
        assert result.status == OrderStatus.PENDING
        assert result.details == {"product": "laptop"}

        # Verify repository interactions
        mock_customer_repo.find_by_id.assert_called_once_with(customer_id)
        mock_order_repo.save.assert_called_once()

    async def test_create_order_customer_not_found(self):
        """Test order creation with non-existent customer"""
        customer_id = uuid4()

        # Mock repositories
        mock_customer_repo = AsyncMock()
        mock_customer_repo.find_by_id.return_value = None  # Customer not found

        mock_order_repo = AsyncMock()

        # Create use case
        use_case = CreateOrderUseCase(mock_order_repo, mock_customer_repo)

        # Execute command and expect error
        command = CreateOrderCommand(customer_id=customer_id, total_amount=Decimal("50.00"), details={})

        with pytest.raises(ValueError, match="not found"):
            await use_case.execute(command)

        # Verify repository interactions
        mock_customer_repo.find_by_id.assert_called_once_with(customer_id)
        mock_order_repo.save.assert_not_called()

    async def test_create_order_inactive_customer(self):
        """Test order creation with inactive customer"""
        customer_id = uuid4()
        inactive_customer = Customer.create(
            customer_id=CustomerId(customer_id),
            name="John Doe",
            email=Email("john@example.com"),
            preferences={},
        ).deactivate("Test deactivation")

        # Mock repositories
        mock_customer_repo = AsyncMock()
        mock_customer_repo.find_by_id.return_value = inactive_customer

        mock_order_repo = AsyncMock()

        # Create use case
        use_case = CreateOrderUseCase(mock_order_repo, mock_customer_repo)

        # Execute command and expect error
        command = CreateOrderCommand(customer_id=customer_id, total_amount=Decimal("50.00"), details={})

        with pytest.raises(ValueError, match="inactive customer"):
            await use_case.execute(command)

        # Verify save was not called
        mock_order_repo.save.assert_not_called()
