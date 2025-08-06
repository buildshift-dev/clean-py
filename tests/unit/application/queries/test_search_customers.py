"""Tests for SearchCustomersUseCase."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.application.use_cases.queries.search_customers import SearchCustomersQuery, SearchCustomersUseCase
from src.domain.entities.customer import Customer
from src.domain.repositories.customer_repository import CustomerRepository
from src.shared_kernel import CustomerId, Email


@pytest.fixture
def mock_customer_repository() -> CustomerRepository:
    """Create a mock customer repository."""
    return AsyncMock(spec=CustomerRepository)


@pytest.fixture
def search_customers_use_case(mock_customer_repository: CustomerRepository) -> SearchCustomersUseCase:
    """Create SearchCustomersUseCase instance."""
    return SearchCustomersUseCase(mock_customer_repository)


class TestSearchCustomersQuery:
    """Test cases for SearchCustomersQuery dataclass."""

    def test_valid_query_creation(self) -> None:
        """Test creating a valid query object."""
        query = SearchCustomersQuery(
            name_contains="John", email_contains="@example.com", is_active=True, limit=10, offset=0
        )

        assert query.name_contains == "John"
        assert query.email_contains == "@example.com"
        assert query.is_active is True
        assert query.limit == 10
        assert query.offset == 0

    def test_default_values(self) -> None:
        """Test query with default values."""
        query = SearchCustomersQuery()

        assert query.name_contains is None
        assert query.email_contains is None
        assert query.is_active is None
        assert query.limit == 50
        assert query.offset == 0

    def test_invalid_limit_zero_raises_error(self) -> None:
        """Test that zero limit raises ValueError."""
        with pytest.raises(ValueError, match="Limit must be positive"):
            SearchCustomersQuery(limit=0)

    def test_invalid_limit_negative_raises_error(self) -> None:
        """Test that negative limit raises ValueError."""
        with pytest.raises(ValueError, match="Limit must be positive"):
            SearchCustomersQuery(limit=-1)

    def test_invalid_limit_too_large_raises_error(self) -> None:
        """Test that limit over 100 raises ValueError."""
        with pytest.raises(ValueError, match="Limit cannot exceed 100"):
            SearchCustomersQuery(limit=101)

    def test_invalid_negative_offset_raises_error(self) -> None:
        """Test that negative offset raises ValueError."""
        with pytest.raises(ValueError, match="Offset cannot be negative"):
            SearchCustomersQuery(offset=-1)


@pytest.mark.asyncio
class TestSearchCustomersUseCase:
    """Test cases for SearchCustomersUseCase."""

    async def test_execute_calls_repository_with_correct_parameters(
        self, search_customers_use_case: SearchCustomersUseCase, mock_customer_repository: CustomerRepository
    ) -> None:
        """Test that execute calls repository with correct parameters."""
        # Arrange
        query = SearchCustomersQuery(
            name_contains="John", email_contains="@example.com", is_active=True, limit=10, offset=5
        )
        expected_customers = [
            Customer.create(
                customer_id=CustomerId(uuid4()), name="John Doe", email=Email("john@example.com"), preferences={}
            )
        ]
        mock_customer_repository.search.return_value = expected_customers

        # Act
        result = await search_customers_use_case.execute(query)

        # Assert
        assert result == expected_customers
        mock_customer_repository.search.assert_called_once_with(
            name_contains="John", email_contains="@example.com", is_active=True, limit=10, offset=5
        )

    async def test_execute_with_default_query(
        self, search_customers_use_case: SearchCustomersUseCase, mock_customer_repository: CustomerRepository
    ) -> None:
        """Test execute with default query parameters."""
        # Arrange
        query = SearchCustomersQuery()
        expected_customers = []
        mock_customer_repository.search.return_value = expected_customers

        # Act
        result = await search_customers_use_case.execute(query)

        # Assert
        assert result == expected_customers
        mock_customer_repository.search.assert_called_once_with(
            name_contains=None, email_contains=None, is_active=None, limit=50, offset=0
        )

    async def test_execute_returns_filtered_customers(
        self, search_customers_use_case: SearchCustomersUseCase, mock_customer_repository: CustomerRepository
    ) -> None:
        """Test that execute returns filtered customers."""
        # Arrange
        query = SearchCustomersQuery(name_contains="Alice", is_active=True)
        expected_customers = [
            Customer.create(
                customer_id=CustomerId(uuid4()),
                name="Alice Johnson",
                email=Email("alice@example.com"),
                preferences={"theme": "dark"},
            ),
            Customer.create(
                customer_id=CustomerId(uuid4()),
                name="Alice Smith",
                email=Email("alice.smith@example.com"),
                preferences={"theme": "light"},
            ),
        ]
        mock_customer_repository.search.return_value = expected_customers

        # Act
        result = await search_customers_use_case.execute(query)

        # Assert
        assert len(result) == 2
        assert all(customer.name.startswith("Alice") for customer in result)
        assert all(customer.is_active for customer in result)

    async def test_execute_returns_empty_list_when_no_matches(
        self, search_customers_use_case: SearchCustomersUseCase, mock_customer_repository: CustomerRepository
    ) -> None:
        """Test that execute returns empty list when no customers match."""
        # Arrange
        query = SearchCustomersQuery(name_contains="NonexistentName")
        mock_customer_repository.search.return_value = []

        # Act
        result = await search_customers_use_case.execute(query)

        # Assert
        assert result == []
        mock_customer_repository.search.assert_called_once_with(
            name_contains="NonexistentName", email_contains=None, is_active=None, limit=50, offset=0
        )
