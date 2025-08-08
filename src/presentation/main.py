"""FastAPI main application module."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.infrastructure.logging import (
    LoggingMiddleware,
    configure_logging,
    correlation_middleware,
    get_logger,
)
from src.presentation.api.health import router as health_router
from src.presentation.api.v1.customers import router as customers_router
from src.presentation.api.v1.orders import router as orders_router
from src.presentation.startup import initialize_sample_data

# Configure logging at startup - automatically detects environment
configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    # Startup
    logger.info("Application starting up")
    await initialize_sample_data()
    logger.info("Application startup completed")
    yield
    # Shutdown
    logger.info("Application shutting down")
    from src.infrastructure.logging.logger import shutdown_logging

    shutdown_logging()


app = FastAPI(
    title="Clean Architecture Python",
    description="Clean Architecture Python demonstration API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add logging middleware (order matters!)
app.add_middleware(correlation_middleware)
app.add_middleware(
    LoggingMiddleware,
    skip_paths={"/health", "/docs", "/redoc", "/openapi.json"},
    log_request_body=False,  # Will be overridden by environment detection
    log_response_body=False,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router)
app.include_router(customers_router)
app.include_router(orders_router)
