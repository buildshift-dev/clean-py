"""Application startup initialization."""

from uuid import uuid4

from src.domain.entities.customer import Customer
from src.presentation.repositories import get_customer_repository
from src.shared_kernel import CustomerId, Email


async def initialize_sample_data() -> None:
    """Initialize the application with sample data for demo purposes."""
    customer_repo = get_customer_repository()

    # Check if data already exists
    existing_customers = await customer_repo.list_all()
    if existing_customers:
        return  # Data already initialized

    # Create sample customers
    sample_customers = [
        Customer.create(
            customer_id=CustomerId(uuid4()),
            name="Alice Johnson",
            email=Email("alice@example.com"),
            preferences={"theme": "light", "notifications": True, "newsletter": True},
        ),
        Customer.create(
            customer_id=CustomerId(uuid4()),
            name="Bob Smith",
            email=Email("bob@example.com"),
            preferences={"theme": "dark", "notifications": False, "newsletter": False},
        ),
        Customer.create(
            customer_id=CustomerId(uuid4()),
            name="Carol Davis",
            email=Email("carol@example.com"),
            preferences={"theme": "light", "notifications": True, "newsletter": True},
        ).deactivate("Demo inactive customer"),
        Customer.create(
            customer_id=CustomerId(uuid4()),
            name="David Wilson",
            email=Email("david@example.com"),
            preferences={"theme": "auto", "notifications": True, "newsletter": False},
        ),
        Customer.create(
            customer_id=CustomerId(uuid4()),
            name="Emma Brown",
            email=Email("emma@example.com"),
            preferences={"theme": "light", "notifications": False, "newsletter": True},
        ),
    ]

    # Save sample customers
    for customer in sample_customers:
        await customer_repo.save(customer)

    print(f"✅ Initialized {len(sample_customers)} sample customers")
