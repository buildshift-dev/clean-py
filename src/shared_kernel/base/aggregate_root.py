"""Base Aggregate Root class."""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .entity import Entity

if TYPE_CHECKING:
    from .domain_event import DomainEvent


@dataclass
class AggregateRoot(Entity):
    """
    Base class for aggregate roots.

    Aggregate roots are the entry point to an aggregate and maintain consistency
    boundaries. They can raise domain events.
    """

    _domain_events: list["DomainEvent"] = field(default_factory=list, init=False, repr=False)

    def add_domain_event(self, event: "DomainEvent") -> None:
        """Add a domain event to this aggregate."""
        self._domain_events.append(event)

    def collect_domain_events(self) -> list["DomainEvent"]:
        """
        Collect and clear domain events.

        Used by infrastructure to get events for publishing after persistence.
        """
        events = self._domain_events.copy()
        self._domain_events.clear()
        return events

    def clear_domain_events(self) -> None:
        """Clear domain events without collecting."""
        self._domain_events.clear()
