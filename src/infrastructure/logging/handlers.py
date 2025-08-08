"""Log handlers for different output targets."""

import logging
import os
import sys

from .config import LogConfig, LogFormat
from .formatters import CloudWatchFormatter, ConsoleFormatter, StructuredFormatter


def get_console_handler(config: LogConfig) -> logging.StreamHandler:
    """
    Create a console handler with appropriate formatter.

    Args:
        config: Logging configuration

    Returns:
        logging.StreamHandler: Configured console handler
    """
    handler = logging.StreamHandler(sys.stdout)

    # Select formatter based on configuration
    if config.environment == "local" and config.format == LogFormat.TEXT:
        formatter = ConsoleFormatter(use_colors=True)
    elif config.format == LogFormat.CLOUDWATCH:
        formatter = CloudWatchFormatter(service_name=config.service_name, environment=config.environment)
    else:
        formatter = StructuredFormatter(
            service_name=config.service_name,
            version=config.version,
            environment=config.environment,
            include_hostname=config.include_hostname,
            include_process_info=config.include_process_info,
        )

    handler.setFormatter(formatter)
    level_value = config.level.value if hasattr(config.level, "value") else config.level
    handler.setLevel(level_value)

    return handler


def get_cloudwatch_handler(
    config: LogConfig,
    batch_size: int = 100,
    flush_interval: int = 10000,
) -> logging.Handler | None:
    """
    Create a CloudWatch Logs handler.

    Args:
        config: Logging configuration
        batch_size: Number of log events to batch before sending
        flush_interval: Maximum time in milliseconds between sends

    Returns:
        Optional[logging.Handler]: CloudWatch handler if enabled and available
    """
    if not config.cloudwatch_enabled:
        return None

    # Don't try CloudWatch in local environments unless explicitly requested
    if config.environment == "local" and not os.getenv("FORCE_CLOUDWATCH"):
        return None

    if not config.cloudwatch_log_group:
        logging.warning("CloudWatch enabled but log group not specified")
        return None

    try:
        # Import boto3 only when needed
        import boto3
        from watchtower import CloudWatchLogHandler

        # Test AWS credentials availability
        try:
            cloudwatch_client = boto3.client("logs", region_name=config.cloudwatch_region)
            # Quick test to verify credentials work
            cloudwatch_client.describe_log_groups(limit=1)
        except Exception as cred_error:
            logging.warning(
                f"CloudWatch credentials not available or invalid: {cred_error}. Falling back to console logging."
            )
            return None

        # Create handler
        handler = CloudWatchLogHandler(
            log_group=config.cloudwatch_log_group,
            stream_name=config.cloudwatch_log_stream,
            boto3_client=cloudwatch_client,
            batch_size=batch_size,
            max_batch_time=flush_interval,
            create_log_group=False,  # Should be created via infrastructure
        )

        # Use CloudWatch-optimized formatter
        formatter = CloudWatchFormatter(service_name=config.service_name, environment=config.environment)
        handler.setFormatter(formatter)
        level_value = config.level.value if hasattr(config.level, "value") else config.level
        handler.setLevel(level_value)

        return handler

    except ImportError:
        if config.environment != "local":
            logging.warning(
                "CloudWatch logging enabled but watchtower not installed. Install with: pip install watchtower"
            )
        return None
    except Exception as e:
        logging.error(f"Failed to initialize CloudWatch handler: {e}")
        return None


def get_file_handler(
    config: LogConfig,
    filename: str = "app.log",
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
) -> logging.Handler:
    """
    Create a rotating file handler for local logging.

    Args:
        config: Logging configuration
        filename: Log file name
        max_bytes: Maximum size per log file
        backup_count: Number of backup files to keep

    Returns:
        logging.Handler: Configured file handler
    """
    from logging.handlers import RotatingFileHandler

    handler = RotatingFileHandler(
        filename=filename,
        maxBytes=max_bytes,
        backupCount=backup_count,
    )

    # Use structured formatter for file logs
    formatter = StructuredFormatter(
        service_name=config.service_name,
        version=config.version,
        environment=config.environment,
        include_hostname=config.include_hostname,
        include_process_info=config.include_process_info,
    )

    handler.setFormatter(formatter)
    level_value = config.level.value if hasattr(config.level, "value") else config.level
    handler.setLevel(level_value)

    return handler


class SamplingHandler(logging.Handler):
    """
    Handler that samples log messages based on a sampling rate.

    Useful for reducing log volume in high-traffic environments while
    still capturing a representative sample of events.
    """

    def __init__(self, handler: logging.Handler, sampling_rate: float = 1.0) -> None:
        """
        Initialize sampling handler.

        Args:
            handler: Underlying handler to forward sampled logs to
            sampling_rate: Fraction of logs to emit (0.0-1.0)
        """
        super().__init__()
        self.handler = handler
        self.sampling_rate = sampling_rate
        self._counter = 0

    def emit(self, record: logging.LogRecord) -> None:
        """
        Emit log record based on sampling rate.

        Args:
            record: Log record to potentially emit
        """
        import random

        # Always emit errors and above
        if record.levelno >= logging.ERROR:
            self.handler.emit(record)
            return

        # Sample other levels
        if random.random() < self.sampling_rate:
            self.handler.emit(record)


class BufferingHandler(logging.Handler):
    """
    Handler that buffers log messages and flushes them periodically.

    Useful for reducing I/O overhead in high-throughput scenarios.
    """

    def __init__(
        self,
        handler: logging.Handler,
        buffer_size: int = 100,
        flush_level: int = logging.ERROR,
    ) -> None:
        """
        Initialize buffering handler.

        Args:
            handler: Underlying handler to forward buffered logs to
            buffer_size: Number of records to buffer before flushing
            flush_level: Log level that triggers immediate flush
        """
        super().__init__()
        self.handler = handler
        self.buffer_size = buffer_size
        self.flush_level = flush_level
        self.buffer = []

    def emit(self, record: logging.LogRecord) -> None:
        """
        Buffer log record and flush if needed.

        Args:
            record: Log record to buffer
        """
        self.buffer.append(record)

        # Immediate flush for high-priority messages
        if record.levelno >= self.flush_level or len(self.buffer) >= self.buffer_size:
            self.flush()

    def flush(self) -> None:
        """Flush buffered records to underlying handler."""
        for record in self.buffer:
            self.handler.emit(record)
        self.buffer.clear()

    def close(self) -> None:
        """Close handler and flush remaining records."""
        self.flush()
        super().close()
