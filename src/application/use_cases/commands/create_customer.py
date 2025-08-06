from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from src.domain.entities.customer import Customer
from src.domain.repositories.customer_repository import CustomerRepository
from src.shared_kernel import CustomerId, Email


@dataclass
class CreateCustomerCommand:
    name: str
    email: str
    preferences: dict[str, Any] | None = None


class CreateCustomerUseCase:
    def __init__(self, customer_repository: CustomerRepository) -> None:
        self._customer_repo = customer_repository

    async def execute(self, command: CreateCustomerCommand) -> Customer:
        # Check if customer with email already exists
        existing = await self._customer_repo.find_by_email(command.email)
        if existing:
            raise ValueError(f"Customer with email {command.email} already exists")

        # Create new customer using factory method
        customer_id = CustomerId(uuid4())
        email = Email(command.email)

        customer = Customer.create(
            customer_id=customer_id,
            name=command.name,
            email=email,
            preferences=command.preferences or {},
        )

        return await self._customer_repo.save(customer)
