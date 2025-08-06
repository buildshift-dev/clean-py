"""Health check endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "healthy"
    service: str = "clean-architecture-api"
    version: str = "1.0.0"


router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint for load balancer."""
    return HealthResponse()


@router.get("/", response_model=dict[str, str])
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {"message": "Clean Architecture Python API", "docs": "/docs", "health": "/health"}
