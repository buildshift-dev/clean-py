"""Common exceptions for the shared kernel."""

from .domain_exceptions import (
    BusinessRuleViolationError,
    DomainError,
    ResourceNotFoundError,
)

__all__ = [
    "DomainError",
    "BusinessRuleViolationError",
    "ResourceNotFoundError",
]
