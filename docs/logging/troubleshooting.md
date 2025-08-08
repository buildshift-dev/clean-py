# Logging Troubleshooting Guide

This guide helps you diagnose and resolve common logging issues in AWS-deployed Clean Architecture applications.

## Table of Contents

- [Common Issues](#common-issues)
- [CloudWatch Problems](#cloudwatch-problems)
- [Lambda Logging Issues](#lambda-logging-issues)
- [Performance Problems](#performance-problems)
- [Configuration Issues](#configuration-issues)
- [Debugging Tools](#debugging-tools)

## Common Issues

### 1. Logs Not Appearing

**Symptoms:**
- No logs in CloudWatch
- Silent application failures
- Missing log entries

**Diagnosis:**
```python
# Add this to your application startup to verify logging is working
from src.infrastructure.logging import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)

# Test basic logging
logger.info("Logging system initialized")
logger.error("Test error message")

# Check if handlers are configured
import logging
root_logger = logging.getLogger()
print(f"Root logger level: {root_logger.level}")
print(f"Handlers count: {len(root_logger.handlers)}")
for handler in root_logger.handlers:
    print(f"Handler: {type(handler).__name__}, Level: {handler.level}")
```

**Solutions:**
1. **Check log level configuration:**
   ```bash
   # Ensure LOG_LEVEL allows your messages
   export LOG_LEVEL=DEBUG  # or INFO, WARNING, ERROR
   ```

2. **Verify handler configuration:**
   ```python
   # Manually add console handler for testing
   import logging
   import sys
   
   root_logger = logging.getLogger()
   handler = logging.StreamHandler(sys.stdout)
   handler.setLevel(logging.DEBUG)
   formatter = logging.Formatter('%(levelname)s - %(message)s')
   handler.setFormatter(formatter)
   root_logger.addHandler(handler)
   root_logger.setLevel(logging.DEBUG)
   ```

### 2. Missing Correlation IDs

**Symptoms:**
- Correlation IDs not appearing in logs
- Cannot trace requests across services

**Diagnosis:**
```python
from src.infrastructure.logging.correlation import CorrelationContext

# Check if correlation ID is set
correlation_id = CorrelationContext.get()
print(f"Current correlation ID: {correlation_id}")

# Manually set for testing
CorrelationContext.set("test-correlation-123")
logger.info("Test message with correlation ID")
```

**Solutions:**
1. **Ensure middleware is properly configured:**
   ```python
   from fastapi import FastAPI
   from src.infrastructure.logging import CorrelationMiddleware, LoggingMiddleware
   
   app = FastAPI()
   
   # Order matters! Correlation middleware must be added first
   app.add_middleware(CorrelationMiddleware)
   app.add_middleware(LoggingMiddleware)
   ```

2. **For Lambda functions:**
   ```python
   from src.infrastructure.logging.lambda_utils import lambda_request_logger
   
   def lambda_handler(event, context):
       # This automatically sets correlation ID
       lambda_request_logger(event, context)
       # Your code here
   ```

### 3. Sensitive Data in Logs

**Symptoms:**
- Personal information appearing in logs
- Security compliance violations
- API keys or tokens in log files

**Diagnosis:**
```bash
# Search for potential sensitive data patterns
grep -r "password\|token\|key\|secret" /var/log/
grep -r "@.*\.com" /var/log/  # Email patterns
grep -r "\d{4}.\d{4}.\d{4}.\d{4}" /var/log/  # Credit card patterns
```

**Solutions:**
1. **Review logging calls:**
   ```python
   # ❌ Bad - logs sensitive data
   logger.info(f"User login: {user.email}, password: {password}")
   
   # ✅ Good - logs safe data only
   logger.info(
       "User login successful",
       extra={
           "user_id": user.id,
           "email_domain": user.email.split("@")[1],
           "login_method": "oauth",
       }
   )
   ```

2. **Use header filtering:**
   ```python
   from src.infrastructure.logging import LoggingMiddleware
   
   app.add_middleware(
       LoggingMiddleware,
       sensitive_headers={"authorization", "x-api-key", "cookie"}
   )
   ```

### 4. High Log Volume and Costs

**Symptoms:**
- High CloudWatch costs
- Performance degradation
- Storage quota exceeded

**Diagnosis:**
```python
# Check log volume
import os
from datetime import datetime, timedelta

def estimate_daily_log_volume():
    """Rough estimate of daily log volume."""
    log_dir = "/var/log"  # Adjust path
    total_size = 0
    
    for root, dirs, files in os.walk(log_dir):
        for file in files:
            if file.endswith(".log"):
                file_path = os.path.join(root, file)
                try:
                    size = os.path.getsize(file_path)
                    total_size += size
                except OSError:
                    continue
    
    # Convert to GB
    size_gb = total_size / (1024 * 1024 * 1024)
    return size_gb
```

**Solutions:**
1. **Implement log sampling:**
   ```python
   from src.infrastructure.logging import LogConfig
   
   config = LogConfig(
       level="INFO",  # Reduce verbosity
       sampling_rate=0.1,  # Sample 10% of debug logs
   )
   ```

2. **Use path filtering:**
   ```python
   app.add_middleware(
       LoggingMiddleware,
       skip_paths={"/health", "/metrics", "/ping"}
   )
   ```

3. **Set appropriate retention:**
   ```bash
   # Set CloudWatch log retention via AWS CLI
   aws logs put-retention-policy \
       --log-group-name "/aws/ecs/clean-py" \
       --retention-in-days 7
   ```

## CloudWatch Problems

### 1. CloudWatch Handler Not Working

**Error Messages:**
```
WARNING:watchtower:Failed to send logs to CloudWatch
NoCredentialsError: Unable to locate credentials
```

**Solutions:**
1. **Check AWS credentials:**
   ```bash
   aws sts get-caller-identity
   aws logs describe-log-groups --limit 1
   ```

2. **Verify IAM permissions:**
   ```json
   {
       "Version": "2012-10-17",
       "Statement": [
           {
               "Effect": "Allow",
               "Action": [
                   "logs:CreateLogStream",
                   "logs:PutLogEvents",
                   "logs:DescribeLogGroups",
                   "logs:DescribeLogStreams"
               ],
               "Resource": "arn:aws:logs:*:*:log-group:/aws/ecs/clean-py:*"
           }
       ]
   }
   ```

3. **Install required dependencies:**
   ```bash
   pip install watchtower boto3
   ```

4. **Test CloudWatch connectivity:**
   ```python
   import boto3
   from watchtower import CloudWatchLogHandler
   
   try:
       client = boto3.client('logs', region_name='us-east-1')
       handler = CloudWatchLogHandler(
           log_group='/aws/test/logs',
           boto3_client=client
       )
       print("CloudWatch handler created successfully")
   except Exception as e:
       print(f"CloudWatch handler failed: {e}")
   ```

### 2. Log Group Not Found

**Error Messages:**
```
ResourceNotFoundException: The specified log group does not exist
```

**Solutions:**
1. **Create log group manually:**
   ```bash
   aws logs create-log-group --log-group-name "/aws/ecs/clean-py"
   ```

2. **Create via Terraform/CloudFormation:**
   ```hcl
   resource "aws_cloudwatch_log_group" "app_logs" {
     name              = "/aws/ecs/clean-py"
     retention_in_days = 30
   }
   ```

3. **Auto-create in application (not recommended for production):**
   ```python
   import boto3
   
   def ensure_log_group_exists(log_group_name, region='us-east-1'):
       client = boto3.client('logs', region_name=region)
       try:
           client.describe_log_groups(logGroupNamePrefix=log_group_name)
       except client.exceptions.ResourceNotFoundException:
           client.create_log_group(logGroupName=log_group_name)
   ```

### 3. CloudWatch Insights Queries Not Working

**Problem:** Cannot find logs in CloudWatch Insights

**Solutions:**
1. **Check field names in queries:**
   ```sql
   # Use @ prefix for CloudWatch formatter fields
   fields @timestamp, @message, @level
   | filter @level = "ERROR"
   | sort @timestamp desc
   ```

2. **Verify JSON structure:**
   ```python
   # Log a test message and check structure
   logger.info(
       "CloudWatch Insights test",
       extra={
           "test_field": "test_value",
           "numeric_field": 123,
       }
   )
   ```

## Lambda Logging Issues

### 1. Lambda Logs Not Appearing

**Symptoms:**
- No logs in CloudWatch for Lambda function
- Lambda execution completes but no log output

**Solutions:**
1. **Check Lambda execution role:**
   ```json
   {
       "Version": "2012-10-17",
       "Statement": [
           {
               "Effect": "Allow",
               "Action": [
                   "logs:CreateLogGroup",
                   "logs:CreateLogStream", 
                   "logs:PutLogEvents"
               ],
               "Resource": "arn:aws:logs:*:*:*"
           }
       ]
   }
   ```

2. **Use Lambda logging utilities:**
   ```python
   from src.infrastructure.logging.lambda_utils import configure_lambda_logging
   
   # Call at module level, not inside handler
   configure_lambda_logging()
   ```

3. **Test basic logging:**
   ```python
   import json
   
   def lambda_handler(event, context):
       print("Basic print statement")  # This should always appear
       
       import logging
       logging.basicConfig(level=logging.INFO)
       logger = logging.getLogger(__name__)
       logger.info("Logger test message")
       
       return {
           'statusCode': 200,
           'body': json.dumps('Hello from Lambda!')
       }
   ```

### 2. Cold Start Logging Issues

**Problem:** Logging configuration lost on cold starts

**Solutions:**
1. **Configure logging at module level:**
   ```python
   # At top of file, not inside handler
   from src.infrastructure.logging.lambda_utils import configure_lambda_logging
   configure_lambda_logging()
   
   def lambda_handler(event, context):
       # Handler code here
       pass
   ```

2. **Use global logger instance:**
   ```python
   from src.infrastructure.logging import get_logger
   
   # Global logger instance
   logger = get_logger(__name__)
   
   def lambda_handler(event, context):
       logger.info("Handler started")
       # Handler code
   ```

## Performance Problems

### 1. Slow Application Performance

**Symptoms:**
- High latency in API responses
- Timeouts in Lambda functions
- CPU/memory spikes

**Diagnosis:**
```python
# Add performance monitoring to logging
import time
from src.infrastructure.logging.decorators import log_performance

@log_performance(threshold_ms=100)
def slow_function():
    time.sleep(0.2)  # Simulate slow operation
    return "result"

# Check for slow log operations
start_time = time.perf_counter()
logger.info("Test message")
duration = (time.perf_counter() - start_time) * 1000
if duration > 10:  # If logging takes more than 10ms
    print(f"Slow logging detected: {duration:.2f}ms")
```

**Solutions:**
1. **Use async logging:**
   ```python
   import asyncio
   import concurrent.futures
   
   def async_log(logger, level, message, **kwargs):
       loop = asyncio.get_event_loop()
       executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
       return loop.run_in_executor(
           executor,
           lambda: logger.log(level, message, **kwargs)
       )
   ```

2. **Implement log batching:**
   ```python
   from src.infrastructure.logging.handlers import BufferingHandler
   
   # Buffer logs and flush periodically
   console_handler = get_console_handler(config)
   buffered_handler = BufferingHandler(
       handler=console_handler,
       buffer_size=50,  # Flush every 50 messages
   )
   ```

3. **Use conditional logging:**
   ```python
   # Avoid expensive operations if not needed
   if logger.isEnabledFor(logging.DEBUG):
       expensive_debug_data = generate_debug_info()
       logger.debug("Debug info", extra={"data": expensive_debug_data})
   ```

### 2. Memory Leaks from Logging

**Symptoms:**
- Gradual memory increase
- Out of memory errors
- Log handler accumulation

**Solutions:**
1. **Properly close handlers:**
   ```python
   import atexit
   from src.infrastructure.logging.logger import shutdown_logging
   
   # Register cleanup function
   atexit.register(shutdown_logging)
   ```

2. **Limit log retention in memory:**
   ```python
   from logging.handlers import RotatingFileHandler
   
   handler = RotatingFileHandler(
       filename="app.log",
       maxBytes=10*1024*1024,  # 10MB
       backupCount=5
   )
   ```

## Configuration Issues

### 1. Environment Variables Not Working

**Problem:** Configuration not loading from environment

**Diagnosis:**
```python
import os
from src.infrastructure.logging.config import get_log_config

# Check environment variables
print("LOG_LEVEL:", os.getenv("LOG_LEVEL", "NOT_SET"))
print("ENVIRONMENT:", os.getenv("ENVIRONMENT", "NOT_SET"))
print("CLOUDWATCH_ENABLED:", os.getenv("CLOUDWATCH_ENABLED", "NOT_SET"))

# Check parsed configuration
config = get_log_config()
print(f"Parsed config: {config}")
```

**Solutions:**
1. **Verify environment variable format:**
   ```bash
   # Correct format
   export LOG_LEVEL=INFO
   export CLOUDWATCH_ENABLED=true
   
   # Incorrect format
   export LOG_LEVEL="INFO"  # Quotes can cause issues
   export CLOUDWATCH_ENABLED=True  # Case sensitive
   ```

2. **Use explicit configuration:**
   ```python
   from src.infrastructure.logging import LogConfig, configure_logging
   
   # Explicit configuration instead of environment
   config = LogConfig(
       level="INFO",
       cloudwatch_enabled=True,
       cloudwatch_log_group="/aws/ecs/clean-py"
   )
   configure_logging(config)
   ```

## Debugging Tools

### 1. Log Configuration Inspector

```python
def inspect_logging_configuration():
    """Inspect current logging configuration for debugging."""
    import logging
    
    print("=== Logging Configuration Inspection ===")
    
    # Root logger info
    root_logger = logging.getLogger()
    print(f"Root logger level: {logging.getLevelName(root_logger.level)}")
    print(f"Root logger handlers: {len(root_logger.handlers)}")
    
    for i, handler in enumerate(root_logger.handlers):
        print(f"  Handler {i}: {type(handler).__name__}")
        print(f"    Level: {logging.getLevelName(handler.level)}")
        print(f"    Formatter: {type(handler.formatter).__name__ if handler.formatter else 'None'}")
    
    # Test logging at all levels
    print("\n=== Test Messages ===")
    test_logger = logging.getLogger("test.inspector")
    
    test_logger.debug("DEBUG level test")
    test_logger.info("INFO level test") 
    test_logger.warning("WARNING level test")
    test_logger.error("ERROR level test")
    test_logger.critical("CRITICAL level test")
    
    print("=== End Inspection ===")

# Run the inspector
inspect_logging_configuration()
```

### 2. CloudWatch Connectivity Tester

```python
def test_cloudwatch_connectivity():
    """Test CloudWatch Logs connectivity."""
    import boto3
    from botocore.exceptions import NoCredentialsError, ClientError
    
    try:
        client = boto3.client('logs', region_name='us-east-1')
        
        # Test basic connectivity
        response = client.describe_log_groups(limit=1)
        print("✅ CloudWatch connectivity OK")
        
        # Test permissions
        test_group = "/aws/test/connectivity"
        try:
            client.create_log_group(logGroupName=test_group)
            client.delete_log_group(logGroupName=test_group)
            print("✅ CloudWatch permissions OK")
        except ClientError as e:
            if "ResourceAlreadyExistsException" in str(e):
                print("✅ CloudWatch permissions OK (log group exists)")
            else:
                print(f"❌ CloudWatch permissions issue: {e}")
        
    except NoCredentialsError:
        print("❌ No AWS credentials found")
    except Exception as e:
        print(f"❌ CloudWatch connectivity failed: {e}")

# Run the test
test_cloudwatch_connectivity()
```

### 3. Log Message Tracer

```python
def trace_log_message():
    """Trace a log message through the logging system."""
    import logging
    from src.infrastructure.logging import get_logger, configure_logging
    
    class TracingHandler(logging.Handler):
        def emit(self, record):
            print(f"TRACE: Handler received record: {record.getMessage()}")
            print(f"TRACE: Record level: {record.levelname}")
            print(f"TRACE: Record logger: {record.name}")
            if hasattr(record, 'correlation_id'):
                print(f"TRACE: Correlation ID: {record.correlation_id}")
    
    # Add tracing handler
    root_logger = logging.getLogger()
    tracer = TracingHandler()
    root_logger.addHandler(tracer)
    
    # Configure logging
    configure_logging()
    
    # Test message
    logger = get_logger("tracer.test")
    logger.info("Traced message", extra={"test_field": "test_value"})
    
    # Remove tracer
    root_logger.removeHandler(tracer)

# Run the tracer
trace_log_message()
```

For additional help, check the AWS CloudWatch Logs documentation and the watchtower library documentation for specific error codes and solutions.