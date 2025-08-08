"""Logging configuration for AWS environments."""

import os
from enum import Enum

from pydantic import BaseModel, Field


class LogLevel(str, Enum):
    """Logging levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogFormat(str, Enum):
    """Logging output formats."""

    JSON = "json"
    TEXT = "text"
    CLOUDWATCH = "cloudwatch"


class Environment(str, Enum):
    """Deployment environments."""

    LOCAL = "local"
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class LogConfig(BaseModel):
    """Centralized logging configuration."""

    level: LogLevel = Field(default=LogLevel.INFO, description="Global log level")
    format: LogFormat = Field(default=LogFormat.JSON, description="Log output format")
    environment: Environment = Field(default=Environment.LOCAL, description="Deployment environment")
    service_name: str = Field(default="clean-py", description="Service identifier for logs")
    version: str = Field(default="1.0.0", description="Service version")

    # AWS CloudWatch settings
    cloudwatch_enabled: bool = Field(default=False, description="Enable CloudWatch logging")
    cloudwatch_log_group: str | None = Field(default=None, description="CloudWatch log group name")
    cloudwatch_log_stream: str | None = Field(default=None, description="CloudWatch log stream name")
    cloudwatch_region: str = Field(default="us-east-1", description="AWS region for CloudWatch")

    # Performance settings
    log_request_body: bool = Field(default=False, description="Log request bodies (be careful with sensitive data)")
    log_response_body: bool = Field(default=False, description="Log response bodies (be careful with sensitive data)")
    slow_request_threshold_ms: int = Field(
        default=1000, description="Threshold for slow request warnings (milliseconds)"
    )

    # Sampling settings for high-volume environments
    sampling_rate: float = Field(default=1.0, ge=0.0, le=1.0, description="Sampling rate for debug logs (0.0-1.0)")

    # Additional metadata
    include_hostname: bool = Field(default=True, description="Include hostname in logs")
    include_process_info: bool = Field(default=True, description="Include process ID and thread ID")

    class Config:
        """Pydantic config."""

        use_enum_values = True


def _parse_bool(value: str | None, default: bool = False) -> bool:
    """Parse string to boolean with various truthy/falsy values."""
    if value is None:
        return default

    value = value.lower().strip()
    return value in ("true", "1", "yes", "on", "enabled")


def _is_running_locally() -> bool:
    """
    Detect if the application is running locally vs in AWS.

    Returns:
        bool: True if running locally, False if in AWS
    """
    # Check for AWS environment indicators
    aws_indicators = [
        "AWS_LAMBDA_FUNCTION_NAME",  # Lambda
        "ECS_CONTAINER_METADATA_URI_V4",  # ECS Fargate
        "AWS_EXECUTION_ENV",  # Lambda/ECS execution environment
        "AWS_BATCH_JOB_ID",  # AWS Batch
        "AWS_REGION",  # Often set in AWS environments
    ]

    # If any AWS indicator is present, we're likely in AWS
    if any(os.getenv(indicator) for indicator in aws_indicators):
        return False

    # Check for local development indicators
    local_indicators = [
        "DOCKER_COMPOSE_PROJECT_NAME",  # Docker Compose
        "COMPOSE_PROJECT_NAME",  # Docker Compose alternative
    ]

    # Check if running in Docker locally
    if any(os.getenv(indicator) for indicator in local_indicators):
        return True

    # Check for development-specific environment variables
    env = os.getenv("ENVIRONMENT", "").lower()
    if env in ["local", "development", "dev"]:
        return True

    # Check if we can detect Docker environment (but not in AWS)
    if os.path.exists("/.dockerenv") and not any(os.getenv(indicator) for indicator in aws_indicators):
        return True

    # Check for common local development patterns
    if os.getenv("HOME") and not os.getenv("AWS_EXECUTION_ENV"):
        # Likely running on a local machine
        return True

    # Default to local if we can't determine
    return True


def _get_local_config() -> LogConfig:
    """Get configuration optimized for local development."""
    return LogConfig(
        level=LogLevel(os.getenv("LOG_LEVEL", "DEBUG")),  # More verbose locally
        format=LogFormat.TEXT,  # Human-readable console output
        environment=Environment.LOCAL,
        service_name=os.getenv("SERVICE_NAME", "clean-py"),
        version=os.getenv("SERVICE_VERSION", "dev"),
        cloudwatch_enabled=False,  # No CloudWatch locally
        log_request_body=_parse_bool(os.getenv("LOG_REQUEST_BODY"), True),  # More debugging info
        log_response_body=_parse_bool(os.getenv("LOG_RESPONSE_BODY"), True),
        slow_request_threshold_ms=int(os.getenv("SLOW_REQUEST_THRESHOLD_MS", "500")),  # Lower threshold
        sampling_rate=1.0,  # No sampling locally
        include_hostname=True,
        include_process_info=True,
    )


def _get_aws_config() -> LogConfig:
    """Get configuration optimized for AWS deployment."""
    # Determine environment based on AWS context
    if os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        env = Environment.PRODUCTION
        default_log_format = LogFormat.CLOUDWATCH
        default_cloudwatch_enabled = False  # Lambda logs automatically
        default_include_process_info = False
    elif os.getenv("ECS_CONTAINER_METADATA_URI_V4"):
        env = Environment(os.getenv("ENVIRONMENT", "production"))
        default_log_format = LogFormat.JSON
        default_cloudwatch_enabled = True
        default_include_process_info = True
    else:
        # Generic AWS environment
        env = Environment(os.getenv("ENVIRONMENT", "production"))
        default_log_format = LogFormat.JSON
        default_cloudwatch_enabled = True
        default_include_process_info = True

    # Allow format override via environment variable
    log_format = LogFormat(os.getenv("LOG_FORMAT", default_log_format.value))

    # Allow boolean overrides via environment variables with proper parsing
    cloudwatch_enabled = _parse_bool(os.getenv("CLOUDWATCH_ENABLED"), default_cloudwatch_enabled)
    include_process_info = _parse_bool(os.getenv("LOG_INCLUDE_PROCESS_INFO"), default_include_process_info)

    return LogConfig(
        level=LogLevel(os.getenv("LOG_LEVEL", "INFO")),  # Less verbose in production
        format=log_format,
        environment=env,
        service_name=os.getenv("SERVICE_NAME", "clean-py"),
        version=os.getenv("SERVICE_VERSION", "1.0.0"),
        cloudwatch_enabled=cloudwatch_enabled,
        cloudwatch_log_group=os.getenv("CLOUDWATCH_LOG_GROUP"),
        cloudwatch_log_stream=os.getenv("CLOUDWATCH_LOG_STREAM"),
        cloudwatch_region=os.getenv("AWS_REGION", "us-east-1"),
        log_request_body=_parse_bool(os.getenv("LOG_REQUEST_BODY"), False),  # Conservative in production
        log_response_body=_parse_bool(os.getenv("LOG_RESPONSE_BODY"), False),
        slow_request_threshold_ms=int(os.getenv("SLOW_REQUEST_THRESHOLD_MS", "1000")),
        sampling_rate=float(os.getenv("LOG_SAMPLING_RATE", "0.1")),  # Sample debug logs in production
        include_hostname=_parse_bool(os.getenv("LOG_INCLUDE_HOSTNAME"), True),
        include_process_info=include_process_info,
    )


def get_log_config() -> LogConfig:
    """
    Get logging configuration automatically detecting local vs AWS environments.

    Returns:
        LogConfig: Environment-appropriate logging configuration
    """
    if _is_running_locally():
        config = _get_local_config()
        # Log the detection for debugging (but only once)
        if not hasattr(get_log_config, "_logged_detection"):
            print(f"🏠 Local environment detected - using console logging (Level: {config.level})")
            get_log_config._logged_detection = True
    else:
        config = _get_aws_config()
        # Log the detection for debugging (but only once)
        if not hasattr(get_log_config, "_logged_detection"):
            print(f"☁️ AWS environment detected - using structured logging (CloudWatch: {config.cloudwatch_enabled})")
            get_log_config._logged_detection = True

    return config
