from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class CreateCustomerRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$")
    preferences: dict[str, Any] | None = Field(default_factory=dict)


class CustomerResponse(BaseModel):
    id: UUID
    name: str
    email: str
    is_active: bool
    preferences: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
