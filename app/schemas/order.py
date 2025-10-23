"""
Order-related Pydantic schemas.

This module contains all order-related request and response schemas.
"""

from typing import Optional
from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import datetime

from app.schemas.base import BaseCreateSchema, BaseUpdateSchema, BaseResponseSchema


class OrderCreate(BaseCreateSchema):
    """Schema for creating an order."""
    
    product_id: str = Field(..., description="Product ID")
    quantity: int = Field(..., ge=1, description="Order quantity")
    shipping_address: Optional[str] = Field(None, description="Shipping address")
    notes: Optional[str] = Field(None, description="Order notes")


class OrderUpdate(BaseUpdateSchema):
    """Schema for updating an order."""
    
    status: Optional[str] = Field(None, description="Order status")
    payment_status: Optional[str] = Field(None, description="Payment status")
    tracking_number: Optional[str] = Field(None, description="Tracking number")
    estimated_delivery: Optional[datetime] = Field(None, description="Estimated delivery date")
    delivered_at: Optional[datetime] = Field(None, description="Actual delivery date")
    notes: Optional[str] = Field(None, description="Order notes")
    buyer_notes: Optional[str] = Field(None, description="Buyer notes")
    seller_notes: Optional[str] = Field(None, description="Seller notes")


class OrderResponse(BaseResponseSchema):
    """Schema for order response data."""
    
    order_number: str = Field(..., description="Order number")
    product_id: str = Field(..., description="Product ID")
    buyer_id: str = Field(..., description="Buyer ID")
    seller_id: str = Field(..., description="Seller ID")
    quantity: int = Field(..., description="Order quantity")
    unit_price: Decimal = Field(..., description="Unit price")
    total_amount: Decimal = Field(..., description="Total amount")
    shipping_cost: Optional[Decimal] = Field(None, description="Shipping cost")
    status: str = Field(..., description="Order status")
    payment_status: str = Field(..., description="Payment status")
    shipping_address: Optional[str] = Field(None, description="Shipping address")
    tracking_number: Optional[str] = Field(None, description="Tracking number")
    estimated_delivery: Optional[datetime] = Field(None, description="Estimated delivery date")
    delivered_at: Optional[datetime] = Field(None, description="Actual delivery date")
    notes: Optional[str] = Field(None, description="Order notes")
    buyer_notes: Optional[str] = Field(None, description="Buyer notes")
    seller_notes: Optional[str] = Field(None, description="Seller notes")
