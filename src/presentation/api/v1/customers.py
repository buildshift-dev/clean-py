from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.application.use_cases.commands.create_customer import (
    CreateCustomerCommand,
    CreateCustomerUseCase,
)
from src.application.use_cases.queries.search_customers import (
    SearchCustomersQuery,
    SearchCustomersUseCase,
)
from src.domain.repositories.customer_repository import CustomerRepository
from src.presentation.repositories import get_customer_repository
from src.presentation.schemas.customer_schemas import (
    CreateCustomerRequest,
    CustomerResponse,
)

router = APIRouter(prefix="/api/v1/customers", tags=["customers"])


async def get_create_customer_use_case() -> CreateCustomerUseCase:
    """Get create customer use case dependency."""
    repo = get_customer_repository()
    return CreateCustomerUseCase(repo)


async def get_search_customers_use_case() -> SearchCustomersUseCase:
    """Get search customers use case dependency."""
    repo = get_customer_repository()
    return SearchCustomersUseCase(repo)


@router.post("/", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    request: CreateCustomerRequest,
    use_case: CreateCustomerUseCase = Depends(get_create_customer_use_case),
) -> CustomerResponse:
    """Create a new customer."""
    try:
        command = CreateCustomerCommand(name=request.name, email=request.email, preferences=request.preferences)
        customer = await use_case.execute(command)

        return CustomerResponse(
            id=customer.id,
            name=customer.name,
            email=str(customer.email),
            is_active=customer.is_active,
            preferences=customer.preferences,
            created_at=customer.created_at,
            updated_at=customer.updated_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("/", response_model=list[CustomerResponse])
async def list_customers(
    repo: CustomerRepository = Depends(get_customer_repository),
) -> list[CustomerResponse]:
    """List all customers."""
    customers = await repo.list_all()
    return [
        CustomerResponse(
            id=c.id,
            name=c.name,
            email=str(c.email),
            is_active=c.is_active,
            preferences=c.preferences,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
        for c in customers
    ]


@router.get("/search", response_model=list[CustomerResponse])
async def search_customers(
    name_contains: str | None = Query(None, description="Filter by name containing this text"),
    email_contains: str | None = Query(None, description="Filter by email containing this text"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    use_case: SearchCustomersUseCase = Depends(get_search_customers_use_case),
) -> list[CustomerResponse]:
    """Search customers with optional filters."""
    query = SearchCustomersQuery(
        name_contains=name_contains,
        email_contains=email_contains,
        is_active=is_active,
        limit=limit,
        offset=offset,
    )
    customers = await use_case.execute(query)
    return [
        CustomerResponse(
            id=c.id,
            name=c.name,
            email=str(c.email),
            is_active=c.is_active,
            preferences=c.preferences,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
        for c in customers
    ]


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: UUID,
    repo: CustomerRepository = Depends(get_customer_repository),
) -> CustomerResponse:
    """Get a specific customer by ID."""
    customer = await repo.find_by_id(customer_id)
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    return CustomerResponse(
        id=customer.id,
        name=customer.name,
        email=str(customer.email),
        is_active=customer.is_active,
        preferences=customer.preferences,
        created_at=customer.created_at,
        updated_at=customer.updated_at,
    )
