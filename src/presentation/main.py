"""FastAPI main application module."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.presentation.api.health import router as health_router
from src.presentation.api.v1.customers import router as customers_router
from src.presentation.api.v1.orders import router as orders_router
from src.presentation.startup import initialize_sample_data


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    # Startup
    await initialize_sample_data()
    yield
    # Shutdown (nothing to do)


app = FastAPI(
    title="Clean Architecture Python",
    description="Clean Architecture Python demonstration API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
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
