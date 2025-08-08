"""AWS-optimized logging infrastructure for Clean Architecture applications."""

from .config import LogConfig, get_log_config
from .correlation import CorrelationContext, correlation_middleware
from .decorators import log_error, log_execution, log_performance
from .formatters import CloudWatchFormatter, StructuredFormatter
from .handlers import get_cloudwatch_handler, get_console_handler
from .logger import configure_logging, get_logger
from .middleware import LoggingMiddleware

__all__ = [
    "LogConfig",
    "get_log_config",
    "CorrelationContext",
    "correlation_middleware",
    "CloudWatchFormatter",
    "StructuredFormatter",
    "get_cloudwatch_handler",
    "get_console_handler",
    "get_logger",
    "configure_logging",
    "log_execution",
    "log_error",
    "log_performance",
    "LoggingMiddleware",
]
