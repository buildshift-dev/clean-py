from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.order import Order, OrderStatus
from src.domain.repositories.order_repository import OrderRepository
from src.infrastructure.database.models import OrderModel


class PostgresOrderRepository(OrderRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_id(self, order_id: UUID) -> Order | None:
        stmt = select(OrderModel).where(OrderModel.id == order_id)  # type: ignore
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return self._model_to_entity(model)

    async def save(self, order: Order) -> Order:
        model = self._entity_to_model(order)
        self._session.add(model)
        await self._session.commit()
        return order

    async def find_by_customer(self, customer_id: UUID) -> list[Order]:
        stmt = select(OrderModel).where(OrderModel.customer_id == customer_id)  # type: ignore
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._model_to_entity(model) for model in models]

    async def list_all(self) -> list[Order]:
        stmt = select(OrderModel)
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._model_to_entity(model) for model in models]

    def _model_to_entity(self, model: OrderModel) -> Order:  # type: ignore
        from src.shared_kernel import CustomerId, Money, OrderId

        return Order(
            id=model.id,  # type: ignore # Will be overridden by __post_init__
            order_id=OrderId(model.id),  # type: ignore
            customer_id=CustomerId(model.customer_id),  # type: ignore
            total_amount=Money(amount=model.total_amount, currency="USD"),  # type: ignore  # TODO: Store currency
            status=OrderStatus(model.status),  # type: ignore
            details=model.details or {},  # type: ignore
            created_at=model.created_at,  # type: ignore
            updated_at=model.updated_at,  # type: ignore
        )

    def _entity_to_model(self, entity: Order) -> OrderModel:  # type: ignore
        return OrderModel(
            id=entity.id,  # type: ignore
            customer_id=entity.customer_id,  # type: ignore
            total_amount=entity.total_amount,  # type: ignore
            status=entity.status.value,  # type: ignore
            details=entity.details,  # type: ignore
            created_at=entity.created_at,  # type: ignore
            updated_at=entity.updated_at,  # type: ignore
        )
