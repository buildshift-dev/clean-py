"""Specification pattern for complex queries."""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")


class Specification(ABC, Generic[T]):
    """
    Base specification for complex queries.

    Specifications encapsulate business rules that can be combined
    and used for querying or validation.
    """

    @abstractmethod
    def is_satisfied_by(self, candidate: T) -> bool:
        """Check if the candidate satisfies this specification."""
        ...

    def and_(self, other: "Specification[T]") -> "AndSpecification[T]":
        """Combine with another specification using AND."""
        return AndSpecification(self, other)

    def or_(self, other: "Specification[T]") -> "OrSpecification[T]":
        """Combine with another specification using OR."""
        return OrSpecification(self, other)

    def not_(self) -> "NotSpecification[T]":
        """Negate this specification."""
        return NotSpecification(self)


class AndSpecification(Specification[T]):
    """Specification that requires both specifications to be satisfied."""

    def __init__(self, left: Specification[T], right: Specification[T]) -> None:
        self.left = left
        self.right = right

    def is_satisfied_by(self, candidate: T) -> bool:
        return self.left.is_satisfied_by(candidate) and self.right.is_satisfied_by(candidate)


class OrSpecification(Specification[T]):
    """Specification that requires at least one specification to be satisfied."""

    def __init__(self, left: Specification[T], right: Specification[T]) -> None:
        self.left = left
        self.right = right

    def is_satisfied_by(self, candidate: T) -> bool:
        return self.left.is_satisfied_by(candidate) or self.right.is_satisfied_by(candidate)


class NotSpecification(Specification[T]):
    """Specification that negates another specification."""

    def __init__(self, spec: Specification[T]) -> None:
        self.spec = spec

    def is_satisfied_by(self, candidate: T) -> bool:
        return not self.spec.is_satisfied_by(candidate)
