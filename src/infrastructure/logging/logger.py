"""Main logging configuration and factory functions."""

import logging

from .config import LogConfig, get_log_config
from .handlers import get_cloudwatch_handler, get_console_handler


def get_logger(name: str, config: LogConfig | None = None) -> logging.Logger:
    """
    Get a configured logger instance.

    Args:
        name: Logger name (typically __name__)
        config: Optional logging configuration (uses default if not provided)

    Returns:
        logging.Logger: Configured logger instance
    """
    if config is None:
        config = get_log_config()

    logger = logging.getLogger(name)

    # Avoid duplicate handlers if logger already configured
    if logger.handlers:
        return logger

    # Configure logger level
    level_value = config.level.value if hasattr(config.level, "value") else config.level
    logger.setLevel(level_value)
    logger.propagate = False  # Prevent duplicate logs

    # Add console handler
    console_handler = get_console_handler(config)
    logger.addHandler(console_handler)

    # Add CloudWatch handler if enabled
    cloudwatch_handler = get_cloudwatch_handler(config)
    if cloudwatch_handler:
        logger.addHandler(cloudwatch_handler)

    return logger


def configure_logging(config: LogConfig | None = None) -> None:
    """
    Configure global logging settings.

    This should be called once at application startup to set up
    the root logger and configure global logging behavior.

    Args:
        config: Optional logging configuration (uses default if not provided)
    """
    if config is None:
        config = get_log_config()

    # Configure root logger
    root_logger = logging.getLogger()
    level_value = config.level.value if hasattr(config.level, "value") else config.level
    root_logger.setLevel(level_value)

    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Add console handler
    console_handler = get_console_handler(config)
    root_logger.addHandler(console_handler)

    # Add CloudWatch handler if enabled
    cloudwatch_handler = get_cloudwatch_handler(config)
    if cloudwatch_handler:
        root_logger.addHandler(cloudwatch_handler)

    # Configure third-party loggers
    _configure_third_party_loggers(config)

    # Log configuration for debugging
    logger = get_logger(__name__, config)
    logger.info(
        "Logging configured",
        extra={
            "config": {
                "level": config.level,
                "format": config.format,
                "environment": config.environment,
                "cloudwatch_enabled": config.cloudwatch_enabled,
                "service_name": config.service_name,
            }
        },
    )


def _configure_third_party_loggers(config: LogConfig) -> None:
    """
    Configure logging for third-party libraries.

    Args:
        config: Logging configuration
    """
    # Reduce noise from common third-party libraries
    third_party_configs = {
        "boto3": logging.WARNING,
        "botocore": logging.WARNING,
        "urllib3": logging.WARNING,
        "requests": logging.WARNING,
        "httpx": logging.WARNING,
        "asyncio": logging.WARNING,
        "sqlalchemy.engine": logging.WARNING,
        "sqlalchemy.pool": logging.WARNING,
        "sqlalchemy.dialects": logging.WARNING,
    }

    # In development, allow more verbose logging for debugging
    if config.environment == "local":
        third_party_configs.update(
            {
                "sqlalchemy.engine": logging.INFO,
                "httpx": logging.INFO,
            }
        )

    # Apply configurations
    for logger_name, level in third_party_configs.items():
        logging.getLogger(logger_name).setLevel(level)


def shutdown_logging() -> None:
    """
    Shutdown logging handlers gracefully.

    This should be called during application shutdown to ensure
    all log messages are flushed and handlers are closed properly.
    """
    logging.shutdown()


# Convenience function for application code
def get_application_logger(name: str) -> logging.Logger:
    """
    Get a logger for application code with standard configuration.

    Args:
        name: Logger name (typically __name__)

    Returns:
        logging.Logger: Configured application logger
    """
    return get_logger(name)
