"""Shared repository instances for the demo."""

from uuid import UUID

from src.domain.entities.customer import Customer
from src.domain.entities.order import Order
from src.domain.repositories.customer_repository import CustomerRepository
from src.domain.repositories.order_repository import OrderRepository


class InMemoryCustomerRepository(CustomerRepository):
    """In-memory customer repository for demos."""

    def __init__(self) -> None:
        self._customers: list[Customer] = []

    async def find_by_id(self, customer_id: UUID) -> Customer | None:
        return next((c for c in self._customers if c.id == customer_id), None)

    async def find_by_email(self, email: str) -> Customer | None:
        return next((c for c in self._customers if str(c.email) == email), None)

    async def save(self, customer: Customer) -> Customer:
        # Remove existing customer with same ID if it exists
        self._customers = [c for c in self._customers if c.id != customer.id]
        self._customers.append(customer)
        return customer

    async def list_all(self) -> list[Customer]:
        return self._customers.copy()

    async def search(
        self,
        name_contains: str | None = None,
        email_contains: str | None = None,
        is_active: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Customer]:
        """Search customers with optional filters."""
        filtered = self._customers.copy()

        if name_contains:
            filtered = [c for c in filtered if name_contains.lower() in c.name.lower()]
        if email_contains:
            filtered = [c for c in filtered if email_contains.lower() in str(c.email).lower()]
        if is_active is not None:
            filtered = [c for c in filtered if c.is_active == is_active]

        return filtered[offset : offset + limit]


class InMemoryOrderRepository(OrderRepository):
    """In-memory order repository for demos."""

    def __init__(self) -> None:
        self._orders: list[Order] = []

    async def find_by_id(self, order_id: UUID) -> Order | None:
        return next((o for o in self._orders if o.id == order_id), None)

    async def save(self, order: Order) -> Order:
        # Remove existing order with same ID if it exists
        self._orders = [o for o in self._orders if o.id != order.id]
        self._orders.append(order)
        return order

    async def find_by_customer(self, customer_id: UUID) -> list[Order]:
        return [o for o in self._orders if o.customer_id == customer_id]

    async def list_all(self) -> list[Order]:
        return self._orders.copy()


# Global shared repository instances
_customer_repository = InMemoryCustomerRepository()
_order_repository = InMemoryOrderRepository()


def get_customer_repository() -> CustomerRepository:
    """Get the shared customer repository instance."""
    return _customer_repository


def get_order_repository() -> OrderRepository:
    """Get the shared order repository instance."""
    return _order_repository
