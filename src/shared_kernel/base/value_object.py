"""Base Value Object class for domain model."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class ValueObject(ABC):
    """
    Base class for value objects.

    Value objects are immutable and defined by their attributes.
    They have no identity and are equal if all their attributes are equal.
    """

    def __post_init__(self) -> None:
        """Validate after initialization."""
        self.validate()

    @abstractmethod
    def validate(self) -> None:
        """
        Override in subclasses to add validation logic.

        Should raise ValueError with descriptive message if invalid.
        """
        ...
