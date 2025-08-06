from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class CreateOrderRequest(BaseModel):
    """Request schema for creating an order."""

    customer_id: UUID = Field(..., description="ID of the customer placing the order")
    total_amount: Decimal = Field(..., gt=0, description="Total order amount")
    currency: str = Field(default="USD", description="Currency code")
    details: dict[str, Any] = Field(default_factory=dict, description="Additional order details")


class OrderResponse(BaseModel):
    """Response schema for order data."""

    id: UUID = Field(..., description="Unique order identifier")
    customer_id: UUID = Field(..., description="ID of the customer who placed the order")
    total_amount: Decimal = Field(..., description="Total order amount")
    currency: str = Field(..., description="Currency code")
    status: str = Field(..., description="Order status")
    details: dict[str, Any] = Field(..., description="Additional order details")
    created_at: datetime = Field(..., description="Order creation timestamp")
    updated_at: datetime = Field(..., description="Order last update timestamp")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "customer_id": "123e4567-e89b-12d3-a456-426614174001",
                "total_amount": "99.99",
                "currency": "USD",
                "status": "pending",
                "details": {"product": "Widget", "category": "electronics"},
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-01T12:00:00Z",
            }
        }
