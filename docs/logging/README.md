# AWS-Optimized Logging Infrastructure

This documentation covers the comprehensive logging infrastructure designed for Clean Architecture applications deployed on AWS. The system provides structured logging, correlation tracking, CloudWatch integration, and Lambda-specific utilities.

## Table of Contents

- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Components Overview](#components-overview)
- [Usage Patterns](#usage-patterns)
- [AWS Integration](#aws-integration)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Quick Start

The logging system automatically detects your environment and configures itself appropriately:

- **Local Development**: Console logging with DEBUG level and human-readable format
- **Docker Local**: Detects Docker Compose and uses local configuration
- **AWS ECS/Fargate**: Structured JSON logging with CloudWatch integration
- **AWS Lambda**: CloudWatch-optimized logging with Lambda context

### FastAPI Application

```python
from fastapi import FastAPI
from src.infrastructure.logging import (
    configure_logging,
    LoggingMiddleware,
    CorrelationMiddleware,
    get_logger
)

app = FastAPI()

# Configure logging at startup - automatically detects environment
configure_logging()

# Add middleware (order matters!)
app.add_middleware(CorrelationMiddleware)
app.add_middleware(LoggingMiddleware)

# Get logger for your module
logger = get_logger(__name__)

@app.get("/")
async def root():
    logger.info("Root endpoint called")  # Shows in console locally, CloudWatch in AWS
    return {"message": "Hello World"}
```

### Environment Detection

The system detects your environment automatically:

```python
# Local machine or Docker Compose
# 🏠 Local environment detected - using console logging (Level: DEBUG)

# AWS ECS/Fargate  
# ☁️ AWS environment detected - using structured logging (CloudWatch: True)

# AWS Lambda
# ☁️ AWS environment detected - using structured logging (CloudWatch: False)
```

### AWS Lambda Function

```python
import time
from src.infrastructure.logging.lambda_utils import (
    configure_lambda_logging,
    lambda_request_logger,
    lambda_response_logger,
    lambda_error_logger
)
from src.infrastructure.logging import get_logger

# Configure at module level
configure_lambda_logging()
logger = get_logger(__name__)

def lambda_handler(event, context):
    start_time = time.perf_counter()
    
    # Log request
    lambda_request_logger(event, context)
    
    try:
        # Your business logic here
        result = {"statusCode": 200, "body": "Success"}
        
        # Log successful response
        duration = (time.perf_counter() - start_time) * 1000
        lambda_response_logger(result, context, duration)
        
        return result
        
    except Exception as e:
        # Log error
        lambda_error_logger(e, context, event)
        raise
```

## Configuration

### Environment Variables

The system uses automatic detection, but you can override with environment variables:

```bash
# Override automatic detection
ENVIRONMENT=local                 # Force local mode: local, development, staging, production
LOG_FORMAT=text                   # Override format: json, text, cloudwatch
LOG_LEVEL=DEBUG                   # Override level: DEBUG, INFO, WARNING, ERROR, CRITICAL

# Force CloudWatch in local environments (needs AWS credentials)
FORCE_CLOUDWATCH=true             # Override local CloudWatch disable
CLOUDWATCH_ENABLED=true           # Explicit CloudWatch control

# Service Configuration (auto-detected in AWS)
SERVICE_NAME=clean-py             # Your service identifier
SERVICE_VERSION=1.0.0             # Service version

# CloudWatch Configuration (AWS environments)
CLOUDWATCH_LOG_GROUP=/aws/ecs/clean-py
CLOUDWATCH_LOG_STREAM=main
AWS_REGION=us-east-1              # CloudWatch region

# Performance Configuration
LOG_REQUEST_BODY=false            # Log HTTP request bodies (default: true locally, false in AWS)
LOG_RESPONSE_BODY=false           # Log HTTP response bodies (default: true locally, false in AWS)
SLOW_REQUEST_THRESHOLD_MS=500     # Slow request threshold (default: 500ms locally, 1000ms in AWS)
LOG_SAMPLING_RATE=1.0             # Debug log sampling rate (default: 1.0 locally, 0.1 in AWS)

# Additional Metadata
LOG_INCLUDE_HOSTNAME=true         # Include hostname in logs
LOG_INCLUDE_PROCESS_INFO=true     # Include PID and thread info
```

### Automatic Environment Detection

The system detects your environment based on:

**Local Environment Indicators:**
- No AWS environment variables present
- `DOCKER_COMPOSE_PROJECT_NAME` or `COMPOSE_PROJECT_NAME` set
- `ENVIRONMENT=local/development/dev`
- `/.dockerenv` file exists (but no AWS indicators)
- `HOME` environment variable present (typical local machine)

**AWS Environment Indicators:**
- `AWS_LAMBDA_FUNCTION_NAME` (Lambda)
- `ECS_CONTAINER_METADATA_URI_V4` (ECS Fargate)
- `AWS_EXECUTION_ENV` (Lambda/ECS)
- `AWS_BATCH_JOB_ID` (AWS Batch)
- `AWS_REGION` (often set in AWS environments)

**Local vs AWS Defaults:**

| Setting | Local Default | AWS Default |
|---------|---------------|-------------|
| Log Level | DEBUG | INFO |
| Log Format | TEXT (human-readable) | JSON/CloudWatch |
| CloudWatch | Disabled | Enabled (if available) |
| Request/Response Body | Logged | Not logged |
| Debug Sampling | No sampling (1.0) | Heavy sampling (0.1) |
| Slow Request Threshold | 500ms | 1000ms |

### Programmatic Configuration

```python
from src.infrastructure.logging import LogConfig, configure_logging

config = LogConfig(
    level="INFO",
    format="json",
    environment="production",
    service_name="my-service",
    cloudwatch_enabled=True,
    cloudwatch_log_group="/aws/ecs/my-service",
    slow_request_threshold_ms=500,
)

configure_logging(config)
```

## Components Overview

### Core Components

| Component | Purpose | Usage |
|-----------|---------|-------|
| `LogConfig` | Centralized configuration | Environment-based settings |
| `get_logger()` | Logger factory | Get configured logger instances |
| `configure_logging()` | Global setup | Application startup configuration |

### Formatters

| Formatter | Use Case | Output Format |
|-----------|----------|---------------|
| `StructuredFormatter` | General use, aggregation systems | JSON with full metadata |
| `CloudWatchFormatter` | CloudWatch Logs optimization | Compact JSON with @ prefixes |
| `ConsoleFormatter` | Local development | Human-readable with colors |

### Handlers

| Handler | Purpose | Configuration |
|---------|---------|---------------|
| Console Handler | Standard output | Always enabled |
| CloudWatch Handler | AWS CloudWatch Logs | Requires watchtower library |
| File Handler | Local file logging | Development/testing |
| Sampling Handler | High-volume environments | Reduces log volume |

### Middleware

| Middleware | Purpose | Features |
|------------|---------|----------|
| `CorrelationMiddleware` | Request tracking | Auto-generates correlation IDs |
| `LoggingMiddleware` | HTTP request/response logging | Performance metrics, filtering |

## Usage Patterns

### Basic Logging

```python
from src.infrastructure.logging import get_logger

logger = get_logger(__name__)

logger.debug("Debug information")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error occurred")
logger.critical("Critical issue")
```

### Structured Logging with Context

```python
logger.info(
    "User created successfully",
    extra={
        "user_id": user.id,
        "email": user.email,
        "registration_source": "api",
        "processing_time_ms": 150,
    }
)
```

### Using Decorators

```python
from src.infrastructure.logging.decorators import (
    log_execution,
    log_error,
    log_performance
)

@log_execution(log_args=True, log_result=True)
@log_performance(threshold_ms=500)
def create_user(email: str, name: str) -> User:
    # Implementation
    pass

@log_error(reraise=True)
async def risky_operation():
    # Implementation that might fail
    pass
```

### Error Logging with Context

```python
try:
    result = risky_operation()
except Exception as e:
    logger.error(
        "Operation failed",
        extra={
            "operation": "risky_operation",
            "error_type": type(e).__name__,
            "user_id": current_user.id,
            "retry_count": attempt_count,
        },
        exc_info=True  # Include full traceback
    )
    raise
```

### Performance Monitoring

```python
import time

start_time = time.perf_counter()
try:
    result = expensive_operation()
    success = True
except Exception as e:
    success = False
    raise
finally:
    duration_ms = (time.perf_counter() - start_time) * 1000
    logger.info(
        "Operation completed",
        extra={
            "operation": "expensive_operation",
            "duration_ms": round(duration_ms, 2),
            "success": success,
        }
    )
```

## AWS Integration

### ECS/Fargate Deployment

The logging system automatically detects ECS environments and configures appropriate settings:

```python
# Automatic ECS detection via ECS_CONTAINER_METADATA_URI_V4
# Enables CloudWatch logging with structured JSON format
```

Example ECS task definition:

```json
{
  "family": "clean-py",
  "taskDefinition": {
    "containerDefinitions": [
      {
        "name": "app",
        "environment": [
          {"name": "LOG_LEVEL", "value": "INFO"},
          {"name": "CLOUDWATCH_ENABLED", "value": "true"},
          {"name": "CLOUDWATCH_LOG_GROUP", "value": "/aws/ecs/clean-py"}
        ],
        "logConfiguration": {
          "logDriver": "awslogs",
          "options": {
            "awslogs-group": "/aws/ecs/clean-py",
            "awslogs-region": "us-east-1",
            "awslogs-stream-prefix": "ecs"
          }
        }
      }
    ]
  }
}
```

### Lambda Deployment

For Lambda functions, use the specialized Lambda utilities:

```python
from src.infrastructure.logging.lambda_utils import configure_lambda_logging

# At module level
configure_lambda_logging(log_level="INFO")
```

Lambda automatically logs to CloudWatch, so the system disables additional CloudWatch handlers and optimizes for Lambda-specific metadata.

### CloudWatch Logs Integration

#### Log Groups Structure
```
/aws/ecs/clean-py/           # ECS containers
/aws/lambda/function-name    # Lambda functions
/aws/apigateway/access-logs  # API Gateway access logs
```

#### CloudWatch Insights Queries

Common queries for the structured logs:

```sql
# Find all errors in the last hour
fields @timestamp, @message, error_type, correlation_id
| filter @level = "ERROR"
| sort @timestamp desc
| limit 100

# Track request performance
fields @timestamp, method, path, duration_ms, status_code
| filter event_type = "request_completed"
| stats avg(duration_ms), max(duration_ms), count() by path
| sort avg desc

# Follow correlation ID across services
fields @timestamp, @message, @level
| filter correlation_id = "your-correlation-id"
| sort @timestamp asc
```

### AWS X-Ray Integration

The correlation ID system integrates with AWS X-Ray tracing:

```python
# Correlation IDs are automatically extracted from X-Amzn-Trace-Id headers
# and propagated through the request lifecycle
```

## Best Practices

See [Logging Best Practices Guide](./best-practices.md) for detailed recommendations.

### Key Principles

1. **Structure Everything**: Use JSON logging with consistent field names
2. **Include Context**: Always add relevant business context to logs
3. **Correlate Requests**: Use correlation IDs for distributed tracing
4. **Monitor Performance**: Log execution times and slow operations
5. **Protect Sensitive Data**: Never log passwords, tokens, or PII
6. **Use Appropriate Levels**: Follow logging level conventions
7. **Sample High Volume**: Use sampling for debug logs in production

### Security Considerations

```python
# ✅ Good - Structured with safe context
logger.info(
    "User login successful",
    extra={
        "user_id": user.id,
        "login_method": "oauth",
        "ip_address": request.client.host,
    }
)

# ❌ Bad - Contains sensitive data
logger.debug(f"Login attempt with password: {password}")

# ❌ Bad - PII in logs
logger.info(f"Processing order for {customer.email}")
```

## Troubleshooting

### Common Issues

#### CloudWatch Handler Not Working

```bash
# Install required dependency
pip install watchtower

# Check AWS credentials
aws sts get-caller-identity

# Verify IAM permissions (logs:CreateLogStream, logs:PutLogEvents)
```

#### Lambda Logs Not Appearing

```python
# Ensure you're calling configure_lambda_logging()
configure_lambda_logging()

# Lambda execution role needs CloudWatch Logs permissions
```

#### High Log Volume

```python
# Use sampling for debug logs
config = LogConfig(
    level="INFO",  # Reduce verbosity
    sampling_rate=0.1,  # Sample 10% of debug logs
)

# Use filtering middleware
app.add_middleware(LoggingMiddleware, skip_paths={"/health", "/metrics"})
```

#### Missing Correlation IDs

```python
# Ensure CorrelationMiddleware is added before LoggingMiddleware
app.add_middleware(CorrelationMiddleware)  # First
app.add_middleware(LoggingMiddleware)      # Second
```

For more troubleshooting information, see the [Troubleshooting Guide](./troubleshooting.md).