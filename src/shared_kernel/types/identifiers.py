"""Strongly typed identifiers."""

from dataclasses import dataclass
from uuid import UUID

from ..base.value_object import ValueObject


@dataclass(frozen=True)
class CustomerId(ValueObject):
    """Strongly typed customer identifier."""

    value: UUID

    def validate(self) -> None:
        """Validate customer ID."""
        # Type is guaranteed by annotation, no validation needed
        pass

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class OrderId(ValueObject):
    """Strongly typed order identifier."""

    value: UUID

    def validate(self) -> None:
        """Validate order ID."""
        # Type is guaranteed by annotation, no validation needed
        pass

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class ProductId(ValueObject):
    """Strongly typed product identifier."""

    value: UUID

    def validate(self) -> None:
        """Validate product ID."""
        # Type is guaranteed by annotation, no validation needed
        pass

    def __str__(self) -> str:
        return str(self.value)
