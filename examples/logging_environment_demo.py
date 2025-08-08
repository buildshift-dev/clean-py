#!/usr/bin/env python3
"""
Demonstration of automatic environment detection for logging configuration.

This script shows how the logging system automatically detects whether it's
running locally or in AWS and configures logging appropriately.
"""

import os
import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

try:
    from src.infrastructure.logging import configure_logging, get_logger
    from src.infrastructure.logging.config import get_log_config, _is_running_locally
except ImportError:
    print("Could not import logging modules. Make sure you're running from the project root.")
    print(f"Tried to import from: {src_path}")
    sys.exit(1)

def demo_environment_detection():
    """Demonstrate environment detection and logging configuration."""
    print("=" * 60)
    print("Logging Environment Detection Demo")
    print("=" * 60)
    
    # Show current environment detection
    is_local = _is_running_locally()
    print(f"Environment detected: {'Local' if is_local else 'AWS'}")
    
    # Show configuration
    config = get_log_config()
    print(f"Log Level: {config.level}")
    print(f"Log Format: {config.format}")
    print(f"CloudWatch Enabled: {config.cloudwatch_enabled}")
    print(f"Environment: {config.environment}")
    print()
    
    # Configure logging
    configure_logging()
    logger = get_logger(__name__)
    
    # Test logging at different levels
    print("Testing log output:")
    print("-" * 30)
    
    logger.debug("This is a debug message - shows locally, sampled in AWS")
    logger.info("This is an info message - always shows")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    
    # Test structured logging
    logger.info(
        "User action performed",
        extra={
            "user_id": "user_123",
            "action": "create_order",
            "duration_ms": 245,
            "success": True,
        }
    )
    
    print("-" * 30)
    print("Demo completed!")

def demo_different_environments():
    """Demonstrate how different environment variables affect detection."""
    print("\n" + "=" * 60)
    print("Testing Different Environment Scenarios")
    print("=" * 60)
    
    # Save original environment
    original_env = dict(os.environ)
    
    scenarios = [
        {
            "name": "Pure Local (no env vars)",
            "env_vars": {},
            "clear_aws": True,
        },
        {
            "name": "Local Docker Compose",
            "env_vars": {
                "DOCKER_COMPOSE_PROJECT_NAME": "clean-py",
                "ENVIRONMENT": "local"
            },
            "clear_aws": True,
        },
        {
            "name": "Local with DEBUG level",
            "env_vars": {
                "ENVIRONMENT": "local",
                "LOG_LEVEL": "DEBUG"
            },
            "clear_aws": True,
        },
        {
            "name": "Simulated AWS ECS",
            "env_vars": {
                "ECS_CONTAINER_METADATA_URI_V4": "http://169.254.170.2/v4/12345",
                "AWS_REGION": "us-west-2",
                "ENVIRONMENT": "production"
            },
            "clear_aws": False,
        },
        {
            "name": "Simulated AWS Lambda",
            "env_vars": {
                "AWS_LAMBDA_FUNCTION_NAME": "clean-py-handler",
                "AWS_EXECUTION_ENV": "AWS_Lambda_python3.11",
                "AWS_REGION": "us-east-1"
            },
            "clear_aws": False,
        }
    ]
    
    for scenario in scenarios:
        print(f"\nScenario: {scenario['name']}")
        print("-" * 40)
        
        # Clear environment if needed
        if scenario.get("clear_aws"):
            aws_vars = ["AWS_REGION", "AWS_LAMBDA_FUNCTION_NAME", "ECS_CONTAINER_METADATA_URI_V4", 
                       "AWS_EXECUTION_ENV", "AWS_BATCH_JOB_ID"]
            for var in aws_vars:
                os.environ.pop(var, None)
        
        # Set scenario environment
        for key, value in scenario["env_vars"].items():
            os.environ[key] = value
        
        # Clear the cached detection result
        if hasattr(get_log_config, '_logged_detection'):
            delattr(get_log_config, '_logged_detection')
        
        # Get configuration
        is_local = _is_running_locally()
        config = get_log_config()
        
        print(f"  Detected as: {'Local' if is_local else 'AWS'}")
        print(f"  Log Level: {config.level}")
        print(f"  Log Format: {config.format}")
        print(f"  CloudWatch: {config.cloudwatch_enabled}")
        print(f"  Debug Details: {config.log_request_body}")
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)

def demo_override_behavior():
    """Demonstrate how to override automatic detection."""
    print("\n" + "=" * 60)
    print("Environment Override Examples")
    print("=" * 60)
    
    # Save original environment
    original_env = dict(os.environ)
    
    print("\n1. Force CloudWatch in local environment:")
    os.environ.update({
        "ENVIRONMENT": "local",
        "FORCE_CLOUDWATCH": "true",
        "CLOUDWATCH_ENABLED": "true",
        "CLOUDWATCH_LOG_GROUP": "/aws/test/local"
    })
    
    # Clear cached detection
    if hasattr(get_log_config, '_logged_detection'):
        delattr(get_log_config, '_logged_detection')
    
    config = get_log_config()
    print(f"  Environment: {config.environment}")
    print(f"  CloudWatch Enabled: {config.cloudwatch_enabled}")
    print(f"  Note: CloudWatch handler will still fail without AWS credentials")
    
    print("\n2. Force local-style logging in AWS:")
    os.environ.update({
        "ECS_CONTAINER_METADATA_URI_V4": "http://169.254.170.2/v4/12345",
        "LOG_FORMAT": "text",
        "LOG_LEVEL": "DEBUG",
        "CLOUDWATCH_ENABLED": "false"
    })
    
    # Clear cached detection
    if hasattr(get_log_config, '_logged_detection'):
        delattr(get_log_config, '_logged_detection')
    
    config = get_log_config()
    print(f"  Environment: {config.environment}")
    print(f"  Log Format: {config.format}")
    print(f"  CloudWatch Enabled: {config.cloudwatch_enabled}")
    print(f"  Note: Manual overrides take precedence")
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)

if __name__ == "__main__":
    demo_environment_detection()
    demo_different_environments()
    demo_override_behavior()
    
    print("\n" + "=" * 60)
    print("How to use in your applications:")
    print("=" * 60)
    print("""
Local Development:
    python your_app.py
    # Automatically uses console logging with DEBUG level
    
Docker Compose:
    DOCKER_COMPOSE_PROJECT_NAME=myapp docker-compose up
    # Automatically detects local Docker environment
    
AWS ECS:
    # Set in ECS task definition
    ECS_CONTAINER_METADATA_URI_V4=<uri>
    CLOUDWATCH_LOG_GROUP=/aws/ecs/myapp
    # Automatically uses CloudWatch logging
    
AWS Lambda:
    # AWS_LAMBDA_FUNCTION_NAME is automatically set
    # Automatically uses CloudWatch-optimized logging
    
Override Detection:
    FORCE_CLOUDWATCH=true  # Force CloudWatch in local
    LOG_FORMAT=text        # Force console format anywhere
    LOG_LEVEL=DEBUG        # Override log level
    """)