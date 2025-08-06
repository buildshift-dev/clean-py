from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities.customer import Customer


class CustomerRepository(ABC):
    @abstractmethod
    async def find_by_id(self, customer_id: UUID) -> Customer | None:
        pass

    @abstractmethod
    async def find_by_email(self, email: str) -> Customer | None:
        pass

    @abstractmethod
    async def save(self, customer: Customer) -> Customer:
        pass

    @abstractmethod
    async def list_all(self) -> list[Customer]:
        pass

    @abstractmethod
    async def search(
        self,
        name_contains: str | None = None,
        email_contains: str | None = None,
        is_active: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Customer]:
        """Search customers with optional filters."""
        pass
