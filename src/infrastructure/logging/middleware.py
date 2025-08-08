"""FastAPI middleware for request/response logging."""

import time
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from .config import get_log_config
from .correlation import CorrelationContext
from .logger import get_logger


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for comprehensive request/response logging.

    Provides structured logging of HTTP requests with performance metrics,
    correlation tracking, and configurable data logging.
    """

    def __init__(
        self,
        app: ASGIApp,
        logger_name: str = "api.requests",
        skip_paths: set[str] | None = None,
        skip_health_checks: bool = True,
        log_request_body: bool = False,
        log_response_body: bool = False,
        sensitive_headers: set[str] | None = None,
        max_body_size: int = 10000,
    ) -> None:
        """
        Initialize logging middleware.

        Args:
            app: FastAPI application instance
            logger_name: Logger name for request logs
            skip_paths: Set of paths to skip logging (exact matches)
            skip_health_checks: Skip common health check endpoints
            log_request_body: Log request body content
            log_response_body: Log response body content
            sensitive_headers: Headers to redact from logs
            max_body_size: Maximum body size to log (bytes)
        """
        super().__init__(app)
        self.logger = get_logger(logger_name)
        self.config = get_log_config()

        # Configure which paths to skip
        self.skip_paths = skip_paths or set()
        if skip_health_checks:
            self.skip_paths.update(
                {
                    "/health",
                    "/healthz",
                    "/health/ready",
                    "/health/live",
                    "/ping",
                    "/status",
                    "/metrics",
                }
            )

        # Configure data logging
        self.log_request_body = log_request_body or self.config.log_request_body
        self.log_response_body = log_response_body or self.config.log_response_body
        self.max_body_size = max_body_size

        # Configure header filtering
        default_sensitive_headers = {
            "authorization",
            "cookie",
            "x-api-key",
            "x-auth-token",
            "x-access-token",
            "x-csrf-token",
        }
        self.sensitive_headers = (sensitive_headers or set()) | default_sensitive_headers

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process HTTP request with comprehensive logging.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware in chain

        Returns:
            Response: HTTP response
        """
        # Skip logging for configured paths
        if request.url.path in self.skip_paths:
            return await call_next(request)

        # Start timing
        start_time = time.perf_counter()

        # Get or generate correlation ID
        correlation_id = CorrelationContext.get() or request.state.__dict__.get("correlation_id")

        # Prepare request context
        request_context = await self._build_request_context(request, correlation_id)

        # Log request
        self.logger.info(
            f"{request.method} {request.url.path}",
            extra={
                "event_type": "request_started",
                **request_context,
            },
        )

        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            # Log error but let it propagate
            self.logger.error(
                f"Request failed: {request.method} {request.url.path}",
                extra={
                    "event_type": "request_error",
                    "error": str(e),
                    **request_context,
                },
                exc_info=True,
            )
            raise

        # Calculate timing
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # Build response context
        response_context = await self._build_response_context(response, duration_ms, request_context)

        # Log response
        log_level = self._get_response_log_level(response.status_code, duration_ms)
        self.logger.log(
            log_level,
            f"{request.method} {request.url.path} - {response.status_code}",
            extra={
                "event_type": "request_completed",
                **response_context,
            },
        )

        return response

    async def _build_request_context(self, request: Request, correlation_id: str | None) -> dict:
        """
        Build structured context for request logging.

        Args:
            request: HTTP request
            correlation_id: Request correlation ID

        Returns:
            Dict: Request logging context
        """
        # Basic request info
        context = {
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "client_ip": self._get_client_ip(request),
            "user_agent": request.headers.get("user-agent"),
            "content_type": request.headers.get("content-type"),
            "content_length": request.headers.get("content-length"),
        }

        # Add correlation ID
        if correlation_id:
            context["correlation_id"] = correlation_id

        # Add filtered headers
        context["headers"] = self._filter_headers(dict(request.headers))

        # Add request body if configured
        if self.log_request_body and request.method in {"POST", "PUT", "PATCH"}:
            body = await self._get_request_body(request)
            if body:
                context["request_body"] = body

        return context

    async def _build_response_context(self, response: Response, duration_ms: float, request_context: dict) -> dict:
        """
        Build structured context for response logging.

        Args:
            response: HTTP response
            duration_ms: Request duration in milliseconds
            request_context: Original request context

        Returns:
            Dict: Response logging context
        """
        # Merge request context with response info
        context = {
            **request_context,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
            "response_size": response.headers.get("content-length"),
        }

        # Add response headers
        context["response_headers"] = self._filter_headers(dict(response.headers))

        # Add response body if configured and appropriate
        if (
            self.log_response_body
            and response.status_code >= 400  # Only log error responses by default
            and hasattr(response, "body")
        ):
            body = await self._get_response_body(response)
            if body:
                context["response_body"] = body

        return context

    def _get_client_ip(self, request: Request) -> str | None:
        """
        Extract client IP address from request.

        Args:
            request: HTTP request

        Returns:
            Optional[str]: Client IP address
        """
        # Check common proxy headers
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        # AWS ALB header
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()

        # Fallback to client address if available
        if hasattr(request, "client") and request.client:
            return request.client.host

        return None

    def _filter_headers(self, headers: dict[str, str]) -> dict[str, str]:
        """
        Filter sensitive headers from logs.

        Args:
            headers: Raw headers dictionary

        Returns:
            Dict[str, str]: Filtered headers
        """
        filtered = {}
        for key, value in headers.items():
            if key.lower() in self.sensitive_headers:
                filtered[key] = "[REDACTED]"
            else:
                filtered[key] = value
        return filtered

    async def _get_request_body(self, request: Request) -> str | None:
        """
        Extract request body for logging.

        Args:
            request: HTTP request

        Returns:
            Optional[str]: Request body content (truncated if too large)
        """
        try:
            body = await request.body()
            if not body:
                return None

            # Check size limit
            if len(body) > self.max_body_size:
                return f"[TRUNCATED - {len(body)} bytes]"

            # Try to decode as text
            try:
                return body.decode("utf-8")
            except UnicodeDecodeError:
                return f"[BINARY DATA - {len(body)} bytes]"

        except Exception as e:
            self.logger.debug(f"Failed to read request body: {e}")
            return None

    async def _get_response_body(self, response: Response) -> str | None:
        """
        Extract response body for logging.

        Args:
            response: HTTP response

        Returns:
            Optional[str]: Response body content (truncated if too large)
        """
        try:
            if not hasattr(response, "body") or not response.body:
                return None

            body = response.body
            if isinstance(body, bytes):
                # Check size limit
                if len(body) > self.max_body_size:
                    return f"[TRUNCATED - {len(body)} bytes]"

                # Try to decode as text
                try:
                    return body.decode("utf-8")
                except UnicodeDecodeError:
                    return f"[BINARY DATA - {len(body)} bytes]"

            return str(body)

        except Exception as e:
            self.logger.debug(f"Failed to read response body: {e}")
            return None

    def _get_response_log_level(self, status_code: int, duration_ms: float) -> int:
        """
        Determine appropriate log level for response.

        Args:
            status_code: HTTP status code
            duration_ms: Request duration in milliseconds

        Returns:
            int: Python logging level
        """
        import logging

        # Errors get ERROR level
        if status_code >= 500:
            return logging.ERROR

        # Client errors get WARNING level
        if status_code >= 400:
            return logging.WARNING

        # Slow requests get WARNING level
        if duration_ms > self.config.slow_request_threshold_ms:
            return logging.WARNING

        # Everything else gets INFO level
        return logging.INFO
