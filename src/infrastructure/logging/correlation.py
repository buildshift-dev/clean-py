"""Correlation ID management for distributed tracing."""

import uuid
from contextvars import ContextVar
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Context variable for storing correlation ID throughout the request lifecycle
correlation_id_var: ContextVar[str | None] = ContextVar("correlation_id", default=None)


class CorrelationContext:
    """Manages correlation IDs for request tracing."""

    CORRELATION_ID_HEADER = "X-Correlation-ID"
    REQUEST_ID_HEADER = "X-Request-ID"
    TRACE_ID_HEADER = "X-Trace-ID"

    # AWS specific headers
    AWS_TRACE_ID_HEADER = "X-Amzn-Trace-Id"
    AWS_REQUEST_ID_HEADER = "AWS-Request-ID"

    @staticmethod
    def get() -> str | None:
        """
        Get the current correlation ID.

        Returns:
            Optional[str]: Current correlation ID or None
        """
        return correlation_id_var.get()

    @staticmethod
    def set(correlation_id: str | None) -> None:
        """
        Set the correlation ID for the current context.

        Args:
            correlation_id: Correlation ID to set
        """
        correlation_id_var.set(correlation_id)

    @staticmethod
    def generate() -> str:
        """
        Generate a new correlation ID.

        Returns:
            str: New UUID-based correlation ID
        """
        return str(uuid.uuid4())

    @staticmethod
    def extract_from_request(request: Request) -> str | None:
        """
        Extract correlation ID from request headers.

        Checks multiple header names for compatibility with different systems.

        Args:
            request: Incoming HTTP request

        Returns:
            Optional[str]: Extracted correlation ID or None
        """
        # Check various header names in order of preference
        headers_to_check = [
            CorrelationContext.CORRELATION_ID_HEADER,
            CorrelationContext.REQUEST_ID_HEADER,
            CorrelationContext.TRACE_ID_HEADER,
            CorrelationContext.AWS_TRACE_ID_HEADER,
            CorrelationContext.AWS_REQUEST_ID_HEADER,
        ]

        for header in headers_to_check:
            correlation_id = request.headers.get(header)
            if correlation_id:
                return correlation_id

        return None

    @staticmethod
    def inject_to_response(response: Response, correlation_id: str) -> None:
        """
        Inject correlation ID into response headers.

        Args:
            response: HTTP response object
            correlation_id: Correlation ID to inject
        """
        response.headers[CorrelationContext.CORRELATION_ID_HEADER] = correlation_id


class CorrelationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for managing correlation IDs across HTTP requests.

    Automatically extracts or generates correlation IDs for each request
    and ensures they're propagated through the response.
    """

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        """
        Process the request with correlation ID management.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware in the chain

        Returns:
            Response with correlation ID header
        """
        # Extract or generate correlation ID
        correlation_id = CorrelationContext.extract_from_request(request)
        if not correlation_id:
            correlation_id = CorrelationContext.generate()

        # Set correlation ID in context
        CorrelationContext.set(correlation_id)

        # Store in request state for access in route handlers
        request.state.correlation_id = correlation_id

        # Process request
        response = await call_next(request)

        # Add correlation ID to response headers
        CorrelationContext.inject_to_response(response, correlation_id)

        return response


# Convenience function for FastAPI dependency injection
def get_correlation_id() -> str:
    """
    Get current correlation ID for use in FastAPI dependencies.

    Returns:
        str: Current correlation ID or new one if not set
    """
    correlation_id = CorrelationContext.get()
    if not correlation_id:
        correlation_id = CorrelationContext.generate()
        CorrelationContext.set(correlation_id)
    return correlation_id


# Alias for backward compatibility
correlation_middleware = CorrelationMiddleware
