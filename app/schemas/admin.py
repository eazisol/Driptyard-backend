"""
Admin-related Pydantic schemas.

This module contains admin-related request and response schemas.
"""

from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field


class StatsOverviewResponse(BaseModel):
    """Schema for admin stats overview response."""
    
    total_users: int = Field(..., description="Total number of users")
    users_change: float = Field(..., description="Percentage change in users compared to previous period")
    total_products: int = Field(..., description="Total number of products (listings)")
    products_change: float = Field(..., description="Percentage change in products compared to previous period")
    pending_verifications: int = Field(..., description="Number of users pending verification")
    flagged_content_count: int = Field(..., description="Number of flagged content items (unverified products)")


class AdminProductResponse(BaseModel):
    """Schema for admin product list item."""
    
    id: str = Field(..., description="Product ID")
    title: str = Field(..., description="Product title")
    price: Decimal = Field(..., description="Product price")
    category: Optional[str] = Field(None, description="Product category")
    condition: Optional[str] = Field(None, description="Product condition")
    stock_quantity: int = Field(..., description="Stock quantity")
    stock_status: str = Field(..., description="Stock status")
    is_active: bool = Field(..., description="Whether product is active")
    is_sold: bool = Field(..., description="Whether product is sold")
    is_verified: bool = Field(..., description="Whether product is verified")
    is_flagged: bool = Field(..., description="Whether product is flagged")
    images: List[str] = Field(default_factory=list, description="Product images")
    owner_id: str = Field(..., description="Owner/seller ID")
    created_at: datetime = Field(..., description="Creation timestamp")


class AdminProductListResponse(BaseModel):
    """Schema for admin product list with pagination."""
    
    products: List[AdminProductResponse] = Field(..., description="List of products")
    total: int = Field(..., description="Total number of products")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")
    
    class Config:
        from_attributes = True


class AdminProductUpdateRequest(BaseModel):
    """Schema for admin product status update."""
    
    is_active: Optional[bool] = Field(None, description="Whether product is active")
    is_verified: Optional[bool] = Field(None, description="Whether product is verified")
    is_flagged: Optional[bool] = Field(None, description="Whether product is flagged")
    stock_status: Optional[str] = Field(None, description="Stock status: In Stock, Out of Stock, Limited")

