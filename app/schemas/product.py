"""
Product-related Pydantic schemas.

This module contains all product-related request and response schemas.
"""

from typing import Optional, List
from pydantic import BaseModel, Field
from decimal import Decimal

from app.schemas.base import BaseCreateSchema, BaseUpdateSchema, BaseResponseSchema


class ProductCreate(BaseCreateSchema):
    """Schema for creating a product."""
    
    name: str = Field(..., min_length=1, max_length=255, description="Product name")
    description: Optional[str] = Field(None, description="Product description")
    price: Decimal = Field(..., gt=0, description="Product price")
    category: Optional[str] = Field(None, max_length=100, description="Product category")
    condition: Optional[str] = Field(None, description="Product condition")
    location: Optional[str] = Field(None, max_length=255, description="Product location")
    shipping_cost: Optional[Decimal] = Field(None, ge=0, description="Shipping cost")
    brand: Optional[str] = Field(None, max_length=100, description="Product brand")
    model: Optional[str] = Field(None, max_length=100, description="Product model")
    year: Optional[int] = Field(None, ge=1900, le=2030, description="Product year")
    tags: Optional[List[str]] = Field(None, description="Product tags")


class ProductUpdate(BaseUpdateSchema):
    """Schema for updating a product."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Product name")
    description: Optional[str] = Field(None, description="Product description")
    price: Optional[Decimal] = Field(None, gt=0, description="Product price")
    category: Optional[str] = Field(None, max_length=100, description="Product category")
    condition: Optional[str] = Field(None, description="Product condition")
    location: Optional[str] = Field(None, max_length=255, description="Product location")
    shipping_cost: Optional[Decimal] = Field(None, ge=0, description="Shipping cost")
    brand: Optional[str] = Field(None, max_length=100, description="Product brand")
    model: Optional[str] = Field(None, max_length=100, description="Product model")
    year: Optional[int] = Field(None, ge=1900, le=2030, description="Product year")
    tags: Optional[List[str]] = Field(None, description="Product tags")
    is_active: Optional[bool] = Field(None, description="Whether product is active")


class ProductResponse(BaseResponseSchema):
    """Schema for product response data."""
    
    name: str = Field(..., description="Product name")
    description: Optional[str] = Field(None, description="Product description")
    price: Decimal = Field(..., description="Product price")
    category: Optional[str] = Field(None, description="Product category")
    condition: Optional[str] = Field(None, description="Product condition")
    location: Optional[str] = Field(None, description="Product location")
    shipping_cost: Optional[Decimal] = Field(None, description="Shipping cost")
    brand: Optional[str] = Field(None, description="Product brand")
    model: Optional[str] = Field(None, description="Product model")
    year: Optional[int] = Field(None, description="Product year")
    tags: Optional[List[str]] = Field(None, description="Product tags")
    is_active: bool = Field(..., description="Whether product is active")
    is_sold: bool = Field(..., description="Whether product is sold")
    owner_id: str = Field(..., description="Product owner ID")
