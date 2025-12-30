"""
Spotlight-related Pydantic schemas.

This module contains all spotlight-related request and response schemas.
"""

from typing import Optional, List
from datetime import datetime, timezone
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator, model_validator


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


class SpotlightWithHistoryResponse(BaseModel):
    """Schema for spotlight with nested history entries."""
    
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
    products: List[SpotlightHistoryResponse] = Field(default_factory=list, description="List of related history entries")


class SpotlightHistoryListResponse(BaseModel):
    """Schema for paginated spotlight history list."""
    
    spotlights: List[SpotlightWithHistoryResponse] = Field(..., description="List of spotlights with nested history entries")
    total: int = Field(..., description="Total number of spotlights")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")


class ProductSpotlightStatusResponse(BaseModel):
    """Schema for product spotlight status response."""
    
    product_id: str = Field(..., description="Product ID")
    is_spotlighted: bool = Field(..., description="Whether product is currently spotlighted")
    spotlight: Optional[SpotlightResponse] = Field(None, description="Current spotlight details if active")
    spotlight_end_time: Optional[datetime] = Field(None, description="When spotlight expires (if active)")


class BulkSpotlightRequest(BaseModel):
    """Schema for bulk spotlight request with add/edit/remove actions."""
    
    product_ids: List[int] = Field(..., description="Array of product IDs", min_length=1, max_length=100)
    action: str = Field(..., description="Action to perform: 'add', 'edit', or 'remove'")
    duration_hours: Optional[int] = Field(None, description="Duration in hours (24, 72, or 168) - required for add/edit")
    custom_end_time: Optional[datetime] = Field(None, description="Custom end time (overrides duration_hours) - required for add/edit")
    
    @field_validator('action')
    @classmethod
    def validate_action(cls, v):
        """Validate action is one of the allowed values."""
        if v not in ['add', 'edit', 'remove']:
            raise ValueError('Action must be one of: add, edit, remove')
        return v
    
    @field_validator('product_ids')
    @classmethod
    def validate_product_ids(cls, v):
        """Validate that all IDs are positive integers."""
        if not v:
            raise ValueError('product_ids cannot be empty')
        if len(v) > 100:
            raise ValueError('Maximum 100 products per request')
        for product_id in v:
            if product_id <= 0:
                raise ValueError('All product IDs must be positive integers')
        return v
    
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
    
    @model_validator(mode='after')
    def validate_action_requirements(self):
        """Validate that required fields are provided based on action."""
        # For add and edit actions, either duration_hours or custom_end_time must be provided
        if self.action in ['add', 'edit']:
            if self.duration_hours is None and self.custom_end_time is None:
                raise ValueError('Either duration_hours or custom_end_time must be provided for add/edit actions')
            if self.duration_hours is not None and self.custom_end_time is not None:
                raise ValueError('Cannot provide both duration_hours and custom_end_time')
        # For remove action, no duration fields are needed
        return self


class SpotlightedProductResponse(BaseModel):
    """Schema for a successfully spotlighted product in bulk operation."""
    
    product_id: int = Field(..., description="Product ID")
    spotlight_id: int = Field(..., description="Spotlight ID")
    start_time: datetime = Field(..., description="Start time")
    end_time: datetime = Field(..., description="End time")
    status: str = Field(..., description="Status (active)")


class FailedProductResponse(BaseModel):
    """Schema for a failed product in bulk operation."""
    
    product_id: int = Field(..., description="Product ID")
    error: str = Field(..., description="Error message")


class BulkSpotlightResponse(BaseModel):
    """Schema for bulk spotlight response."""
    
    message: str = Field(..., description="Response message")
    success: bool = Field(..., description="Whether operation was successful")
    updated_count: int = Field(..., description="Number of products successfully processed")
    failed_count: int = Field(..., description="Number of products that failed")
    failed_product_ids: List[int] = Field(default_factory=list, description="List of product IDs that failed")
    data: Optional[dict] = Field(None, description="Response data containing spotlighted and failed products (for backward compatibility)")
