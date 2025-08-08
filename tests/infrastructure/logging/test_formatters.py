"""Tests for log formatters."""

import json
import logging
import sys
from typing import Any
from unittest.mock import patch

from src.infrastructure.logging.correlation import CorrelationContext
from src.infrastructure.logging.formatters import (
    CloudWatchFormatter,
    ConsoleFormatter,
    StructuredFormatter,
)


class TestStructuredFormatter:
    """Test StructuredFormatter functionality."""

    def test_basic_log_formatting(self):
        """Test basic log record formatting."""
        formatter = StructuredFormatter(service_name="test-service", version="1.0.0", environment="test")

        # Create a log record
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        # Format the record
        formatted = formatter.format(record)
        parsed = json.loads(formatted)

        # Verify basic structure
        assert parsed["level"] == "INFO"
        assert parsed["logger"] == "test.logger"
        assert parsed["message"] == "Test message"
        assert parsed["service"] == "test-service"
        assert parsed["version"] == "1.0.0"
        assert parsed["environment"] == "test"
        assert "timestamp" in parsed
        assert "source" in parsed
        assert parsed["source"]["file"] == "/test/path.py"
        assert parsed["source"]["line"] == 42

    def test_correlation_id_inclusion(self):
        """Test correlation ID inclusion in formatted logs."""
        formatter = StructuredFormatter()

        # Set correlation ID
        test_correlation_id = "test-correlation-123"
        CorrelationContext.set(test_correlation_id)

        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="/test.py", lineno=1, msg="Test", args=(), exc_info=None
        )

        formatted = formatter.format(record)
        parsed = json.loads(formatted)

        assert parsed["correlation_id"] == test_correlation_id

        # Clean up
        CorrelationContext.set(None)

    def test_exception_formatting(self):
        """Test exception information formatting."""
        formatter = StructuredFormatter()

        # Create exception info
        try:
            raise ValueError("Test exception")
        except ValueError:
            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="/test.py",
            lineno=1,
            msg="Error occurred",
            args=(),
            exc_info=exc_info,
        )

        formatted = formatter.format(record)
        parsed = json.loads(formatted)

        assert "exception" in parsed
        assert parsed["exception"]["type"] == "ValueError"
        assert parsed["exception"]["message"] == "Test exception"
        assert isinstance(parsed["exception"]["traceback"], list)
        assert len(parsed["exception"]["traceback"]) > 0

    def test_extra_fields_handling(self):
        """Test handling of extra fields in log records."""
        formatter = StructuredFormatter()

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="/test.py",
            lineno=1,
            msg="Test with extras",
            args=(),
            exc_info=None,
        )

        # Add extra fields
        record.user_id = "user123"
        record.operation = "create_order"
        record.duration_ms = 250.5
        record.metadata = {"key": "value"}

        formatted = formatter.format(record)
        parsed = json.loads(formatted)

        assert "extra" in parsed
        assert parsed["extra"]["user_id"] == "user123"
        assert parsed["extra"]["operation"] == "create_order"
        assert parsed["extra"]["duration_ms"] == 250.5
        assert parsed["extra"]["metadata"] == {"key": "value"}

    def test_hostname_inclusion(self):
        """Test hostname inclusion when enabled."""
        formatter = StructuredFormatter(include_hostname=True)

        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="/test.py", lineno=1, msg="Test", args=(), exc_info=None
        )

        formatted = formatter.format(record)
        parsed = json.loads(formatted)

        assert "hostname" in parsed
        assert isinstance(parsed["hostname"], str)
        assert len(parsed["hostname"]) > 0

    def test_hostname_exclusion(self):
        """Test hostname exclusion when disabled."""
        formatter = StructuredFormatter(include_hostname=False)

        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="/test.py", lineno=1, msg="Test", args=(), exc_info=None
        )

        formatted = formatter.format(record)
        parsed = json.loads(formatted)

        assert "hostname" not in parsed

    def test_process_info_inclusion(self):
        """Test process info inclusion when enabled."""
        formatter = StructuredFormatter(include_process_info=True)

        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="/test.py", lineno=1, msg="Test", args=(), exc_info=None
        )

        formatted = formatter.format(record)
        parsed = json.loads(formatted)

        assert "process" in parsed
        assert "pid" in parsed["process"]
        assert "thread_id" in parsed["process"]
        assert "thread_name" in parsed["process"]

    def test_process_info_exclusion(self):
        """Test process info exclusion when disabled."""
        formatter = StructuredFormatter(include_process_info=False)

        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="/test.py", lineno=1, msg="Test", args=(), exc_info=None
        )

        formatted = formatter.format(record)
        parsed = json.loads(formatted)

        assert "process" not in parsed


class TestCloudWatchFormatter:
    """Test CloudWatchFormatter functionality."""

    def test_basic_cloudwatch_formatting(self):
        """Test basic CloudWatch log formatting."""
        formatter = CloudWatchFormatter(service_name="test-service", environment="production")

        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/test.py",
            lineno=42,
            msg="CloudWatch test message",
            args=(),
            exc_info=None,
        )

        formatted = formatter.format(record)
        parsed = json.loads(formatted)

        # Verify CloudWatch-specific structure
        assert parsed["@level"] == "INFO"
        assert parsed["@logger"] == "test.logger"
        assert parsed["@message"] == "CloudWatch test message"
        assert parsed["service"] == "test-service"
        assert parsed["env"] == "production"
        assert "@timestamp" in parsed

    def test_correlation_id_cloudwatch_format(self):
        """Test correlation ID formatting for CloudWatch."""
        formatter = CloudWatchFormatter()

        # Set correlation ID
        test_correlation_id = "cloudwatch-correlation-123"
        CorrelationContext.set(test_correlation_id)

        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="/test.py", lineno=1, msg="Test", args=(), exc_info=None
        )

        formatted = formatter.format(record)
        parsed = json.loads(formatted)

        assert parsed["@correlationId"] == test_correlation_id

        # Clean up
        CorrelationContext.set(None)

    def test_cloudwatch_exception_formatting(self):
        """Test exception formatting for CloudWatch."""
        formatter = CloudWatchFormatter()

        # Create exception info
        try:
            raise RuntimeError("CloudWatch exception test")
        except RuntimeError:
            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="/test.py",
            lineno=1,
            msg="CloudWatch error",
            args=(),
            exc_info=exc_info,
        )

        formatted = formatter.format(record)
        parsed = json.loads(formatted)

        assert "@exception" in parsed
        assert parsed["@exception"]["type"] == "RuntimeError"
        assert parsed["@exception"]["message"] == "CloudWatch exception test"
        assert "stack" in parsed["@exception"]
        assert isinstance(parsed["@exception"]["stack"], str)

    def test_lambda_context_handling(self):
        """Test Lambda context information handling."""
        formatter = CloudWatchFormatter()

        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="/test.py", lineno=1, msg="Lambda test", args=(), exc_info=None
        )

        # Add Lambda-specific attribute
        record.aws_request_id = "lambda-request-123"

        formatted = formatter.format(record)
        parsed = json.loads(formatted)

        assert parsed["@requestId"] == "lambda-request-123"

    def test_custom_fields_handling(self):
        """Test handling of custom fields in CloudWatch format."""
        formatter = CloudWatchFormatter()

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="/test.py",
            lineno=1,
            msg="Custom fields test",
            args=(),
            exc_info=None,
        )

        # Add custom fields
        record.custom_user_id = "user123"
        record.metric_duration = 150.5
        record.custom_operation = "process_payment"

        formatted = formatter.format(record)
        parsed = json.loads(formatted)

        assert parsed["custom_user_id"] == "user123"
        assert parsed["metric_duration"] == 150.5
        assert parsed["custom_operation"] == "process_payment"


class TestConsoleFormatter:
    """Test ConsoleFormatter functionality."""

    def test_basic_console_formatting(self):
        """Test basic console log formatting."""
        formatter = ConsoleFormatter(use_colors=False)

        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/test.py",
            lineno=42,
            msg="Console test message",
            args=(),
            exc_info=None,
        )
        record.funcName = "test_function"

        formatted = formatter.format(record)

        # Verify basic console format components
        assert "INFO" in formatted
        assert "test.logger:test_function:42" in formatted
        assert "Console test message" in formatted
        # Should contain timestamp (basic format check)
        assert "-" in formatted and ":" in formatted

    def test_colored_output_disabled(self):
        """Test console formatting without colors."""
        formatter = ConsoleFormatter(use_colors=False)

        record = logging.LogRecord(
            name="test", level=logging.ERROR, pathname="/test.py", lineno=1, msg="Error message", args=(), exc_info=None
        )
        record.funcName = "test_func"

        formatted = formatter.format(record)

        # Should not contain ANSI color codes
        assert "\033[" not in formatted
        assert "ERROR" in formatted

    @patch("sys.stderr.isatty", return_value=True)
    def test_colored_output_enabled(self, mock_isatty: Any) -> None:
        """Test console formatting with colors enabled."""
        formatter = ConsoleFormatter(use_colors=True)

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="/test.py",
            lineno=1,
            msg="Colored error message",
            args=(),
            exc_info=None,
        )
        record.funcName = "test_func"

        formatted = formatter.format(record)

        # Should contain ANSI color codes for ERROR level (red)
        assert "\033[31m" in formatted  # Red color code
        assert "\033[0m" in formatted  # Reset code
        assert "ERROR" in formatted

    def test_correlation_id_display(self):
        """Test correlation ID display in console format."""
        formatter = ConsoleFormatter(use_colors=False)

        # Set correlation ID
        test_correlation_id = "console-correlation-123"
        CorrelationContext.set(test_correlation_id)

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="/test.py",
            lineno=1,
            msg="Test with correlation",
            args=(),
            exc_info=None,
        )
        record.funcName = "test_func"

        formatted = formatter.format(record)

        # Should display first 8 chars of correlation ID in brackets
        expected_short_id = test_correlation_id[:8]
        assert f"[{expected_short_id}]" in formatted

        # Clean up
        CorrelationContext.set(None)

    def test_exception_display(self):
        """Test exception display in console format."""
        formatter = ConsoleFormatter(use_colors=False)

        # Create exception info
        try:
            raise ValueError("Console exception test")
        except ValueError:
            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="/test.py",
            lineno=1,
            msg="Console error with exception",
            args=(),
            exc_info=exc_info,
        )
        record.funcName = "test_func"

        formatted = formatter.format(record)

        # Should contain exception information
        assert "Console error with exception" in formatted
        assert "ValueError: Console exception test" in formatted
        assert "Traceback" in formatted

    def test_color_codes_mapping(self):
        """Test that different log levels use appropriate colors."""
        formatter = ConsoleFormatter(use_colors=True)

        # Mock isatty to return True for color support
        with patch("sys.stderr.isatty", return_value=True):
            levels_and_colors = [
                (logging.DEBUG, "\033[36m"),  # Cyan
                (logging.INFO, "\033[32m"),  # Green
                (logging.WARNING, "\033[33m"),  # Yellow
                (logging.ERROR, "\033[31m"),  # Red
                (logging.CRITICAL, "\033[35m"),  # Magenta
            ]

            for level, expected_color in levels_and_colors:
                record = logging.LogRecord(
                    name="test", level=level, pathname="/test.py", lineno=1, msg="Test message", args=(), exc_info=None
                )
                record.funcName = "test_func"

                formatted = formatter.format(record)
                assert expected_color in formatted, f"Color not found for level {level}"
