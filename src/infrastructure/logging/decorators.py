"""Decorators for automatic logging of function execution and performance."""

import functools
import time
from collections.abc import Callable
from typing import Any, TypeVar, cast

from .logger import get_logger

F = TypeVar("F", bound=Callable[..., Any])


def log_execution(
    logger_name: str | None = None,
    log_args: bool = False,
    log_result: bool = False,
    log_performance: bool = True,
    log_level: str = "INFO",
) -> Callable[[F], F]:
    """
    Decorator to log function execution.

    Args:
        logger_name: Custom logger name (uses function module if None)
        log_args: Whether to log function arguments
        log_result: Whether to log function result
        log_performance: Whether to log execution time
        log_level: Log level for execution messages

    Returns:
        Decorated function
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get logger
            logger = get_logger(logger_name or func.__module__)
            log_level_num = getattr(logger, log_level.lower())

            # Prepare log context
            log_context: dict[str, Any] = {
                "function": func.__name__,
                "module": func.__module__,
            }

            # Log arguments if requested
            if log_args:
                log_context.update(
                    {
                        "args": args,
                        "kwargs": kwargs,
                    }
                )

            # Log function entry
            logger.log(log_level_num, f"Executing {func.__name__}", extra=log_context)

            # Execute function with timing
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                success = True
            except Exception as e:
                success = False
                result = None
                log_context["error"] = str(e)
                logger.error(f"Error in {func.__name__}: {e}", extra=log_context, exc_info=True)
                raise
            finally:
                # Log performance metrics
                if log_performance:
                    execution_time = time.perf_counter() - start_time
                    log_context["execution_time_ms"] = round(execution_time * 1000, 2)
                    log_context["success"] = success

                    # Log completion
                    if success:
                        if log_result and result is not None:
                            log_context["result"] = result
                        logger.log(log_level_num, f"Completed {func.__name__}", extra=log_context)

            return result

        return cast("F", wrapper)

    return decorator


def log_error(
    logger_name: str | None = None,
    reraise: bool = True,
    log_level: str = "ERROR",
) -> Callable[[F], F]:
    """
    Decorator to log function errors with detailed context.

    Args:
        logger_name: Custom logger name (uses function module if None)
        reraise: Whether to re-raise caught exceptions
        log_level: Log level for error messages

    Returns:
        Decorated function
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            logger = get_logger(logger_name or func.__module__)

            try:
                return func(*args, **kwargs)
            except Exception as e:
                log_context = {
                    "function": func.__name__,
                    "module": func.__module__,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "args_count": len(args),
                    "kwargs_keys": list(kwargs.keys()),
                }

                logger.log(
                    getattr(logger, log_level.lower()),
                    f"Error in {func.__name__}: {e}",
                    extra=log_context,
                    exc_info=True,
                )

                if reraise:
                    raise
                return None

        return cast("F", wrapper)

    return decorator


def log_performance(
    threshold_ms: int = 1000,
    logger_name: str | None = None,
    log_level: str = "WARNING",
) -> Callable[[F], F]:
    """
    Decorator to log slow function executions.

    Args:
        threshold_ms: Execution time threshold in milliseconds for logging
        logger_name: Custom logger name (uses function module if None)
        log_level: Log level for slow execution warnings

    Returns:
        Decorated function
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.perf_counter()
            result = func(*args, **kwargs)
            execution_time = time.perf_counter() - start_time
            execution_time_ms = execution_time * 1000

            if execution_time_ms > threshold_ms:
                logger = get_logger(logger_name or func.__module__)
                log_context = {
                    "function": func.__name__,
                    "module": func.__module__,
                    "execution_time_ms": round(execution_time_ms, 2),
                    "threshold_ms": threshold_ms,
                }

                logger.log(
                    getattr(logger, log_level.lower()),
                    f"Slow execution detected: {func.__name__} took {execution_time_ms:.2f}ms",
                    extra=log_context,
                )

            return result

        return cast("F", wrapper)

    return decorator


def log_async_execution(
    logger_name: str | None = None,
    log_args: bool = False,
    log_result: bool = False,
    log_performance: bool = True,
    log_level: str = "INFO",
) -> Callable[[F], F]:
    """
    Decorator to log async function execution.

    Similar to log_execution but for async functions.

    Args:
        logger_name: Custom logger name (uses function module if None)
        log_args: Whether to log function arguments
        log_result: Whether to log function result
        log_performance: Whether to log execution time
        log_level: Log level for execution messages

    Returns:
        Decorated async function
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get logger
            logger = get_logger(logger_name or func.__module__)
            log_level_num = getattr(logger, log_level.lower())

            # Prepare log context
            log_context: dict[str, Any] = {
                "function": func.__name__,
                "module": func.__module__,
                "async": True,
            }

            # Log arguments if requested
            if log_args:
                log_context.update(
                    {
                        "args": args,
                        "kwargs": kwargs,
                    }
                )

            # Log function entry
            logger.log(log_level_num, f"Executing async {func.__name__}", extra=log_context)

            # Execute function with timing
            start_time = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                success = True
            except Exception as e:
                success = False
                result = None
                log_context["error"] = str(e)
                logger.error(f"Error in async {func.__name__}: {e}", extra=log_context, exc_info=True)
                raise
            finally:
                # Log performance metrics
                if log_performance:
                    execution_time = time.perf_counter() - start_time
                    log_context["execution_time_ms"] = round(execution_time * 1000, 2)
                    log_context["success"] = success

                    # Log completion
                    if success:
                        if log_result and result is not None:
                            log_context["result"] = result
                        logger.log(log_level_num, f"Completed async {func.__name__}", extra=log_context)

            return result

        return cast("F", wrapper)

    return decorator


# Convenience decorators with common configurations
debug_execution = functools.partial(log_execution, log_level="DEBUG", log_args=True)
trace_performance = functools.partial(log_performance, threshold_ms=500, log_level="INFO")
monitor_errors = functools.partial(log_error, log_level="ERROR")
