from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities.order import Order


class OrderRepository(ABC):
    @abstractmethod
    async def find_by_id(self, order_id: UUID) -> Order | None:
        pass

    @abstractmethod
    async def save(self, order: Order) -> Order:
        pass

    @abstractmethod
    async def find_by_customer(self, customer_id: UUID) -> list[Order]:
        pass

    @abstractmethod
    async def list_all(self) -> list[Order]:
        pass
