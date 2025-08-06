from dataclasses import dataclass
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from src.domain.entities.order import Order
from src.domain.repositories.customer_repository import CustomerRepository
from src.domain.repositories.order_repository import OrderRepository
from src.shared_kernel import CustomerId, Money, OrderId


@dataclass
class CreateOrderCommand:
    customer_id: UUID
    total_amount: Decimal
    currency: str = "USD"
    details: dict[str, Any] | None = None


class CreateOrderUseCase:
    def __init__(self, order_repository: OrderRepository, customer_repository: CustomerRepository) -> None:
        self._order_repo = order_repository
        self._customer_repo = customer_repository

    async def execute(self, command: CreateOrderCommand) -> Order:
        # Verify customer exists
        customer = await self._customer_repo.find_by_id(command.customer_id)
        if not customer:
            raise ValueError(f"Customer with ID {command.customer_id} not found")

        if not customer.is_active:
            raise ValueError("Cannot create order for inactive customer")

        # Create new order using factory method
        order_id = OrderId(uuid4())
        customer_id = CustomerId(command.customer_id)
        total_amount = Money(command.total_amount, command.currency)

        order = Order.create(
            order_id=order_id,
            customer_id=customer_id,
            total_amount=total_amount,
            details=command.details or {},
        )

        return await self._order_repo.save(order)
