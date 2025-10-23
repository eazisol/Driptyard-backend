"""
Order Pydantic schemas.

This module contains all Pydantic schemas related to order operations
including request/response validation for order endpoints.
"""

from typing import Optional
from pydantic import Field, validator
from decimal import Decimal
from uuid import UUID
from enum import Enum

from app.schemas.base import BaseResponseSchema, BaseCreateSchema, BaseUpdateSchema


class OrderStatus(str, Enum):
    """Order status enumeration."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class OrderBaseSchema(BaseCreateSchema):
    """Base order schema with common fields."""
    
    product_id: UUID = Field(..., description="Product ID")
    quantity: int = Field(..., ge=1, description="Order quantity")
    total_amount: Decimal = Field(..., gt=0, description="Total order amount")
    shipping_address: str = Field(..., min_length=1, max_length=500, description="Shipping address")
    notes: Optional[str] = Field(None, max_length=500, description="Order notes")


class OrderCreate(OrderBaseSchema):
    """Schema for order creation."""
    
    pass


class OrderUpdate(BaseUpdateSchema):
    """Schema for order updates."""
    
    status: Optional[OrderStatus] = Field(None, description="Order status")
    shipping_address: Optional[str] = Field(None, min_length=1, max_length=500, description="Shipping address")
    notes: Optional[str] = Field(None, max_length=500, description="Order notes")
    tracking_number: Optional[str] = Field(None, max_length=100, description="Shipping tracking number")


class OrderResponse(BaseResponseSchema):
    """Schema for order response data."""
    
    product_id: UUID = Field(..., description="Product ID")
    buyer_id: UUID = Field(..., description="Buyer ID")
    seller_id: UUID = Field(..., description="Seller ID")
    quantity: int = Field(..., description="Order quantity")
    total_amount: Decimal = Field(..., description="Total order amount")
    status: OrderStatus = Field(..., description="Order status")
    shipping_address: str = Field(..., description="Shipping address")
    notes: Optional[str] = Field(None, description="Order notes")
    tracking_number: Optional[str] = Field(None, description="Shipping tracking number")
    shipped_at: Optional[str] = Field(None, description="Shipping timestamp")
    delivered_at: Optional[str] = Field(None, description="Delivery timestamp")


class OrderStatusUpdate(BaseUpdateSchema):
    """Schema for order status updates."""
    
    status: OrderStatus = Field(..., description="New order status")
    tracking_number: Optional[str] = Field(None, max_length=100, description="Shipping tracking number")
    notes: Optional[str] = Field(None, max_length=500, description="Status update notes")
