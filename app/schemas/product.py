"""
Product-related Pydantic schemas.

This module contains all product-related request and response schemas.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import datetime

from app.schemas.base import BaseCreateSchema, BaseUpdateSchema, BaseResponseSchema


class SellerInfo(BaseModel):
    """Schema for seller information."""
    
    id: str = Field(..., description="Seller ID")
    username: str = Field(..., description="Seller username")
    rating: float = Field(default=0.0, description="Seller rating")
    total_sales: int = Field(default=0, description="Total number of sales")
    avatar_url: Optional[str] = Field(None, description="Seller avatar URL")


class ProductCreate(BaseCreateSchema):
    """Schema for creating a product."""
    
    title: str = Field(..., min_length=1, max_length=255, description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: str = Field(..., description="Product price as string")
    category: Optional[str] = Field(None, max_length=100, description="Product category")
    condition: Optional[str] = Field(None, description="Product condition")
    
    # Deal method and meetup details
    dealMethod: str = Field(..., description="Deal method: 'delivery' or 'meetup'")
    meetupDate: Optional[str] = Field(None, description="Meetup date (YYYY-MM-DD)")
    meetupLocation: Optional[str] = Field(None, max_length=255, description="Meetup location")
    meetupTime: Optional[str] = Field(None, description="Meetup time (HH:MM)")
    
    # Images
    images: Optional[List[Dict[str, Any]]] = Field(default=[], description="Product images with file and preview data")
    
    # Additional fields for internal use
    currentStep: Optional[int] = Field(None, description="Current step in creation process")


class ProductUpdate(BaseUpdateSchema):
    """Schema for updating a product."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Product name")
    description: Optional[str] = Field(None, description="Product description")
    price: Optional[Decimal] = Field(None, gt=0, description="Product price")
    category: Optional[str] = Field(None, max_length=100, description="Product category")
    condition: Optional[str] = Field(None, description="Product condition")
    condition_badge: Optional[str] = Field(None, description="Condition badge")
    
    stock_quantity: Optional[int] = Field(None, ge=0, description="Stock quantity")
    stock_status: Optional[str] = Field(None, description="Stock status")
    
    location: Optional[str] = Field(None, max_length=255, description="Product location")
    shipping_cost: Optional[Decimal] = Field(None, ge=0, description="Shipping cost")
    delivery_days: Optional[str] = Field(None, description="Estimated delivery time")
    
    brand: Optional[str] = Field(None, max_length=100, description="Product brand")
    model: Optional[str] = Field(None, max_length=100, description="Product model")
    year: Optional[int] = Field(None, ge=1900, le=2030, description="Product year")
    
    images: Optional[List[str]] = Field(None, description="Product image URLs")
    specifications: Optional[Dict[str, Any]] = Field(None, description="Product specifications")
    key_features: Optional[List[str]] = Field(None, description="Key features")
    tags: Optional[List[str]] = Field(None, description="Product tags")
    
    return_policy: Optional[str] = Field(None, description="Return policy")
    warranty_info: Optional[str] = Field(None, description="Warranty information")
    packaging_info: Optional[str] = Field(None, description="Packaging info")
    
    is_active: Optional[bool] = Field(None, description="Whether product is active")
    is_featured: Optional[bool] = Field(None, description="Whether product is featured")


class ProductListResponse(BaseModel):
    """Schema for product list item (card view)."""
    
    id: str = Field(..., description="Product ID")
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description (short)")
    price: Decimal = Field(..., description="Product price")
    condition: Optional[str] = Field(None, description="Product condition")
    images: List[str] = Field(default=[], description="Product images")
    rating: float = Field(default=0.0, description="Product rating")
    review_count: int = Field(default=0, description="Number of reviews")
    stock_status: str = Field(..., description="Stock status")
    deal_method: str = Field(..., description="Deal method")
    seller: SellerInfo = Field(..., description="Seller information")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    class Config:
        from_attributes = True


class ProductDetailResponse(BaseResponseSchema):
    """Schema for product detail response (full view)."""
    
    # Basic info
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: Decimal = Field(..., description="Product price")
    category: Optional[str] = Field(None, description="Product category")
    condition: Optional[str] = Field(None, description="Product condition")
    
    # Deal method and meetup details
    deal_method: str = Field(..., description="Deal method")
    meetup_date: Optional[str] = Field(None, description="Meetup date")
    meetup_location: Optional[str] = Field(None, description="Meetup location")
    meetup_time: Optional[str] = Field(None, description="Meetup time")
    
    # Stock
    stock_quantity: int = Field(..., description="Stock quantity")
    stock_status: str = Field(..., description="Stock status")
    
    # Ratings
    rating: float = Field(default=0.0, description="Product rating")
    review_count: int = Field(default=0, description="Number of reviews")
    
    # Images
    images: List[str] = Field(default=[], description="Product image URLs")
    
    # Status
    is_active: bool = Field(..., description="Whether product is active")
    is_sold: bool = Field(..., description="Whether product is sold")
    is_featured: bool = Field(..., description="Whether product is featured")
    
    # Seller info
    seller: SellerInfo = Field(..., description="Seller information")
    
    class Config:
        from_attributes = True


class ProductPaginationResponse(BaseModel):
    """Schema for paginated product list response."""
    
    items: List[ProductListResponse] = Field(..., description="List of products")
    total: int = Field(..., description="Total number of products")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")
