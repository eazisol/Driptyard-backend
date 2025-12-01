"""
Follow-related Pydantic schemas.

This module contains all follow-related request and response schemas.
"""

from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field

from app.schemas.product import SellerInfo, ProductListResponse


class FollowSellerResponse(BaseModel):
    """Schema for follow seller response."""
    
    id: str = Field(..., description="Follow relationship ID")
    follower_id: str = Field(..., description="Follower user ID")
    followed_user_id: str = Field(..., description="Followed seller user ID")
    seller: SellerInfo = Field(..., description="Seller information")
    created_at: datetime = Field(..., description="Follow creation timestamp")
    
    class Config:
        from_attributes = True


class FollowProductResponse(BaseModel):
    """Schema for follow product response."""
    
    id: str = Field(..., description="Follow relationship ID")
    user_id: str = Field(..., description="User ID who followed")
    product_id: str = Field(..., description="Product ID that was followed")
    product: ProductListResponse = Field(..., description="Product information")
    created_at: datetime = Field(..., description="Follow creation timestamp")
    
    class Config:
        from_attributes = True


class FollowedSellerResponse(BaseModel):
    """Schema for followed seller information."""
    
    id: str = Field(..., description="Follow relationship ID")
    seller: SellerInfo = Field(..., description="Seller information")
    followed_at: datetime = Field(..., description="When the seller was followed")
    
    class Config:
        from_attributes = True


class FollowedProductResponse(BaseModel):
    """Schema for followed product information."""
    
    id: str = Field(..., description="Follow relationship ID")
    product: ProductListResponse = Field(..., description="Product information")
    followed_at: datetime = Field(..., description="When the product was followed")
    
    class Config:
        from_attributes = True


class FollowedSellersListResponse(BaseModel):
    """Schema for paginated list of followed sellers."""
    
    sellers: List[FollowedSellerResponse] = Field(..., description="List of followed sellers")
    total: int = Field(..., description="Total number of followed sellers")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")
    
    class Config:
        from_attributes = True


class FollowedProductsListResponse(BaseModel):
    """Schema for paginated list of followed products."""
    
    products: List[FollowedProductResponse] = Field(..., description="List of followed products")
    total: int = Field(..., description="Total number of followed products")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")
    
    class Config:
        from_attributes = True


class FollowStatusResponse(BaseModel):
    """Schema for follow status check response."""
    
    is_following: bool = Field(..., description="Whether the user is following")
    follow_id: Optional[str] = Field(None, description="Follow relationship ID if following")
    
    class Config:
        from_attributes = True

