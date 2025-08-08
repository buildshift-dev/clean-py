"""Lambda-specific logging utilities and helpers."""

import json
import os
from typing import Any

from .config import Environment, LogConfig, LogFormat, LogLevel
from .correlation import CorrelationContext
from .logger import configure_logging, get_logger


def configure_lambda_logging(
    service_name: str | None = None,
    version: str | None = None,
    log_level: str = "INFO",
) -> None:
    """
    Configure logging specifically for AWS Lambda environment.

    This function should be called at the start of your Lambda handler
    to set up proper logging configuration.

    Args:
        service_name: Lambda function name (auto-detected if not provided)
        version: Function version (auto-detected if not provided)
        log_level: Logging level
    """
    # Auto-detect Lambda context
    function_name = service_name or os.getenv("AWS_LAMBDA_FUNCTION_NAME", "unknown-function")
    function_version = version or os.getenv("AWS_LAMBDA_FUNCTION_VERSION", "1.0.0")

    # Parse log level string to enum
    try:
        level_enum = LogLevel[log_level.upper()]
    except KeyError:
        level_enum = LogLevel.INFO

    # Create Lambda-optimized config
    config = LogConfig(
        level=level_enum,
        format=LogFormat.CLOUDWATCH,  # CloudWatch-optimized format
        environment=Environment.PRODUCTION,  # Lambda is always production
        service_name=function_name,
        version=function_version,
        cloudwatch_enabled=False,  # Lambda automatically logs to CloudWatch
        include_hostname=False,  # Not relevant in Lambda
        include_process_info=False,  # Not relevant in Lambda
        log_request_body=False,  # Be conservative with Lambda logs
        log_response_body=False,
    )

    # Configure logging
    configure_logging(config)


def lambda_request_logger(
    event: dict[str, Any],
    context: Any,
    logger_name: str = "lambda.request",
) -> None:
    """
    Log Lambda request details in a structured format.

    Args:
        event: Lambda event data
        context: Lambda context object
        logger_name: Logger name to use
    """
    logger = get_logger(logger_name)

    # Extract correlation ID from various event sources
    correlation_id = _extract_correlation_id_from_event(event)
    if correlation_id:
        CorrelationContext.set(correlation_id)

    # Build request context
    request_context = {
        "event_type": "lambda_request",
        "aws_request_id": context.aws_request_id,
        "function_name": context.function_name,
        "function_version": context.function_version,
        "remaining_time_ms": context.get_remaining_time_in_millis(),
        "memory_limit_mb": context.memory_limit_in_mb,
        "log_group_name": context.log_group_name,
        "log_stream_name": context.log_stream_name,
    }

    # Add correlation ID if available
    if correlation_id:
        request_context["correlation_id"] = correlation_id

    # Add event source information
    event_source_info = _get_event_source_info(event)
    if event_source_info:
        request_context.update(event_source_info)

    # Log request
    logger.info(f"Lambda request started: {context.function_name}", extra=request_context)


def lambda_response_logger(
    response: Any,
    context: Any,
    duration_ms: float | None = None,
    logger_name: str = "lambda.response",
) -> None:
    """
    Log Lambda response details.

    Args:
        response: Lambda response data
        context: Lambda context object
        duration_ms: Execution duration in milliseconds
        logger_name: Logger name to use
    """
    logger = get_logger(logger_name)

    # Build response context
    response_context = {
        "event_type": "lambda_response",
        "aws_request_id": context.aws_request_id,
        "function_name": context.function_name,
        "remaining_time_ms": context.get_remaining_time_in_millis(),
        "response_type": type(response).__name__,
    }

    # Add correlation ID if available
    correlation_id = CorrelationContext.get()
    if correlation_id:
        response_context["correlation_id"] = correlation_id

    # Add duration if provided
    if duration_ms is not None:
        response_context["duration_ms"] = duration_ms

    # Add response size estimation
    try:
        if isinstance(response, dict):
            response_size = len(json.dumps(response, default=str))
            response_context["response_size_bytes"] = response_size
        elif isinstance(response, str):
            response_context["response_size_bytes"] = len(response.encode())
    except Exception:
        pass  # Don't fail if we can't estimate size

    # Log response
    logger.info(f"Lambda request completed: {context.function_name}", extra=response_context)


def lambda_error_logger(
    error: Exception,
    context: Any,
    event: dict[str, Any] | None = None,
    logger_name: str = "lambda.error",
) -> None:
    """
    Log Lambda execution errors with detailed context.

    Args:
        error: Exception that occurred
        context: Lambda context object
        event: Original Lambda event (optional)
        logger_name: Logger name to use
    """
    logger = get_logger(logger_name)

    # Build error context
    error_context = {
        "event_type": "lambda_error",
        "aws_request_id": context.aws_request_id,
        "function_name": context.function_name,
        "function_version": context.function_version,
        "remaining_time_ms": context.get_remaining_time_in_millis(),
        "error_type": type(error).__name__,
        "error_message": str(error),
    }

    # Add correlation ID if available
    correlation_id = CorrelationContext.get()
    if correlation_id:
        error_context["correlation_id"] = correlation_id

    # Add event source info if available
    if event:
        event_source_info = _get_event_source_info(event)
        if event_source_info:
            error_context.update(event_source_info)

    # Log error
    logger.error(f"Lambda error in {context.function_name}: {error}", extra=error_context, exc_info=True)


def _extract_correlation_id_from_event(event: dict[str, Any]) -> str | None:
    """
    Extract correlation ID from various Lambda event sources.

    Args:
        event: Lambda event data

    Returns:
        Optional[str]: Extracted correlation ID
    """
    # API Gateway events
    if "headers" in event:
        headers = event.get("headers", {})
        correlation_id = headers.get("X-Correlation-ID") or headers.get("X-Request-ID") or headers.get("X-Trace-ID")
        if correlation_id:
            return correlation_id

    # ALB events
    if "requestContext" in event and "requestId" in event["requestContext"]:
        return event["requestContext"]["requestId"]

    # SQS events
    if "Records" in event and event["Records"]:
        record = event["Records"][0]
        if "messageAttributes" in record:
            attrs = record["messageAttributes"]
            if "correlationId" in attrs:
                return attrs["correlationId"]["stringValue"]

    # SNS events
    if "Records" in event and event["Records"]:
        record = event["Records"][0]
        if record.get("EventSource") == "aws:sns" and "MessageAttributes" in record.get("Sns", {}):
            attrs = record["Sns"]["MessageAttributes"]
            if "correlationId" in attrs:
                return attrs["correlationId"]["Value"]

    # EventBridge events
    if "detail" in event and isinstance(event["detail"], dict):
        return event["detail"].get("correlationId")

    return None


def _get_event_source_info(event: dict[str, Any]) -> dict[str, Any] | None:
    """
    Extract event source information for logging.

    Args:
        event: Lambda event data

    Returns:
        Optional[Dict[str, Any]]: Event source information
    """
    info = {}

    # API Gateway
    if "httpMethod" in event and "path" in event:
        info.update(
            {
                "event_source": "api_gateway",
                "http_method": event.get("httpMethod"),
                "path": event.get("path"),
                "query_string_parameters": event.get("queryStringParameters"),
            }
        )
        if "requestContext" in event:
            request_context = event["requestContext"]
            info.update(
                {
                    "request_id": request_context.get("requestId"),
                    "stage": request_context.get("stage"),
                    "api_id": request_context.get("apiId"),
                }
            )

    # ALB
    elif "requestContext" in event and "elb" in event["requestContext"]:
        info.update(
            {
                "event_source": "alb",
                "http_method": event.get("httpMethod"),
                "path": event.get("path"),
                "target_group_arn": event["requestContext"]["elb"]["targetGroupArn"],
            }
        )

    # SQS
    elif "Records" in event and event["Records"] and event["Records"][0].get("eventSource") == "aws:sqs":
        record = event["Records"][0]
        info.update(
            {
                "event_source": "sqs",
                "queue_url": record.get("eventSourceARN"),
                "message_count": len(event["Records"]),
            }
        )

    # SNS
    elif "Records" in event and event["Records"] and event["Records"][0].get("EventSource") == "aws:sns":
        record = event["Records"][0]
        info.update(
            {
                "event_source": "sns",
                "topic_arn": record["Sns"]["TopicArn"],
                "message_count": len(event["Records"]),
            }
        )

    # EventBridge
    elif "source" in event and "detail-type" in event:
        info.update(
            {
                "event_source": "eventbridge",
                "source": event["source"],
                "detail_type": event["detail-type"],
                "account": event.get("account"),
                "region": event.get("region"),
            }
        )

    # S3
    elif "Records" in event and event["Records"] and event["Records"][0].get("eventSource") == "aws:s3":
        record = event["Records"][0]
        s3_info = record["s3"]
        info.update(
            {
                "event_source": "s3",
                "bucket_name": s3_info["bucket"]["name"],
                "object_key": s3_info["object"]["key"],
                "event_name": record["eventName"],
            }
        )

    return info if info else None
