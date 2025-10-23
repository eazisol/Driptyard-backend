"""
Product Pydantic schemas.

This module contains all Pydantic schemas related to product operations
including request/response validation for product endpoints.
"""

from typing import Optional, List
from pydantic import Field, field_validator
from decimal import Decimal
from uuid import UUID

from app.schemas.base import BaseResponseSchema, BaseCreateSchema, BaseUpdateSchema


class ProductBaseSchema(BaseCreateSchema):
    """Base product schema with common fields."""
    
    name: str = Field(..., min_length=1, max_length=200, description="Product name")
    description: str = Field(..., min_length=1, max_length=2000, description="Product description")
    price: Decimal = Field(..., gt=0, description="Product price")
    category: str = Field(..., min_length=1, max_length=100, description="Product category")
    condition: str = Field(..., description="Product condition")
    location: str = Field(..., min_length=1, max_length=200, description="Product location")
    
    @field_validator('condition')
    @classmethod
    def validate_condition(cls, v):
        """Validate product condition."""
        valid_conditions = ['new', 'like_new', 'good', 'fair', 'poor']
        if v.lower() not in valid_conditions:
            raise ValueError(f'Condition must be one of: {", ".join(valid_conditions)}')
        return v.lower()


class ProductCreate(ProductBaseSchema):
    """Schema for product creation."""
    
    images: Optional[List[str]] = Field(default=[], description="Product image URLs")
    tags: Optional[List[str]] = Field(default=[], description="Product tags")
    is_negotiable: bool = Field(default=True, description="Whether price is negotiable")
    is_available: bool = Field(default=True, description="Whether product is available")


class ProductUpdate(BaseUpdateSchema):
    """Schema for product updates."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Product name")
    description: Optional[str] = Field(None, min_length=1, max_length=2000, description="Product description")
    price: Optional[Decimal] = Field(None, gt=0, description="Product price")
    category: Optional[str] = Field(None, min_length=1, max_length=100, description="Product category")
    condition: Optional[str] = Field(None, description="Product condition")
    location: Optional[str] = Field(None, min_length=1, max_length=200, description="Product location")
    images: Optional[List[str]] = Field(None, description="Product image URLs")
    tags: Optional[List[str]] = Field(None, description="Product tags")
    is_negotiable: Optional[bool] = Field(None, description="Whether price is negotiable")
    is_available: Optional[bool] = Field(None, description="Whether product is available")


class ProductResponse(BaseResponseSchema):
    """Schema for product response data."""
    
    name: str = Field(..., description="Product name")
    description: str = Field(..., description="Product description")
    price: Decimal = Field(..., description="Product price")
    category: str = Field(..., description="Product category")
    condition: str = Field(..., description="Product condition")
    location: str = Field(..., description="Product location")
    images: List[str] = Field(default=[], description="Product image URLs")
    tags: List[str] = Field(default=[], description="Product tags")
    is_negotiable: bool = Field(..., description="Whether price is negotiable")
    is_available: bool = Field(..., description="Whether product is available")
    owner_id: UUID = Field(..., description="Product owner ID")
    view_count: int = Field(default=0, description="Number of views")
    like_count: int = Field(default=0, description="Number of likes")


class ProductListResponse(BaseResponseSchema):
    """Schema for product list response (limited information)."""
    
    name: str = Field(..., description="Product name")
    price: Decimal = Field(..., description="Product price")
    category: str = Field(..., description="Product category")
    condition: str = Field(..., description="Product condition")
    location: str = Field(..., description="Product location")
    images: List[str] = Field(default=[], description="Product image URLs")
    is_available: bool = Field(..., description="Whether product is available")
    owner_id: UUID = Field(..., description="Product owner ID")
    view_count: int = Field(default=0, description="Number of views")
