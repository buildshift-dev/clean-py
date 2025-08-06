"""Phone number value object."""

import re
from dataclasses import dataclass

from ..base.value_object import ValueObject


@dataclass(frozen=True)
class PhoneNumber(ValueObject):
    """Phone number value object with validation."""

    value: str
    country_code: str = "+1"  # Default to US

    def validate(self) -> None:
        """Validate phone number format."""
        if not self.value:
            raise ValueError("Phone number cannot be empty")

        if not self.country_code:
            raise ValueError("Country code cannot be empty")

        # Remove all non-digit characters for validation
        digits_only = re.sub(r"\D", "", self.value)

        if len(digits_only) < 10:
            raise ValueError("Phone number must have at least 10 digits")

        if len(digits_only) > 15:
            raise ValueError("Phone number cannot have more than 15 digits")

        # Validate country code format
        if not self.country_code.startswith("+"):
            raise ValueError("Country code must start with +")

        country_digits = re.sub(r"\D", "", self.country_code)
        if not country_digits:
            raise ValueError("Country code must contain digits")

    @property
    def formatted(self) -> str:
        """Get formatted phone number."""
        digits_only = re.sub(r"\D", "", self.value)

        if len(digits_only) == 10 and self.country_code == "+1":
            # US format: (xxx) xxx-xxxx
            return f"({digits_only[:3]}) {digits_only[3:6]}-{digits_only[6:]}"
        # International format with country code
        return f"{self.country_code} {self.value}"

    @property
    def digits_only(self) -> str:
        """Get only the digits from the phone number."""
        return re.sub(r"\D", "", self.value)

    def __str__(self) -> str:
        return self.formatted
