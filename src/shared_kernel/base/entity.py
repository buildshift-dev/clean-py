"""Base Entity class for domain model."""

from abc import ABC
from dataclasses import dataclass
from uuid import UUID


@dataclass
class Entity(ABC):
    """
    Base class for all entities.

    An entity has a unique identity that persists through state changes.
    Equality is based on identity, not attributes.
    """

    id: UUID

    def __eq__(self, other: object) -> bool:
        """Entities are equal if they have the same ID."""
        if not isinstance(other, Entity):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        """Hash based on identity."""
        return hash(self.id)
