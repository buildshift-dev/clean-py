from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.application.use_cases.commands.create_customer import (
    CreateCustomerCommand,
    CreateCustomerUseCase,
)
from src.domain.entities.customer import Customer
from src.shared_kernel import CustomerId, Email


@pytest.mark.asyncio
class TestCreateCustomerUseCase:
    async def test_create_customer_success(self):
        """Test successful customer creation"""
        # Mock repository
        mock_repo = AsyncMock()
        mock_repo.find_by_email.return_value = None  # No existing customer
        mock_repo.save.side_effect = lambda c: c  # Return saved customer

        # Create use case
        use_case = CreateCustomerUseCase(mock_repo)

        # Execute command
        command = CreateCustomerCommand(name="John Doe", email="john@example.com", preferences={"theme": "dark"})

        result = await use_case.execute(command)

        # Assertions
        assert result.name == "John Doe"
        assert str(result.email) == "john@example.com"
        assert result.preferences == {"theme": "dark"}
        assert result.is_active is True

        # Verify repository interactions
        mock_repo.find_by_email.assert_called_once_with("john@example.com")
        mock_repo.save.assert_called_once()

    async def test_create_customer_duplicate_email(self):
        """Test customer creation with duplicate email"""
        # Mock repository with existing customer
        existing_customer = Customer.create(
            customer_id=CustomerId(uuid4()),
            name="Existing User",
            email=Email("john@example.com"),
            preferences={},
        )

        mock_repo = AsyncMock()
        mock_repo.find_by_email.return_value = existing_customer

        # Create use case
        use_case = CreateCustomerUseCase(mock_repo)

        # Execute command and expect error
        command = CreateCustomerCommand(name="John Doe", email="john@example.com", preferences={})

        with pytest.raises(ValueError, match="already exists"):
            await use_case.execute(command)

        # Verify repository called but save was not
        mock_repo.find_by_email.assert_called_once_with("john@example.com")
        mock_repo.save.assert_not_called()

    async def test_create_customer_with_empty_preferences(self):
        """Test customer creation with no preferences"""
        mock_repo = AsyncMock()
        mock_repo.find_by_email.return_value = None
        mock_repo.save.side_effect = lambda c: c

        use_case = CreateCustomerUseCase(mock_repo)

        command = CreateCustomerCommand(
            name="Jane Doe",
            email="jane@example.com",
            # No preferences provided
        )

        result = await use_case.execute(command)

        assert result.preferences == {}  # Should default to empty dict
