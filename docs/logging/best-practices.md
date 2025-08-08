# Logging Best Practices

This guide provides comprehensive best practices for logging in AWS-deployed applications, focusing on security, performance, observability, and maintainability.

## Table of Contents

- [Core Principles](#core-principles)
- [Log Levels and When to Use Them](#log-levels-and-when-to-use-them)
- [Structured Logging](#structured-logging)
- [Security and Compliance](#security-and-compliance)
- [Performance Considerations](#performance-considerations)
- [AWS-Specific Guidelines](#aws-specific-guidelines)
- [Monitoring and Alerting](#monitoring-and-alerting)
- [Development vs Production](#development-vs-production)

## Core Principles

### 1. Log with Purpose

Every log entry should serve a specific purpose:

```python
# ✅ Good - Actionable business event
logger.info(
    "Order payment processed",
    extra={
        "order_id": order.id,
        "amount": order.total_amount,
        "payment_method": "credit_card",
        "processing_time_ms": 250,
    }
)

# ❌ Bad - Debugging leftover
logger.info("Entering function process_payment")
```

### 2. Structure for Searchability

Use consistent field names and structure across your application:

```python
# ✅ Good - Consistent structure
logger.info(
    "Database query executed",
    extra={
        "query_type": "SELECT",
        "table_name": "customers",
        "duration_ms": 45,
        "rows_returned": 100,
    }
)

logger.info(
    "Database query executed", 
    extra={
        "query_type": "INSERT",
        "table_name": "orders",
        "duration_ms": 12,
        "rows_affected": 1,
    }
)
```

### 3. Include Correlation Context

Always include correlation IDs and relevant business context:

```python
from src.infrastructure.logging.correlation import CorrelationContext

def process_order(order_id: str):
    correlation_id = CorrelationContext.get()
    logger.info(
        "Processing order",
        extra={
            "correlation_id": correlation_id,
            "order_id": order_id,
            "user_id": current_user.id,
            "step": "validation",
        }
    )
```

## Log Levels and When to Use Them

### DEBUG
**When**: Detailed diagnostic information for development and troubleshooting
**Production**: Usually disabled or heavily sampled

```python
logger.debug(
    "Cache lookup performed",
    extra={
        "cache_key": key,
        "cache_hit": hit,
        "lookup_time_ms": duration,
    }
)
```

### INFO
**When**: General application flow and business events
**Production**: Standard level for operational visibility

```python
logger.info(
    "User registration completed",
    extra={
        "user_id": user.id,
        "registration_source": "web",
        "email_verified": user.email_verified,
    }
)
```

### WARNING
**When**: Recoverable errors or unexpected but handled situations
**Production**: Requires monitoring but not immediate action

```python
logger.warning(
    "External service timeout, using cached data",
    extra={
        "service": "payment_gateway",
        "timeout_ms": 5000,
        "fallback_strategy": "cached_data",
        "cache_age_minutes": 15,
    }
)
```

### ERROR
**When**: Errors that affect functionality but don't crash the application
**Production**: Requires investigation and potential action

```python
try:
    payment_result = process_payment(order)
except PaymentProcessingError as e:
    logger.error(
        "Payment processing failed",
        extra={
            "order_id": order.id,
            "payment_method": order.payment_method,
            "error_code": e.error_code,
            "retry_count": retry_count,
        },
        exc_info=True
    )
```

### CRITICAL
**When**: Critical errors that may cause system failure
**Production**: Requires immediate attention and alerting

```python
logger.critical(
    "Database connection pool exhausted",
    extra={
        "active_connections": pool.active_count,
        "max_connections": pool.max_connections,
        "pending_requests": pool.pending_count,
        "system_health": "degraded",
    }
)
```

## Structured Logging

### Field Naming Conventions

Use consistent field names across your application:

```python
# Recommended field names
standard_fields = {
    # Identifiers
    "user_id": "unique user identifier",
    "order_id": "unique order identifier", 
    "correlation_id": "request correlation ID",
    "session_id": "user session identifier",
    
    # Metrics
    "duration_ms": "execution time in milliseconds",
    "response_size_bytes": "response size in bytes",
    "memory_usage_mb": "memory usage in megabytes",
    
    # Business Context
    "operation": "business operation name",
    "step": "current process step",
    "status": "operation status",
    "error_code": "application error code",
    
    # Technical Context
    "service_name": "microservice name",
    "version": "application version",
    "environment": "deployment environment",
    "hostname": "server hostname",
}
```

### Complex Data Handling

```python
# ✅ Good - Serialize complex objects safely
logger.info(
    "Order created",
    extra={
        "order": {
            "id": order.id,
            "total_amount": float(order.total_amount),
            "items_count": len(order.items),
            "customer_tier": order.customer.tier,
        }
    }
)

# ❌ Bad - Don't log entire objects
logger.info("Order created", extra={"order": order})
```

### Metrics and Performance Data

```python
import time
from contextlib import contextmanager

@contextmanager
def log_performance(operation: str, **context):
    start_time = time.perf_counter()
    try:
        yield
        success = True
    except Exception as e:
        success = False
        raise
    finally:
        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.info(
            f"{operation} completed",
            extra={
                "operation": operation,
                "duration_ms": round(duration_ms, 2),
                "success": success,
                **context,
            }
        )

# Usage
with log_performance("database_query", table="users", query_type="SELECT"):
    users = db.query_users(filters)
```

## Security and Compliance

### Never Log Sensitive Data

```python
# ❌ Never log these
sensitive_data = [
    "passwords",
    "API keys", 
    "tokens",
    "credit card numbers",
    "SSNs",
    "personal email content",
    "full addresses",
    "phone numbers",
]

# ✅ Use safe alternatives
logger.info(
    "User authentication successful",
    extra={
        "user_id": user.id,  # ✅ Internal ID
        "login_method": "oauth",  # ✅ Method type
        "email_domain": user.email.split("@")[1],  # ✅ Domain only
        "ip_address_hash": hashlib.sha256(ip.encode()).hexdigest()[:8],  # ✅ Hashed IP
    }
)
```

### PII Handling

```python
def safe_user_context(user):
    """Create safe logging context for user data."""
    return {
        "user_id": user.id,
        "user_type": user.account_type,
        "registration_date": user.created_at.date().isoformat(),
        "email_domain": user.email.split("@")[1] if user.email else None,
        "country_code": user.address.country_code if user.address else None,
    }

# Usage
logger.info(
    "User profile updated",
    extra={
        **safe_user_context(user),
        "fields_updated": ["preferences", "notification_settings"],
    }
)
```

### Audit Logging

```python
def audit_log(action: str, resource: str, user_id: str, **details):
    """Log security-relevant actions for audit trails."""
    logger.info(
        f"AUDIT: {action}",
        extra={
            "audit": True,  # Flag for audit log processing
            "action": action,
            "resource": resource,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "source_ip": get_client_ip(),
            **details,
        }
    )

# Usage
audit_log(
    action="user_role_changed",
    resource=f"user:{user.id}",
    user_id=admin_user.id,
    previous_role="user",
    new_role="admin",
)
```

## Performance Considerations

### Log Sampling

```python
import random
from src.infrastructure.logging.handlers import SamplingHandler

# Sample debug logs in high-traffic scenarios
def should_sample_debug() -> bool:
    """Sample debug logs at 10% rate in production."""
    environment = os.getenv("ENVIRONMENT", "local")
    if environment == "production":
        return random.random() < 0.1
    return True

if should_sample_debug():
    logger.debug("Detailed debugging information", extra=context)
```

### Async Logging for High Performance

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

class AsyncLogger:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=2)
        
    async def async_log(self, level, message, **kwargs):
        """Log asynchronously to avoid blocking main thread."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            self.executor,
            lambda: logger.log(level, message, **kwargs)
        )

# Usage in async context
async_logger = AsyncLogger()
await async_logger.async_log(logging.INFO, "Async operation completed")
```

### Conditional Logging

```python
# Avoid expensive operations if logging level won't be used
if logger.isEnabledFor(logging.DEBUG):
    expensive_debug_data = compute_debug_info()
    logger.debug("Debug info", extra={"data": expensive_debug_data})
```

## AWS-Specific Guidelines

### CloudWatch Optimization

```python
# Use CloudWatch-friendly field names (@ prefix for system fields)
logger.info(
    "Request processed",
    extra={
        "@timestamp": datetime.utcnow().isoformat(),
        "@correlationId": correlation_id,
        "@requestId": request_id,
        "custom_field": "value",  # Custom fields without @
    }
)
```

### Lambda Best Practices

```python
from src.infrastructure.logging.lambda_utils import (
    configure_lambda_logging,
    lambda_request_logger,
    lambda_response_logger
)

# Configure once at module level
configure_lambda_logging()

def lambda_handler(event, context):
    # Log request automatically
    lambda_request_logger(event, context)
    
    # Add Lambda-specific context
    logger.info(
        "Processing Lambda request",
        extra={
            "remaining_time_ms": context.get_remaining_time_in_millis(),
            "memory_limit_mb": context.memory_limit_in_mb,
            "cold_start": is_cold_start(),
        }
    )
    
    # Your logic here
    result = process_request(event)
    
    # Log response
    lambda_response_logger(result, context)
    return result
```

### Cost Management

```python
# Estimate CloudWatch Logs costs
def estimate_log_cost(daily_gb: float, retention_days: int = 30) -> float:
    """Estimate monthly CloudWatch Logs cost."""
    ingestion_cost_per_gb = 0.50  # USD
    storage_cost_per_gb_month = 0.03  # USD
    
    monthly_ingestion = daily_gb * 30 * ingestion_cost_per_gb
    storage_gb = daily_gb * retention_days
    monthly_storage = storage_gb * storage_cost_per_gb_month
    
    return monthly_ingestion + monthly_storage

# Monitor log volume
logger.info(
    "Log volume metric",
    extra={
        "metric_type": "log_volume",
        "daily_gb_estimate": estimate_daily_gb(),
        "estimated_monthly_cost": estimate_log_cost(daily_gb),
    }
)
```

## Monitoring and Alerting

### Health Check Logging

```python
@app.get("/health")
async def health_check():
    health_status = {
        "status": "healthy",
        "checks": {},
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    # Check database
    try:
        await db.execute("SELECT 1")
        health_status["checks"]["database"] = "healthy"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = "failed"
        logger.error(
            "Database health check failed",
            extra={"error": str(e)},
            exc_info=True
        )
    
    # Check external services
    try:
        await external_service.ping()
        health_status["checks"]["external_service"] = "healthy"
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["checks"]["external_service"] = "failed"
        logger.warning(
            "External service health check failed",
            extra={"service": "payment_gateway", "error": str(e)}
        )
    
    # Log health status
    log_level = logging.INFO if health_status["status"] == "healthy" else logging.ERROR
    logger.log(
        log_level,
        f"Health check: {health_status['status']}",
        extra={"health_check": health_status}
    )
    
    return health_status
```

### Error Rate Monitoring

```python
class ErrorRateMonitor:
    def __init__(self):
        self.error_counts = {}
        self.request_counts = {}
    
    def log_request(self, endpoint: str, success: bool):
        # Increment counters
        self.request_counts[endpoint] = self.request_counts.get(endpoint, 0) + 1
        if not success:
            self.error_counts[endpoint] = self.error_counts.get(endpoint, 0) + 1
        
        # Log metrics periodically
        if self.request_counts[endpoint] % 100 == 0:
            error_rate = self.error_counts.get(endpoint, 0) / self.request_counts[endpoint]
            logger.info(
                "Endpoint error rate",
                extra={
                    "metric_type": "error_rate",
                    "endpoint": endpoint,
                    "error_rate": error_rate,
                    "total_requests": self.request_counts[endpoint],
                    "total_errors": self.error_counts.get(endpoint, 0),
                }
            )

# Usage
monitor = ErrorRateMonitor()
monitor.log_request("/api/orders", success=True)
```

### Custom Metrics

```python
def log_business_metric(metric_name: str, value: float, unit: str = "count", **dimensions):
    """Log custom business metrics for monitoring."""
    logger.info(
        f"Business metric: {metric_name}",
        extra={
            "metric_type": "business",
            "metric_name": metric_name,
            "metric_value": value,
            "metric_unit": unit,
            "dimensions": dimensions,
            "timestamp": datetime.utcnow().isoformat(),
        }
    )

# Usage
log_business_metric(
    "orders_completed",
    value=1,
    unit="count",
    payment_method="credit_card",
    customer_tier="premium"
)

log_business_metric(
    "revenue_generated",
    value=float(order.total_amount),
    unit="dollars",
    product_category=order.primary_category
)
```

## Development vs Production

### Environment-Specific Configuration

```python
def get_logging_config_for_environment():
    environment = os.getenv("ENVIRONMENT", "local")
    
    if environment == "local":
        return LogConfig(
            level="DEBUG",
            format="text",  # Human-readable for development
            log_request_body=True,
            log_response_body=True,
            include_hostname=True,
        )
    elif environment in ["staging", "development"]:
        return LogConfig(
            level="INFO",
            format="json",
            cloudwatch_enabled=True,
            sampling_rate=0.5,  # Sample some debug logs
        )
    else:  # production
        return LogConfig(
            level="INFO",
            format="cloudwatch",
            cloudwatch_enabled=True,
            sampling_rate=0.1,  # Heavy sampling for debug
            log_request_body=False,
            log_response_body=False,
        )
```

### Testing Considerations

```python
import pytest
from unittest.mock import Mock
from src.infrastructure.logging import get_logger

def test_user_creation_logging(caplog):
    """Test that user creation is properly logged."""
    logger = get_logger(__name__)
    
    with caplog.at_level(logging.INFO):
        create_user("test@example.com", "Test User")
    
    # Verify log was created
    assert "User created successfully" in caplog.text
    
    # Verify structured data
    log_record = caplog.records[0]
    assert log_record.user_id is not None
    assert log_record.email_domain == "example.com"

@pytest.fixture
def mock_logger():
    """Provide mock logger for testing."""
    return Mock(spec=logging.Logger)
```

Remember: The goal of logging is observability, not just recording events. Every log should help you understand, debug, or monitor your system's behavior.