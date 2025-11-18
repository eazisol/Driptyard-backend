"""
Base Pydantic schemas.

This module contains base schemas that other schemas inherit from.
"""

from pydantic import BaseModel, Field
from datetime import datetime


class BaseResponseSchema(BaseModel):
    """Base response schema with common fields."""
    
    id: str = Field(..., description="Unique identifier (as string)")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class BaseCreateSchema(BaseModel):
    """Base schema for creation requests."""
    pass


class BaseUpdateSchema(BaseModel):
    """Base schema for update requests."""
    pass
