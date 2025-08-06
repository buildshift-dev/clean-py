"""Get customer orders query use case."""

from uuid import UUID

from src.domain.entities.order import Order
from src.domain.repositories.order_repository import OrderRepository


class GetCustomerOrdersQuery:
    """Query to retrieve all orders for a specific customer."""

    def __init__(self, order_repository: OrderRepository) -> None:
        self._order_repository = order_repository

    async def execute(self, customer_id: UUID) -> list[Order]:
        """Execute the query to get customer orders.

        Args:
            customer_id: The UUID of the customer

        Returns:
            List of orders for the customer

        Raises:
            ValueError: If customer_id is invalid
        """
        if not customer_id:
            raise ValueError("Customer ID cannot be empty")

        return await self._order_repository.find_by_customer(customer_id)
