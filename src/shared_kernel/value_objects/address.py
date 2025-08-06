"""Address value object."""

from dataclasses import dataclass

from ..base.value_object import ValueObject


@dataclass(frozen=True)
class Address(ValueObject):
    """Physical address value object."""

    street: str
    city: str
    state: str
    postal_code: str
    country: str
    apartment: str | None = None

    def validate(self) -> None:
        """Validate address fields."""
        if not self.street.strip():
            raise ValueError("Street cannot be empty")

        if not self.city.strip():
            raise ValueError("City cannot be empty")

        if not self.state.strip():
            raise ValueError("State cannot be empty")

        if not self.postal_code.strip():
            raise ValueError("Postal code cannot be empty")

        if not self.country.strip():
            raise ValueError("Country cannot be empty")

        # Basic postal code validation (flexible format)
        if len(self.postal_code) < 3:
            raise ValueError("Postal code too short")

    @property
    def full_address(self) -> str:
        """Get formatted full address."""
        address_parts = [self.street]

        if self.apartment:
            address_parts.append(f"Apt {self.apartment}")

        address_parts.extend([f"{self.city}, {self.state} {self.postal_code}", self.country])

        return "\n".join(address_parts)

    def __str__(self) -> str:
        return self.full_address
