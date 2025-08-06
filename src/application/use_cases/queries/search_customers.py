"""Search customers query use case."""

from dataclasses import dataclass

from src.domain.entities.customer import Customer
from src.domain.repositories.customer_repository import CustomerRepository


@dataclass(frozen=True)
class SearchCustomersQuery:
    """Query parameters for searching customers."""

    name_contains: str | None = None
    email_contains: str | None = None
    is_active: bool | None = None
    limit: int = 50
    offset: int = 0

    def __post_init__(self) -> None:
        """Validate query parameters."""
        if self.limit <= 0:
            raise ValueError("Limit must be positive")
        if self.limit > 100:
            raise ValueError("Limit cannot exceed 100")
        if self.offset < 0:
            raise ValueError("Offset cannot be negative")


class SearchCustomersUseCase:
    """Use case for searching customers with various filters."""

    def __init__(self, customer_repository: CustomerRepository) -> None:
        self._customer_repository = customer_repository

    async def execute(self, query: SearchCustomersQuery) -> list[Customer]:
        """Execute the search query.

        Args:
            query: Search parameters

        Returns:
            List of customers matching the criteria
        """
        return await self._customer_repository.search(
            name_contains=query.name_contains,
            email_contains=query.email_contains,
            is_active=query.is_active,
            limit=query.limit,
            offset=query.offset,
        )
