"""Domain-specific exceptions."""


class DomainError(Exception):
    """Base exception for domain-specific errors."""

    def __init__(self, message: str, error_code: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code


class BusinessRuleViolationError(DomainError):
    """Raised when a business rule is violated."""

    def __init__(self, message: str, rule_name: str | None = None) -> None:
        super().__init__(message, "BUSINESS_RULE_VIOLATION")
        self.rule_name = rule_name


class ResourceNotFoundError(DomainError):
    """Raised when a requested resource is not found."""

    def __init__(self, resource_type: str, resource_id: str) -> None:
        message = f"{resource_type} with ID {resource_id} not found"
        super().__init__(message, "RESOURCE_NOT_FOUND")
        self.resource_type = resource_type
        self.resource_id = resource_id
