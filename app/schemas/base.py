"""
Base Pydantic schemas.

This module provides base schema classes that other schemas can inherit from,
including common fields and validation logic.
"""

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID


class BaseSchema(BaseModel):
    """
    Base schema class with common configuration.
    
    All schemas should inherit from this class to get common
    configuration and behavior.
    """
    
    model_config = ConfigDict(
        from_attributes=True,
        validate_assignment=True,
        arbitrary_types_allowed=True,
        json_encoders={
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }
    )


class BaseResponseSchema(BaseSchema):
    """
    Base response schema with common fields.
    
    All response schemas should inherit from this class to get
    common fields like id, created_at, and updated_at.
    """
    
    id: UUID = Field(..., description="Unique identifier")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class BaseCreateSchema(BaseSchema):
    """
    Base schema for creation requests.
    
    All creation schemas should inherit from this class.
    """
    pass


class BaseUpdateSchema(BaseSchema):
    """
    Base schema for update requests.
    
    All update schemas should inherit from this class.
    """
    pass


class PaginationSchema(BaseSchema):
    """
    Pagination schema for list responses.
    """
    
    skip: int = Field(0, ge=0, description="Number of items to skip")
    limit: int = Field(10, ge=1, le=100, description="Number of items to return")
    total: int = Field(..., ge=0, description="Total number of items")
    has_next: bool = Field(..., description="Whether there are more items")
    has_prev: bool = Field(..., description="Whether there are previous items")


class ErrorResponseSchema(BaseSchema):
    """
    Error response schema.
    """
    
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[dict[str, Any]] = Field(None, description="Additional error details")
