"""Base Domain Event class."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class DomainEvent:
    """
    Base class for domain events.

    Domain events represent something significant that happened in the domain.
    They are immutable and carry all information about what occurred.
    """

    event_id: UUID
    occurred_at: datetime

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            "event_type": self.__class__.__name__,
            "event_id": str(self.event_id),
            "occurred_at": self.occurred_at.isoformat(),
            **{k: v for k, v in self.__dict__.items() if k not in ["event_id", "occurred_at"]},
        }
