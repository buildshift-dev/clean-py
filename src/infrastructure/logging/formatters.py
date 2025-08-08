"""Custom log formatters for different output targets."""

import json
import logging
import socket
import sys
import traceback
from datetime import UTC, datetime
from typing import Any

from .correlation import CorrelationContext


class StructuredFormatter(logging.Formatter):
    """
    JSON structured logging formatter for machine-readable logs.

    Produces logs suitable for aggregation systems like CloudWatch Insights,
    Elasticsearch, or Splunk.
    """

    def __init__(
        self,
        service_name: str = "clean-py",
        version: str = "1.0.0",
        environment: str = "local",
        include_hostname: bool = True,
        include_process_info: bool = True,
    ) -> None:
        """
        Initialize the structured formatter.

        Args:
            service_name: Name of the service
            version: Service version
            environment: Deployment environment
            include_hostname: Include hostname in logs
            include_process_info: Include process and thread IDs
        """
        super().__init__()
        self.service_name = service_name
        self.version = version
        self.environment = environment
        self.include_hostname = include_hostname
        self.include_process_info = include_process_info
        self.hostname = socket.gethostname() if include_hostname else None

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.

        Args:
            record: Log record to format

        Returns:
            str: JSON-formatted log entry
        """
        # Build base log structure
        log_obj: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": self.service_name,
            "version": self.version,
            "environment": self.environment,
        }

        # Add correlation ID if available
        correlation_id = CorrelationContext.get()
        if correlation_id:
            log_obj["correlation_id"] = correlation_id

        # Add hostname if configured
        if self.hostname:
            log_obj["hostname"] = self.hostname

        # Add process info if configured
        if self.include_process_info:
            log_obj["process"] = {
                "pid": record.process,
                "thread_id": record.thread,
                "thread_name": record.threadName,
            }

        # Add source location
        log_obj["source"] = {
            "file": record.pathname,
            "line": record.lineno,
            "function": record.funcName,
            "module": record.module,
        }

        # Add exception info if present
        if record.exc_info:
            log_obj["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info),
            }

        # Add extra fields from record
        extra_fields = {}
        for key, value in record.__dict__.items():
            if key not in [
                "name",
                "msg",
                "args",
                "created",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "message",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "thread",
                "threadName",
                "exc_info",
                "exc_text",
                "stack_info",
            ]:
                try:
                    # Attempt to serialize the value
                    json.dumps(value)
                    extra_fields[key] = value
                except (TypeError, ValueError):
                    extra_fields[key] = str(value)

        if extra_fields:
            log_obj["extra"] = extra_fields

        return json.dumps(log_obj, default=str)


class CloudWatchFormatter(logging.Formatter):
    """
    Formatter optimized for AWS CloudWatch Logs.

    Produces compact JSON that works well with CloudWatch Insights queries.
    """

    def __init__(self, service_name: str = "clean-py", environment: str = "production") -> None:
        """
        Initialize CloudWatch formatter.

        Args:
            service_name: Name of the service
            environment: Deployment environment
        """
        super().__init__()
        self.service_name = service_name
        self.environment = environment

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record for CloudWatch.

        Args:
            record: Log record to format

        Returns:
            str: CloudWatch-optimized JSON log entry
        """
        # Build CloudWatch-optimized structure
        log_obj: dict[str, Any] = {
            "@timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "@level": record.levelname,
            "@logger": record.name,
            "@message": record.getMessage(),
            "service": self.service_name,
            "env": self.environment,
        }

        # Add correlation ID for tracing
        correlation_id = CorrelationContext.get()
        if correlation_id:
            log_obj["@correlationId"] = correlation_id

        # Add exception details if present
        if record.exc_info:
            log_obj["@exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "stack": "".join(traceback.format_exception(*record.exc_info)),
            }

        # Add Lambda context if available
        if hasattr(record, "aws_request_id"):
            log_obj["@requestId"] = record.aws_request_id

        # Add any custom fields
        for key, value in record.__dict__.items():
            if key.startswith("custom_") or key.startswith("metric_"):
                log_obj[key] = value

        return json.dumps(log_obj, default=str)


class ConsoleFormatter(logging.Formatter):
    """
    Human-readable formatter for console output during development.

    Provides colored output and readable formatting for local development.
    """

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def __init__(self, use_colors: bool = True) -> None:
        """
        Initialize console formatter.

        Args:
            use_colors: Enable colored output
        """
        super().__init__()
        self.use_colors = use_colors

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record for console output.

        Args:
            record: Log record to format

        Returns:
            str: Human-readable log entry
        """
        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")

        # Get correlation ID if available
        correlation_id = CorrelationContext.get()
        correlation_str = f"[{correlation_id[:8]}] " if correlation_id else ""

        # Apply color if enabled and supported
        if self.use_colors and sys.stderr.isatty():
            level_color = self.COLORS.get(record.levelname, "")
            level_str = f"{level_color}{record.levelname:8}{self.RESET}"
        else:
            level_str = f"{record.levelname:8}"

        # Build the message
        location = f"{record.name}:{record.funcName}:{record.lineno}"
        message = f"{timestamp} | {level_str} | {correlation_str}{location} | {record.getMessage()}"

        # Add exception info if present
        if record.exc_info:
            exception_text = "".join(traceback.format_exception(*record.exc_info))
            message += f"\n{exception_text}"

        return message
