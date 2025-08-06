"""Orders API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from src.application.use_cases.commands.create_order import (
    CreateOrderCommand,
    CreateOrderUseCase,
)
from src.application.use_cases.queries.get_customer_orders import GetCustomerOrdersQuery
from src.domain.repositories.order_repository import OrderRepository
from src.presentation.repositories import get_customer_repository, get_order_repository
from src.presentation.schemas.order_schemas import (
    CreateOrderRequest,
    OrderResponse,
)

router = APIRouter(prefix="/api/v1/orders", tags=["orders"])


async def get_create_order_use_case() -> CreateOrderUseCase:
    """Get create order use case dependency."""
    order_repo = get_order_repository()
    customer_repo = get_customer_repository()
    return CreateOrderUseCase(order_repo, customer_repo)


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    request: CreateOrderRequest,
    use_case: CreateOrderUseCase = Depends(get_create_order_use_case),
) -> OrderResponse:
    """Create a new order."""
    try:
        command = CreateOrderCommand(
            customer_id=request.customer_id,
            total_amount=request.total_amount,
            currency=request.currency,
            details=request.details,
        )
        order = await use_case.execute(command)

        return OrderResponse(
            id=order.id,
            customer_id=UUID(str(order.customer_id)),
            total_amount=order.total_amount.amount,
            currency=order.total_amount.currency,
            status=order.status.value,
            details=order.details,
            created_at=order.created_at,
            updated_at=order.updated_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("/", response_model=list[OrderResponse])
async def list_orders(
    repo: OrderRepository = Depends(get_order_repository),
) -> list[OrderResponse]:
    """List all orders."""
    orders = await repo.list_all()
    return [
        OrderResponse(
            id=o.id,
            customer_id=UUID(str(o.customer_id)),
            total_amount=o.total_amount.amount,
            currency=o.total_amount.currency,
            status=o.status.value,
            details=o.details,
            created_at=o.created_at,
            updated_at=o.updated_at,
        )
        for o in orders
    ]


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: UUID,
    repo: OrderRepository = Depends(get_order_repository),
) -> OrderResponse:
    """Get a specific order by ID."""
    order = await repo.find_by_id(order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    return OrderResponse(
        id=order.id,
        customer_id=UUID(str(order.customer_id)),
        total_amount=order.total_amount.amount,
        currency=order.total_amount.currency,
        status=order.status.value,
        details=order.details,
        created_at=order.created_at,
        updated_at=order.updated_at,
    )


@router.get("/customer/{customer_id}", response_model=list[OrderResponse])
async def get_customer_orders(
    customer_id: UUID,
    repo: OrderRepository = Depends(get_order_repository),
) -> list[OrderResponse]:
    """Get all orders for a specific customer."""
    query = GetCustomerOrdersQuery(repo)
    orders = await query.execute(customer_id)

    return [
        OrderResponse(
            id=o.id,
            customer_id=UUID(str(o.customer_id)),
            total_amount=o.total_amount.amount,
            currency=o.total_amount.currency,
            status=o.status.value,
            details=o.details,
            created_at=o.created_at,
            updated_at=o.updated_at,
        )
        for o in orders
    ]
