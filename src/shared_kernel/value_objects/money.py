"""Money value object."""

from dataclasses import dataclass
from decimal import Decimal

from ..base.value_object import ValueObject


@dataclass(frozen=True)
class Money(ValueObject):
    """Money value object with currency and amount."""

    amount: Decimal
    currency: str

    def validate(self) -> None:
        """Validate money constraints."""
        # Type is guaranteed by annotation

        if self.amount < 0:
            raise ValueError("Amount cannot be negative")

        if not self.currency:
            raise ValueError("Currency cannot be empty")

        # Basic currency code validation (3 uppercase letters)
        if len(self.currency) != 3 or not self.currency.isupper():
            raise ValueError(f"Invalid currency code: {self.currency}")

    def add(self, other: "Money") -> "Money":
        """Add two money amounts (must have same currency)."""
        if self.currency != other.currency:
            raise ValueError(f"Cannot add different currencies: {self.currency} and {other.currency}")

        return Money(amount=self.amount + other.amount, currency=self.currency)

    def subtract(self, other: "Money") -> "Money":
        """Subtract two money amounts (must have same currency)."""
        if self.currency != other.currency:
            raise ValueError(f"Cannot subtract different currencies: {self.currency} and {other.currency}")

        result_amount = self.amount - other.amount
        if result_amount < 0:
            raise ValueError("Subtraction would result in negative amount")

        return Money(amount=result_amount, currency=self.currency)

    def multiply(self, factor: int | Decimal) -> "Money":
        """Multiply money by a factor."""
        # Type is guaranteed by annotation

        if factor < 0:
            raise ValueError("Factor cannot be negative")

        return Money(amount=self.amount * Decimal(str(factor)), currency=self.currency)

    def __str__(self) -> str:
        return f"{self.amount} {self.currency}"
