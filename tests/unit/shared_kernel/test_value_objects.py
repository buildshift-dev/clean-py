"""Tests for shared kernel value objects."""

from decimal import Decimal
from uuid import uuid4

import pytest

from src.shared_kernel import Address, CustomerId, Email, Money, OrderId, PhoneNumber


class TestEmail:
    """Test cases for Email value object."""

    def test_valid_email_creation(self):
        """Test creating a valid email."""
        email = Email("test@example.com")
        assert email.value == "test@example.com"
        assert email.domain == "example.com"
        assert email.local_part == "test"
        assert str(email) == "test@example.com"

    def test_invalid_email_format_raises_error(self):
        """Test that invalid email format raises ValueError."""
        with pytest.raises(ValueError, match="Invalid email format"):
            Email("invalid-email")

        with pytest.raises(ValueError, match="Invalid email format"):
            Email("test@")

        with pytest.raises(ValueError, match="Invalid email format"):
            Email("@example.com")

    def test_empty_email_raises_error(self):
        """Test that empty email raises ValueError."""
        with pytest.raises(ValueError, match="Email cannot be empty"):
            Email("")


class TestMoney:
    """Test cases for Money value object."""

    def test_valid_money_creation(self):
        """Test creating valid money."""
        money = Money(Decimal("100.50"), "USD")
        assert money.amount == Decimal("100.50")
        assert money.currency == "USD"
        assert str(money) == "100.50 USD"

    def test_negative_amount_raises_error(self):
        """Test that negative amount raises ValueError."""
        with pytest.raises(ValueError, match="Amount cannot be negative"):
            Money(Decimal("-10.00"), "USD")

    def test_invalid_currency_raises_error(self):
        """Test that invalid currency raises ValueError."""
        with pytest.raises(ValueError, match="Invalid currency code"):
            Money(Decimal("100.00"), "US")  # Too short

        with pytest.raises(ValueError, match="Invalid currency code"):
            Money(Decimal("100.00"), "usd")  # Not uppercase

    def test_money_addition(self):
        """Test adding money with same currency."""
        money1 = Money(Decimal("100.00"), "USD")
        money2 = Money(Decimal("50.00"), "USD")
        result = money1.add(money2)

        assert result.amount == Decimal("150.00")
        assert result.currency == "USD"

    def test_money_addition_different_currency_raises_error(self):
        """Test that adding different currencies raises ValueError."""
        money1 = Money(Decimal("100.00"), "USD")
        money2 = Money(Decimal("50.00"), "EUR")

        with pytest.raises(ValueError, match="Cannot add different currencies"):
            money1.add(money2)

    def test_money_multiplication(self):
        """Test multiplying money by a factor."""
        money = Money(Decimal("100.00"), "USD")
        result = money.multiply(Decimal("2.5"))

        assert result.amount == Decimal("250.00")
        assert result.currency == "USD"


class TestAddress:
    """Test cases for Address value object."""

    def test_valid_address_creation(self):
        """Test creating a valid address."""
        address = Address(
            street="123 Main St",
            city="Anytown",
            state="CA",
            postal_code="12345",
            country="USA",
        )

        assert address.street == "123 Main St"
        assert address.city == "Anytown"
        assert address.state == "CA"
        assert address.postal_code == "12345"
        assert address.country == "USA"

        expected_full = "123 Main St\nAnytown, CA 12345\nUSA"
        assert address.full_address == expected_full

    def test_address_with_apartment(self):
        """Test address with apartment number."""
        address = Address(
            street="123 Main St",
            city="Anytown",
            state="CA",
            postal_code="12345",
            country="USA",
            apartment="4B",
        )

        expected_full = "123 Main St\nApt 4B\nAnytown, CA 12345\nUSA"
        assert address.full_address == expected_full

    def test_empty_fields_raise_error(self):
        """Test that empty required fields raise ValueError."""
        with pytest.raises(ValueError, match="Street cannot be empty"):
            Address("", "City", "State", "12345", "Country")

        with pytest.raises(ValueError, match="City cannot be empty"):
            Address("Street", "", "State", "12345", "Country")


class TestPhoneNumber:
    """Test cases for PhoneNumber value object."""

    def test_valid_phone_creation(self):
        """Test creating a valid phone number."""
        phone = PhoneNumber("555-123-4567")
        assert phone.value == "555-123-4567"
        assert phone.country_code == "+1"
        assert phone.digits_only == "5551234567"
        assert phone.formatted == "(555) 123-4567"

    def test_phone_with_custom_country_code(self):
        """Test phone with custom country code."""
        phone = PhoneNumber("1234567890", "+44")
        assert phone.country_code == "+44"
        assert phone.formatted == "+44 1234567890"

    def test_invalid_phone_length_raises_error(self):
        """Test that invalid phone length raises ValueError."""
        with pytest.raises(ValueError, match="must have at least 10 digits"):
            PhoneNumber("123456789")  # Too short

        with pytest.raises(ValueError, match="cannot have more than 15 digits"):
            PhoneNumber("1234567890123456")  # Too long


class TestStronglyTypedIds:
    """Test cases for strongly typed identifiers."""

    def test_customer_id_creation(self):
        """Test creating a customer ID."""
        uuid_val = uuid4()
        customer_id = CustomerId(uuid_val)

        assert customer_id.value == uuid_val
        assert str(customer_id) == str(uuid_val)

    def test_order_id_creation(self):
        """Test creating an order ID."""
        uuid_val = uuid4()
        order_id = OrderId(uuid_val)

        assert order_id.value == uuid_val
        assert str(order_id) == str(uuid_val)

    def test_different_id_types_are_different(self):
        """Test that different ID types are distinct."""
        uuid_val = uuid4()
        customer_id = CustomerId(uuid_val)
        order_id = OrderId(uuid_val)

        # Even with same UUID, they should be different types
        assert not isinstance(customer_id, type(order_id))
        assert customer_id != order_id  # Value objects compare by all attributes
