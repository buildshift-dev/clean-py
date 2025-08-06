from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.customer import Customer
from src.domain.repositories.customer_repository import CustomerRepository
from src.infrastructure.database.models import CustomerModel


class PostgresCustomerRepository(CustomerRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_id(self, customer_id: UUID) -> Customer | None:
        stmt = select(CustomerModel).where(CustomerModel.id == customer_id)  # type: ignore
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return self._model_to_entity(model)

    async def find_by_email(self, email: str) -> Customer | None:
        stmt = select(CustomerModel).where(CustomerModel.email == email)  # type: ignore
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return self._model_to_entity(model)

    async def save(self, customer: Customer) -> Customer:
        model = self._entity_to_model(customer)
        self._session.add(model)
        await self._session.commit()
        return customer

    async def list_all(self) -> list[Customer]:
        stmt = select(CustomerModel)
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._model_to_entity(model) for model in models]

    def _model_to_entity(self, model: CustomerModel) -> Customer:  # type: ignore
        from src.shared_kernel import CustomerId, Email

        return Customer(
            id=model.id,  # type: ignore # Will be overridden by __post_init__
            customer_id=CustomerId(model.id),  # type: ignore
            name=model.name,  # type: ignore
            email=Email(model.email),  # type: ignore
            is_active=model.is_active,  # type: ignore
            preferences=model.preferences or {},  # type: ignore
            created_at=model.created_at,  # type: ignore
            updated_at=model.updated_at,  # type: ignore
        )

    def _entity_to_model(self, entity: Customer) -> CustomerModel:  # type: ignore
        return CustomerModel(
            id=entity.id,  # type: ignore
            name=entity.name,  # type: ignore
            email=entity.email,  # type: ignore
            is_active=entity.is_active,  # type: ignore
            preferences=entity.preferences,  # type: ignore
            created_at=entity.created_at,  # type: ignore
            updated_at=entity.updated_at,  # type: ignore
        )
