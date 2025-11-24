"""
Spotlight-related Pydantic schemas.

This module contains all spotlight-related request and response schemas.
"""

from typing import Optional, List
from datetime import datetime, timezone
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator


class SpotlightApplyRequest(BaseModel):
    """Schema for applying spotlight to a product."""
    
    duration_hours: Optional[int] = Field(None, description="Duration in hours (24, 72, or 168)")
    custom_end_time: Optional[datetime] = Field(None, description="Custom end time (overrides duration_hours)")
    
    @field_validator('duration_hours')
    @classmethod
    def validate_duration(cls, v):
        """Validate duration is one of the allowed values."""
        if v is not None and v not in [24, 72, 168]:
            raise ValueError('Duration must be 24, 72, or 168 hours')
        return v
    
    @field_validator('custom_end_time')
    @classmethod
    def validate_custom_end_time(cls, v):
        """Validate custom end time is in the future."""
        if v is not None:
            # Handle both timezone-aware and timezone-naive datetimes
            now = datetime.now(timezone.utc)
            # If v is timezone-naive, make it timezone-aware (assume UTC)
            if v.tzinfo is None:
                v = v.replace(tzinfo=timezone.utc)
            if v <= now:
                raise ValueError('Custom end time must be in the future')
        return v


class SpotlightResponse(BaseModel):
    """Schema for spotlight response."""
    
    id: str = Field(..., description="Spotlight ID")
    product_id: str = Field(..., description="Product ID")
    product_title: str = Field(..., description="Product title")
    product_image: Optional[str] = Field(None, description="First product image")
    applied_by: str = Field(..., description="Admin user ID who applied")
    applied_by_username: str = Field(..., description="Admin username")
    start_time: datetime = Field(..., description="Start time")
    end_time: datetime = Field(..., description="End time")
    duration_hours: int = Field(..., description="Duration in hours")
    status: str = Field(..., description="Status (active, expired, removed)")
    created_at: datetime = Field(..., description="Creation timestamp")


class ActiveSpotlightResponse(BaseModel):
    """Schema for active spotlight with product details."""
    
    id: str = Field(..., description="Spotlight ID")
    product_id: str = Field(..., description="Product ID")
    product_title: str = Field(..., description="Product title")
    product_price: Decimal = Field(..., description="Product price")
    product_image: Optional[str] = Field(None, description="First product image")
    seller_username: str = Field(..., description="Seller username")
    applied_by_username: str = Field(..., description="Admin username who applied")
    start_time: datetime = Field(..., description="Start time")
    end_time: datetime = Field(..., description="End time")
    duration_hours: int = Field(..., description="Duration in hours")
    created_at: datetime = Field(..., description="Creation timestamp")


class ActiveSpotlightListResponse(BaseModel):
    """Schema for paginated active spotlights list."""
    
    spotlights: List[ActiveSpotlightResponse] = Field(..., description="List of active spotlights")
    total: int = Field(..., description="Total number of active spotlights")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")


class SpotlightHistoryResponse(BaseModel):
    """Schema for spotlight history entry."""
    
    id: str = Field(..., description="History entry ID")
    spotlight_id: Optional[str] = Field(None, description="Spotlight ID")
    product_id: str = Field(..., description="Product ID")
    product_title: str = Field(..., description="Product title")
    product_image: Optional[str] = Field(None, description="First product image")
    seller_username: str = Field(..., description="Seller username")
    action: str = Field(..., description="Action (applied, expired, removed)")
    applied_by_username: str = Field(..., description="Admin who applied")
    removed_by_username: Optional[str] = Field(None, description="Admin who removed (if applicable)")
    start_time: datetime = Field(..., description="Start time")
    end_time: datetime = Field(..., description="End time")
    duration_hours: int = Field(..., description="Duration in hours")
    created_at: datetime = Field(..., description="Creation timestamp")


class SpotlightHistoryListResponse(BaseModel):
    """Schema for paginated spotlight history list."""
    
    history: List[SpotlightHistoryResponse] = Field(..., description="List of history entries")
    total: int = Field(..., description="Total number of entries")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")


class ProductSpotlightStatusResponse(BaseModel):
    """Schema for product spotlight status response."""
    
    product_id: str = Field(..., description="Product ID")
    is_spotlighted: bool = Field(..., description="Whether product is currently spotlighted")
    spotlight: Optional[SpotlightResponse] = Field(None, description="Current spotlight details if active")
    spotlight_end_time: Optional[datetime] = Field(None, description="When spotlight expires (if active)")

