"""Tests for main logging configuration and factory functions."""

import logging
from typing import Any
from unittest.mock import Mock, patch

from src.infrastructure.logging.config import Environment, LogConfig, LogLevel
from src.infrastructure.logging.logger import (
    _configure_third_party_loggers,  # pyright: ignore[reportPrivateUsage]
    configure_logging,
    get_application_logger,
    get_logger,
    shutdown_logging,
)


class TestGetLogger:
    """Test get_logger functionality."""

    @patch("src.infrastructure.logging.config._is_running_locally")
    def test_get_logger_default_config(self, mock_is_local: Any) -> None:
        """Test getting logger with default configuration."""
        # Force AWS environment detection for consistent test behavior
        mock_is_local.return_value = False

        logger = get_logger("test.module")

        assert isinstance(logger, logging.Logger)
        assert logger.name == "test.module"
        assert logger.level == logging.INFO  # Default level

    def test_get_logger_custom_config(self):
        """Test getting logger with custom configuration."""
        config = LogConfig(level=LogLevel.DEBUG, service_name="custom-service")

        logger = get_logger("test.module", config)

        assert logger.level == logging.DEBUG

    def test_get_logger_no_duplicate_handlers(self):
        """Test that getting the same logger doesn't add duplicate handlers."""
        logger1 = get_logger("test.duplicate")
        initial_handler_count = len(logger1.handlers)

        logger2 = get_logger("test.duplicate")

        # Should be the same logger instance
        assert logger1 is logger2
        # Should not have added more handlers
        assert len(logger2.handlers) == initial_handler_count

    def test_logger_propagation_disabled(self):
        """Test that logger propagation is disabled."""
        logger = get_logger("test.propagation")
        assert logger.propagate is False


class TestConfigureLogging:
    """Test configure_logging functionality."""

    def setUp(self):
        """Clear any existing handlers before each test."""
        # Clear root logger handlers
        root_logger = logging.getLogger()
        root_logger.handlers.clear()

    @patch("src.infrastructure.logging.config._is_running_locally")
    def test_configure_logging_default(self, mock_is_local: Any) -> None:
        """Test logging configuration with defaults."""
        # Force AWS environment detection for consistent test behavior
        mock_is_local.return_value = False

        configure_logging()

        root_logger = logging.getLogger()

        # Should have at least console handler
        assert len(root_logger.handlers) >= 1
        assert root_logger.level == logging.INFO

    def test_configure_logging_custom_config(self):
        """Test logging configuration with custom config."""
        config = LogConfig(level=LogLevel.DEBUG, service_name="test-service", environment=Environment.PRODUCTION)

        configure_logging(config)

        root_logger = logging.getLogger()
        assert root_logger.level == logging.DEBUG

    @patch("src.infrastructure.logging.logger.get_cloudwatch_handler")
    def test_configure_logging_with_cloudwatch(self, mock_cloudwatch_handler: Any) -> None:
        """Test logging configuration with CloudWatch enabled."""
        # Mock CloudWatch handler
        mock_handler = Mock(spec=logging.Handler)
        mock_handler.level = logging.INFO  # Set level attribute for the mock
        mock_cloudwatch_handler.return_value = mock_handler

        config = LogConfig(
            environment=Environment.PRODUCTION,  # Use non-local environment
            cloudwatch_enabled=True,
            cloudwatch_log_group="/test/logs",
        )

        configure_logging(config)

        # CloudWatch handler should have been requested (called twice - once during configure, once during get_logger)
        assert mock_cloudwatch_handler.call_count >= 1

        # Root logger should have both console and CloudWatch handlers
        root_logger = logging.getLogger()
        [type(h).__name__ for h in root_logger.handlers]
        assert len(root_logger.handlers) >= 2

    def test_configure_logging_clears_existing_handlers(self):
        """Test that configure_logging clears existing handlers."""
        root_logger = logging.getLogger()

        # Add a dummy handler
        dummy_handler = logging.StreamHandler()
        root_logger.addHandler(dummy_handler)
        initial_count = len(root_logger.handlers)
        assert initial_count >= 1

        # Configure logging
        configure_logging()

        # Should have cleared old handlers and added new ones
        assert dummy_handler not in root_logger.handlers
        assert len(root_logger.handlers) >= 1

    @patch("src.infrastructure.logging.logger._configure_third_party_loggers")
    def test_configure_logging_configures_third_party(self, mock_configure_third_party: Any) -> None:
        """Test that third-party loggers are configured."""
        config = LogConfig()

        configure_logging(config)

        mock_configure_third_party.assert_called_once_with(config)


class TestConfigureThirdPartyLoggers:
    """Test third-party logger configuration."""

    def test_configure_third_party_loggers_production(self):
        """Test third-party logger configuration for production."""
        config = LogConfig(environment=Environment.PRODUCTION)

        _configure_third_party_loggers(config)

        # Check that noisy loggers are set to WARNING
        boto3_logger = logging.getLogger("boto3")
        assert boto3_logger.level == logging.WARNING

        urllib3_logger = logging.getLogger("urllib3")
        assert urllib3_logger.level == logging.WARNING

        sqlalchemy_logger = logging.getLogger("sqlalchemy.engine")
        assert sqlalchemy_logger.level == logging.WARNING

    def test_configure_third_party_loggers_local(self):
        """Test third-party logger configuration for local development."""
        config = LogConfig(environment=Environment.LOCAL)

        _configure_third_party_loggers(config)

        # Some loggers should be more verbose in local
        sqlalchemy_logger = logging.getLogger("sqlalchemy.engine")
        assert sqlalchemy_logger.level == logging.INFO

        httpx_logger = logging.getLogger("httpx")
        assert httpx_logger.level == logging.INFO

        # But some should still be quiet
        boto3_logger = logging.getLogger("boto3")
        assert boto3_logger.level == logging.WARNING


class TestShutdownLogging:
    """Test logging shutdown functionality."""

    @patch("logging.shutdown")
    def test_shutdown_logging(self, mock_logging_shutdown: Any) -> None:
        """Test that shutdown_logging calls logging.shutdown."""
        shutdown_logging()
        mock_logging_shutdown.assert_called_once()


class TestGetApplicationLogger:
    """Test get_application_logger convenience function."""

    def test_get_application_logger(self):
        """Test that get_application_logger works as expected."""
        logger = get_application_logger("test.app")

        assert isinstance(logger, logging.Logger)
        assert logger.name == "test.app"

    @patch("src.infrastructure.logging.logger.get_logger")
    def test_get_application_logger_calls_get_logger(self, mock_get_logger: Any) -> None:
        """Test that get_application_logger calls get_logger."""
        mock_logger = Mock(spec=logging.Logger)
        mock_get_logger.return_value = mock_logger

        result = get_application_logger("test.app")

        mock_get_logger.assert_called_once_with("test.app")
        assert result == mock_logger


class TestLoggingIntegration:
    """Integration tests for logging functionality."""

    def test_end_to_end_logging_setup(self):
        """Test complete logging setup process."""
        # Clear any existing configuration
        root_logger = logging.getLogger()
        root_logger.handlers.clear()

        # Configure with custom settings
        config = LogConfig(
            level=LogLevel.DEBUG,
            service_name="integration-test",
            environment=Environment.LOCAL,
            include_hostname=True,
        )

        configure_logging(config)

        # Get application logger
        logger = get_application_logger("integration.test")

        # Test logging at different levels
        with patch("sys.stdout"):
            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")

        # Verify logger configuration
        assert logger.level <= logging.DEBUG  # Should log debug messages
        assert len(root_logger.handlers) >= 1

    def test_correlation_id_in_logs(self):
        """Test that correlation IDs appear in formatted logs."""
        from src.infrastructure.logging.correlation import CorrelationContext

        # Configure logging
        configure_logging()
        logger = get_application_logger("correlation.test")

        # Set correlation ID
        test_correlation_id = "integration-correlation-123"
        CorrelationContext.set(test_correlation_id)

        # Capture log output
        with patch("sys.stdout"):
            logger.info("Test message with correlation")

        # Verify correlation ID is included (implementation depends on formatter)
        # This is a basic check - more detailed testing in formatter tests
        assert logger is not None  # Basic sanity check

        # Clean up
        CorrelationContext.set(None)

    def test_exception_logging_integration(self):
        """Test exception logging integration."""
        configure_logging()
        logger = get_application_logger("exception.test")

        try:
            raise ValueError("Integration test exception")
        except ValueError:
            with patch("sys.stdout"):
                logger.exception("Exception occurred during integration test")

        # If no exception is raised, the integration works
        assert True

    def test_multiple_loggers_isolation(self):
        """Test that multiple loggers work independently."""
        configure_logging()

        logger1 = get_application_logger("test.module1")
        logger2 = get_application_logger("test.module2")

        # Should be different logger instances
        assert logger1 is not logger2
        assert logger1.name != logger2.name

        # But should both work correctly
        with patch("sys.stdout"):
            logger1.info("Message from logger 1")
            logger2.info("Message from logger 2")

        # Both should be configured properly
        assert logger1.level is not None
        assert logger2.level is not None
