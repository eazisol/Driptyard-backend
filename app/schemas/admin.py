"""
Admin-related Pydantic schemas.

This module contains admin-related request and response schemas.
"""

from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, EmailStr, field_validator


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
    owner_name: Optional[str] = Field(None, description="Owner/seller username")
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
    """Schema for admin product update."""
    
    title: Optional[str] = Field(None, min_length=1, max_length=255, description="Product title")
    price: Optional[Decimal] = Field(None, ge=0, description="Product price")
    condition: Optional[str] = Field(None, max_length=50, description="Product condition")
    is_active: Optional[bool] = Field(None, description="Whether product is active")
    is_verified: Optional[bool] = Field(None, description="Whether product is verified")
    is_flagged: Optional[bool] = Field(None, description="Whether product is flagged")
    stock_status: Optional[str] = Field(None, description="Stock status: In Stock, Out of Stock, Limited")


class AdminUserResponse(BaseModel):
    """Schema for admin user list item."""
    
    id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    username: str = Field(..., description="Username")
    first_name: Optional[str] = Field(None, description="First name")
    last_name: Optional[str] = Field(None, description="Last name")
    phone: Optional[str] = Field(None, description="Phone number")
    country_code: Optional[str] = Field(None, description="Country code")
    is_active: bool = Field(..., description="Whether user is active")
    is_verified: bool = Field(..., description="Whether user is verified")
    is_admin: bool = Field(..., description="Whether user is admin")
    avatar_url: Optional[str] = Field(None, description="Avatar URL")
    created_at: datetime = Field(..., description="Creation timestamp")


class AdminUserListResponse(BaseModel):
    """Schema for admin user list with pagination."""
    
    users: List[AdminUserResponse] = Field(..., description="List of users")
    total: int = Field(..., description="Total number of users")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")
    
    class Config:
        from_attributes = True


class AdminUserUpdateRequest(BaseModel):
    """Schema for admin user full profile update."""
    
    email: Optional[EmailStr] = Field(None, description="User email address")
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="Username")
    first_name: Optional[str] = Field(None, max_length=100, description="First name")
    last_name: Optional[str] = Field(None, max_length=100, description="Last name")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    country_code: Optional[str] = Field(None, min_length=2, max_length=3, description="Country code")
    bio: Optional[str] = Field(None, max_length=500, description="User bio")
    avatar_url: Optional[str] = Field(None, max_length=500, description="Avatar URL")
    company_name: Optional[str] = Field(None, max_length=200, description="Company name")
    sin_number: Optional[str] = Field(None, max_length=20, description="Social Insurance Number")
    is_active: Optional[bool] = Field(None, description="Whether user is active")
    is_verified: Optional[bool] = Field(None, description="Whether user is verified")
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        """Validate username format."""
        if v is None:
            return v
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username can only contain letters, numbers, underscores, and hyphens')
        return v.lower()

