"""Tests for logging configuration module."""

import os
from typing import Any
from unittest.mock import patch

import pytest

from src.infrastructure.logging.config import (
    Environment,
    LogConfig,
    LogFormat,
    LogLevel,
    get_log_config,
)


class TestLogConfig:
    """Test LogConfig model validation and defaults."""

    def test_default_configuration(self):
        """Test default configuration values."""
        config = LogConfig()

        assert config.level == LogLevel.INFO
        assert config.format == LogFormat.JSON
        assert config.environment == Environment.LOCAL
        assert config.service_name == "clean-py"
        assert config.version == "1.0.0"
        assert config.cloudwatch_enabled is False
        assert config.cloudwatch_log_group is None
        assert config.cloudwatch_region == "us-east-1"
        assert config.log_request_body is False
        assert config.log_response_body is False
        assert config.slow_request_threshold_ms == 1000
        assert config.sampling_rate == 1.0
        assert config.include_hostname is True
        assert config.include_process_info is True

    def test_custom_configuration(self):
        """Test custom configuration values."""
        config = LogConfig(
            level=LogLevel.DEBUG,
            format=LogFormat.CLOUDWATCH,
            environment=Environment.PRODUCTION,
            service_name="test-service",
            version="2.0.0",
            cloudwatch_enabled=True,
            cloudwatch_log_group="/aws/test/logs",
            cloudwatch_region="us-west-2",
            log_request_body=True,
            slow_request_threshold_ms=500,
            sampling_rate=0.5,
        )

        assert config.level == LogLevel.DEBUG
        assert config.format == LogFormat.CLOUDWATCH
        assert config.environment == Environment.PRODUCTION
        assert config.service_name == "test-service"
        assert config.version == "2.0.0"
        assert config.cloudwatch_enabled is True
        assert config.cloudwatch_log_group == "/aws/test/logs"
        assert config.cloudwatch_region == "us-west-2"
        assert config.log_request_body is True
        assert config.slow_request_threshold_ms == 500
        assert config.sampling_rate == 0.5

    def test_sampling_rate_validation(self):
        """Test sampling rate validation bounds."""
        # Valid sampling rates
        config = LogConfig(sampling_rate=0.0)
        assert config.sampling_rate == 0.0

        config = LogConfig(sampling_rate=1.0)
        assert config.sampling_rate == 1.0

        config = LogConfig(sampling_rate=0.5)
        assert config.sampling_rate == 0.5

        # Invalid sampling rates should raise validation error
        with pytest.raises(ValueError):
            LogConfig(sampling_rate=-0.1)

        with pytest.raises(ValueError):
            LogConfig(sampling_rate=1.1)


class TestGetLogConfig:
    """Test get_log_config function with environment variables."""

    def test_default_environment_config(self):
        """Test configuration with no environment variables set (local environment)."""
        with patch.dict(os.environ, {}, clear=True):
            config = get_log_config()

            # Local environment defaults to DEBUG and TEXT format
            assert config.level == LogLevel.DEBUG
            assert config.format == LogFormat.TEXT
            assert config.environment == Environment.LOCAL
            assert config.service_name == "clean-py"
            assert config.version == "dev"

    @patch("src.infrastructure.logging.config._is_running_locally")
    def test_environment_variables_override(self, mock_is_local: Any) -> None:
        """Test configuration with environment variables in AWS environment."""
        # Force AWS environment detection
        mock_is_local.return_value = False

        env_vars = {
            "LOG_LEVEL": "DEBUG",
            "LOG_FORMAT": "text",
            "ENVIRONMENT": "production",
            "SERVICE_NAME": "test-app",
            "SERVICE_VERSION": "3.0.0",
            "CLOUDWATCH_ENABLED": "true",
            "CLOUDWATCH_LOG_GROUP": "/aws/test/app",
            "CLOUDWATCH_LOG_STREAM": "test-stream",
            "AWS_REGION": "eu-west-1",
            "LOG_REQUEST_BODY": "true",
            "LOG_RESPONSE_BODY": "true",
            "SLOW_REQUEST_THRESHOLD_MS": "2000",
            "LOG_SAMPLING_RATE": "0.3",
            "LOG_INCLUDE_HOSTNAME": "false",
            "LOG_INCLUDE_PROCESS_INFO": "false",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            config = get_log_config()

            assert config.level == LogLevel.DEBUG
            assert config.format == LogFormat.TEXT  # Overridden from AWS default
            assert config.environment == Environment.PRODUCTION
            assert config.service_name == "test-app"
            assert config.version == "3.0.0"
            assert config.cloudwatch_enabled is True
            assert config.cloudwatch_log_group == "/aws/test/app"
            assert config.cloudwatch_log_stream == "test-stream"
            assert config.cloudwatch_region == "eu-west-1"
            assert config.log_request_body is True
            assert config.log_response_body is True
            assert config.slow_request_threshold_ms == 2000
            assert config.sampling_rate == 0.3
            assert config.include_hostname is False
            assert config.include_process_info is False

    def test_lambda_environment_detection(self):
        """Test automatic Lambda environment detection."""
        env_vars = {
            "AWS_LAMBDA_FUNCTION_NAME": "test-function",
            "LOG_LEVEL": "INFO",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            config = get_log_config()

            assert config.environment == Environment.PRODUCTION
            assert config.format == LogFormat.CLOUDWATCH
            assert config.cloudwatch_enabled is False  # Lambda logs automatically
            assert config.include_process_info is False

    def test_ecs_environment_detection(self):
        """Test automatic ECS environment detection."""
        env_vars = {
            "ECS_CONTAINER_METADATA_URI_V4": "http://169.254.170.2/v4/12345",
            "LOG_LEVEL": "INFO",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            config = get_log_config()

            assert config.cloudwatch_enabled is True
            assert config.format == LogFormat.JSON

    @patch("src.infrastructure.logging.config._is_running_locally")
    def test_boolean_environment_parsing(self, mock_is_local: Any) -> None:
        """Test boolean environment variable parsing in AWS environment."""
        # Force AWS environment detection
        mock_is_local.return_value = False

        # Test various truthy values
        truthy_values = ["true", "True", "TRUE", "1", "yes", "Yes"]
        for value in truthy_values:
            with patch.dict(os.environ, {"CLOUDWATCH_ENABLED": value}, clear=True):
                config = get_log_config()
                assert config.cloudwatch_enabled is True, f"Failed for value: {value}"

        # Test various falsy values
        falsy_values = ["false", "False", "FALSE", "0", "no", "No", ""]
        for value in falsy_values:
            with patch.dict(os.environ, {"CLOUDWATCH_ENABLED": value}, clear=True):
                config = get_log_config()
                assert config.cloudwatch_enabled is False, f"Failed for value: {value}"

    def test_integer_environment_parsing(self):
        """Test integer environment variable parsing."""
        with patch.dict(os.environ, {"SLOW_REQUEST_THRESHOLD_MS": "5000"}, clear=True):
            config = get_log_config()
            assert config.slow_request_threshold_ms == 5000

    @patch("src.infrastructure.logging.config._is_running_locally")
    def test_float_environment_parsing(self, mock_is_local: Any) -> None:
        """Test float environment variable parsing in AWS environment."""
        # Force AWS environment detection
        mock_is_local.return_value = False

        with patch.dict(os.environ, {"LOG_SAMPLING_RATE": "0.25"}, clear=True):
            config = get_log_config()
            assert config.sampling_rate == 0.25

    @patch("src.infrastructure.logging.config._is_running_locally")
    def test_invalid_enum_values(self, mock_is_local: Any) -> None:
        """Test handling of invalid enum values in AWS environment."""
        # Force AWS environment detection to test enum validation
        mock_is_local.return_value = False

        with (
            patch.dict(os.environ, {"LOG_LEVEL": "INVALID"}, clear=True),
            pytest.raises(ValueError, match="'INVALID' is not a valid LogLevel"),
        ):
            get_log_config()

        with (
            patch.dict(os.environ, {"LOG_FORMAT": "invalid"}, clear=True),
            pytest.raises(ValueError, match="'invalid' is not a valid LogFormat"),
        ):
            get_log_config()

        with (
            patch.dict(os.environ, {"ENVIRONMENT": "invalid"}, clear=True),
            pytest.raises(ValueError, match="'invalid' is not a valid Environment"),
        ):
            get_log_config()


class TestLogConfigIntegration:
    """Integration tests for log configuration."""

    @patch("src.infrastructure.logging.config._is_running_locally")
    def test_production_like_config(self, mock_is_local: Any) -> None:
        """Test production-like configuration in AWS environment."""
        # Force AWS environment detection
        mock_is_local.return_value = False

        env_vars = {
            "ENVIRONMENT": "production",
            "LOG_LEVEL": "INFO",
            "LOG_FORMAT": "cloudwatch",
            "SERVICE_NAME": "ecommerce-api",
            "SERVICE_VERSION": "2.1.0",
            "CLOUDWATCH_ENABLED": "true",
            "CLOUDWATCH_LOG_GROUP": "/aws/ecs/ecommerce-api",
            "AWS_REGION": "us-west-2",
            "LOG_REQUEST_BODY": "false",
            "LOG_RESPONSE_BODY": "false",
            "SLOW_REQUEST_THRESHOLD_MS": "1000",
            "LOG_SAMPLING_RATE": "0.1",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            config = get_log_config()

            # Verify production settings
            assert config.environment == Environment.PRODUCTION
            assert config.level == LogLevel.INFO
            assert config.format == LogFormat.CLOUDWATCH
            assert config.cloudwatch_enabled is True
            assert config.log_request_body is False
            assert config.log_response_body is False
            assert config.sampling_rate == 0.1

    def test_development_config(self):
        """Test development configuration."""
        env_vars = {
            "ENVIRONMENT": "local",
            "LOG_LEVEL": "DEBUG",
            "LOG_FORMAT": "text",
            "LOG_REQUEST_BODY": "true",
            "LOG_RESPONSE_BODY": "true",
            "LOG_SAMPLING_RATE": "1.0",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            config = get_log_config()

            # Verify development settings
            assert config.environment == Environment.LOCAL
            assert config.level == LogLevel.DEBUG
            assert config.format == LogFormat.TEXT
            assert config.cloudwatch_enabled is False
            assert config.log_request_body is True
            assert config.log_response_body is True
            assert config.sampling_rate == 1.0
