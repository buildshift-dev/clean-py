"""Tests for correlation ID management."""

from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response

from src.infrastructure.logging.correlation import (
    CorrelationContext,
    CorrelationMiddleware,
    correlation_id_var,
    get_correlation_id,
)


class TestCorrelationContext:
    """Test CorrelationContext functionality."""

    def test_get_set_correlation_id(self):
        """Test getting and setting correlation ID."""
        # Initially should be None
        assert CorrelationContext.get() is None

        # Set a correlation ID
        test_id = "test-correlation-id"
        CorrelationContext.set(test_id)

        # Should retrieve the same ID
        assert CorrelationContext.get() == test_id

    def test_generate_correlation_id(self):
        """Test correlation ID generation."""
        id1 = CorrelationContext.generate()
        id2 = CorrelationContext.generate()

        # Should generate unique IDs
        assert id1 != id2
        assert len(id1) == 36  # UUID format
        assert len(id2) == 36

    def test_extract_from_request_standard_headers(self):
        """Test extracting correlation ID from standard headers."""
        # Mock request with X-Correlation-ID header
        request = Mock(spec=Request)
        request.headers = {"X-Correlation-ID": "test-id-1"}

        correlation_id = CorrelationContext.extract_from_request(request)
        assert correlation_id == "test-id-1"

    def test_extract_from_request_multiple_headers(self):
        """Test extraction priority from multiple header types."""
        # Test X-Request-ID when X-Correlation-ID is not present
        request = Mock(spec=Request)
        request.headers = {"X-Request-ID": "test-id-2"}

        correlation_id = CorrelationContext.extract_from_request(request)
        assert correlation_id == "test-id-2"

        # Test that X-Correlation-ID takes priority
        request.headers = {
            "X-Correlation-ID": "primary-id",
            "X-Request-ID": "secondary-id",
        }

        correlation_id = CorrelationContext.extract_from_request(request)
        assert correlation_id == "primary-id"

    def test_extract_from_request_aws_headers(self):
        """Test extracting from AWS-specific headers."""
        request = Mock(spec=Request)
        request.headers = {"X-Amzn-Trace-Id": "aws-trace-id"}

        correlation_id = CorrelationContext.extract_from_request(request)
        assert correlation_id == "aws-trace-id"

    def test_extract_from_request_no_headers(self):
        """Test extraction when no relevant headers are present."""
        request = Mock(spec=Request)
        request.headers = {"User-Agent": "test", "Content-Type": "application/json"}

        correlation_id = CorrelationContext.extract_from_request(request)
        assert correlation_id is None

    def test_inject_to_response(self):
        """Test injecting correlation ID into response headers."""
        response = Response()
        test_id = "response-correlation-id"

        CorrelationContext.inject_to_response(response, test_id)

        assert response.headers["X-Correlation-ID"] == test_id


class TestCorrelationMiddleware:
    """Test CorrelationMiddleware functionality."""

    @pytest.fixture
    def app(self) -> Starlette:
        """Create a test Starlette app."""
        app = Starlette()

        @app.route("/test")  # pyright: ignore[reportUntypedFunctionDecorator]
        async def test_endpoint(request: Request) -> Response:  # pyright: ignore[reportUnusedFunction]
            # Check that correlation ID is available
            correlation_id = CorrelationContext.get()
            return Response(content=correlation_id or "no-correlation-id", media_type="text/plain")

        return app

    @pytest.fixture
    def middleware_app(self, app: Starlette) -> Starlette:
        """Create app with correlation middleware."""
        app.add_middleware(CorrelationMiddleware)
        return app

    @pytest.mark.asyncio
    async def test_middleware_generates_correlation_id(self, middleware_app: Starlette) -> None:
        """Test that middleware generates correlation ID when none exists."""
        from starlette.testclient import TestClient

        client = TestClient(middleware_app)
        response = client.get("/test")

        assert response.status_code == 200
        assert len(response.text) == 36  # UUID format
        assert "X-Correlation-ID" in response.headers
        assert response.headers["X-Correlation-ID"] == response.text

    @pytest.mark.asyncio
    async def test_middleware_uses_existing_correlation_id(self, middleware_app: Starlette) -> None:
        """Test that middleware uses existing correlation ID from headers."""
        from starlette.testclient import TestClient

        existing_id = "existing-correlation-id"
        client = TestClient(middleware_app)
        response = client.get("/test", headers={"X-Correlation-ID": existing_id})

        assert response.status_code == 200
        assert response.text == existing_id
        assert response.headers["X-Correlation-ID"] == existing_id

    @pytest.mark.asyncio
    async def test_middleware_sets_request_state(self):
        """Test that middleware sets correlation ID in request state."""
        # Create mock request and call_next
        request = Mock(spec=Request)
        request.headers = {}
        request.state = Mock()

        call_next = AsyncMock()
        call_next.return_value = Response()

        middleware = CorrelationMiddleware(Mock())

        await middleware.dispatch(request, call_next)

        # Verify correlation ID was set in request state
        assert hasattr(request.state, "correlation_id")
        assert len(request.state.correlation_id) == 36  # UUID format

    @pytest.mark.asyncio
    async def test_middleware_context_isolation(self):
        """Test that correlation IDs are properly isolated between requests."""
        app = Starlette()
        correlation_ids = []

        @app.route("/capture")  # pyright: ignore[reportUntypedFunctionDecorator]
        async def capture_endpoint(request: Request) -> Response:  # pyright: ignore[reportUnusedFunction]
            correlation_id = CorrelationContext.get()
            correlation_ids.append(correlation_id)
            return Response(content="ok")

        app.add_middleware(CorrelationMiddleware)

        from starlette.testclient import TestClient

        client = TestClient(app)

        # Make multiple requests
        for _i in range(3):
            response = client.get("/capture")
            assert response.status_code == 200

        # Verify all correlation IDs are different
        assert len(correlation_ids) == 3
        assert len(set(correlation_ids)) == 3  # All unique


class TestGetCorrelationId:
    """Test get_correlation_id dependency function."""

    def test_get_correlation_id_existing(self):
        """Test getting existing correlation ID."""
        test_id = "existing-id"
        CorrelationContext.set(test_id)

        result = get_correlation_id()
        assert result == test_id

    def test_get_correlation_id_generates_new(self):
        """Test generating new correlation ID when none exists."""
        # Ensure no correlation ID is set
        correlation_id_var.set(None)

        result = get_correlation_id()

        # Should generate and return new ID
        assert result is not None
        assert len(result) == 36  # UUID format

        # Should also set it in context
        assert CorrelationContext.get() == result


class TestCorrelationIntegration:
    """Integration tests for correlation functionality."""

    @pytest.mark.asyncio
    async def test_correlation_propagation_through_middleware(self):
        """Test correlation ID propagation through multiple middleware layers."""
        app = Starlette()
        captured_ids = []

        # Custom middleware to capture correlation ID
        class CaptureMiddleware:
            def __init__(self, app: Any) -> None:
                self.app = app

            async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
                if scope["type"] == "http":
                    # Capture correlation ID at middleware level
                    correlation_id = CorrelationContext.get()
                    captured_ids.append(("middleware", correlation_id))

                await self.app(scope, receive, send)

        @app.route("/test")  # pyright: ignore[reportUntypedFunctionDecorator]
        async def test_endpoint(request: Request) -> Response:  # pyright: ignore[reportUnusedFunction]
            # Capture correlation ID at endpoint level
            correlation_id = CorrelationContext.get()
            captured_ids.append(("endpoint", correlation_id))
            return Response(content="ok")

        # Add middlewares (reverse order due to LIFO)
        app.add_middleware(CaptureMiddleware)
        app.add_middleware(CorrelationMiddleware)

        from starlette.testclient import TestClient

        client = TestClient(app)

        response = client.get("/test", headers={"X-Correlation-ID": "test-propagation"})

        assert response.status_code == 200
        assert len(captured_ids) == 2

        # Both middleware and endpoint should see the same correlation ID
        middleware_id = captured_ids[0][1]
        endpoint_id = captured_ids[1][1]

        assert middleware_id == "test-propagation"
        assert endpoint_id == "test-propagation"

    def test_correlation_context_cleanup(self):
        """Test that correlation context is properly cleaned up."""
        # Set a correlation ID
        CorrelationContext.set("cleanup-test")
        assert CorrelationContext.get() == "cleanup-test"

        # Clear the context (simulating request cleanup)
        correlation_id_var.set(None)
        assert CorrelationContext.get() is None

    def test_multiple_header_priority(self):
        """Test header priority order for correlation ID extraction."""
        request = Mock(spec=Request)

        # Test all headers present - should use highest priority
        request.headers = {
            "X-Correlation-ID": "priority-1",
            "X-Request-ID": "priority-2",
            "X-Trace-ID": "priority-3",
            "X-Amzn-Trace-Id": "priority-4",
            "AWS-Request-ID": "priority-5",
        }

        correlation_id = CorrelationContext.extract_from_request(request)
        assert correlation_id == "priority-1"

        # Remove highest priority, should fall back
        del request.headers["X-Correlation-ID"]
        correlation_id = CorrelationContext.extract_from_request(request)
        assert correlation_id == "priority-2"
