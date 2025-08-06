from uuid import uuid4

from src.domain.entities.customer import Customer, CustomerCreated, CustomerDeactivated
from src.shared_kernel import Address, CustomerId, Email


class TestCustomer:
    def test_customer_creation_with_factory(self):
        """Test creating a customer using the factory method"""
        customer_id = CustomerId(uuid4())
        email = Email("john@example.com")

        customer = Customer.create(
            customer_id=customer_id,
            name="John Doe",
            email=email,
            preferences={"theme": "dark"},
        )

        assert customer.customer_id == customer_id
        assert customer.name == "John Doe"
        assert customer.email == email
        assert customer.is_active is True
        assert customer.preferences == {"theme": "dark"}

        # Check domain events
        events = customer.collect_domain_events()
        assert len(events) == 1
        assert isinstance(events[0], CustomerCreated)
        assert events[0].customer_id == customer_id
        assert events[0].customer_name == "John Doe"

    def test_customer_creation_with_address_and_phone(self):
        """Test creating a customer with address and phone"""
        customer_id = CustomerId(uuid4())
        email = Email("john@example.com")
        address = Address(
            street="123 Main St",
            city="Anytown",
            state="CA",
            postal_code="12345",
            country="USA",
        )

        customer = Customer.create(customer_id=customer_id, name="John Doe", email=email, address=address)

        assert customer.address == address
        assert customer.customer_id == customer_id

    def test_customer_deactivate(self):
        """Test customer deactivation business rule"""
        customer_id = CustomerId(uuid4())
        email = Email("john@example.com")

        customer = Customer.create(customer_id=customer_id, name="John Doe", email=email)

        # Clear the creation event for cleaner testing
        customer.collect_domain_events()

        deactivated = customer.deactivate("Business closure")

        # Original customer unchanged (immutable)
        assert customer.is_active is True

        # New customer is deactivated
        assert deactivated.is_active is False
        assert deactivated.name == customer.name
        assert deactivated.email == customer.email
        assert deactivated.updated_at > customer.updated_at

        # Check domain events
        events = deactivated.collect_domain_events()
        assert len(events) == 1
        assert isinstance(events[0], CustomerDeactivated)
        assert events[0].customer_id == customer_id
        assert events[0].reason == "Business closure"

    def test_customer_deactivate_already_inactive_raises_error(self):
        """Test that deactivating an inactive customer raises error"""
        customer_id = CustomerId(uuid4())
        email = Email("john@example.com")

        customer = Customer.create(customer_id=customer_id, name="John Doe", email=email)

        deactivated = customer.deactivate("Manual deactivation")

        # Try to deactivate again should raise error
        try:
            deactivated.deactivate("Test reason")
            raise AssertionError("Should have raised ValueError")
        except ValueError as e:
            assert "already deactivated" in str(e)

    def test_customer_update_address(self):
        """Test updating customer address"""
        customer_id = CustomerId(uuid4())
        email = Email("john@example.com")

        customer = Customer.create(customer_id=customer_id, name="John Doe", email=email)

        address = Address(
            street="456 Oak Ave",
            city="New City",
            state="NY",
            postal_code="54321",
            country="USA",
        )

        updated_customer = customer.update_address(address)

        assert updated_customer.address == address
        assert updated_customer.customer_id == customer_id
        assert updated_customer.name == customer.name
        assert updated_customer.updated_at > customer.updated_at
