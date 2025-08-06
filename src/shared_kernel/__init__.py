"""Shared kernel containing common domain concepts and base classes."""

# Base classes
from .base.aggregate_root import AggregateRoot
from .base.domain_event import DomainEvent
from .base.entity import Entity
from .base.specification import Specification
from .base.value_object import ValueObject

# Common exceptions
from .exceptions.domain_exceptions import (
    BusinessRuleViolationError,
    DomainError,
    ResourceNotFoundError,
)

# Common types
from .types.identifiers import CustomerId, OrderId, ProductId
from .value_objects.address import Address

# Common value objects
from .value_objects.email import Email
from .value_objects.money import Money
from .value_objects.phone_number import PhoneNumber

__all__ = [
    # Base classes
    "Entity",
    "ValueObject",
    "AggregateRoot",
    "DomainEvent",
    "Specification",
    # Common value objects
    "Email",
    "Money",
    "Address",
    "PhoneNumber",
    # Common types
    "CustomerId",
    "OrderId",
    "ProductId",
    # Common exceptions
    "DomainError",
    "BusinessRuleViolationError",
    "ResourceNotFoundError",
]
