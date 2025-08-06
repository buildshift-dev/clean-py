"""Email value object."""

import re
from dataclasses import dataclass

from ..base.value_object import ValueObject


@dataclass(frozen=True)
class Email(ValueObject):
    """Email address value object with validation."""

    value: str

    def validate(self) -> None:
        """Validate email format."""
        if not self.value:
            raise ValueError("Email cannot be empty")

        # Basic email validation regex
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, self.value):
            raise ValueError(f"Invalid email format: {self.value}")

    @property
    def domain(self) -> str:
        """Get the domain part of the email."""
        return self.value.split("@")[1]

    @property
    def local_part(self) -> str:
        """Get the local part of the email."""
        return self.value.split("@")[0]

    def __str__(self) -> str:
        return self.value
