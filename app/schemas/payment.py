"""
Payment Pydantic schemas.

This module contains all Pydantic schemas related to payment operations
including request/response validation for payment endpoints.
"""

from typing import Optional
from pydantic import Field, validator
from decimal import Decimal
from uuid import UUID
from enum import Enum

from app.schemas.base import BaseResponseSchema, BaseCreateSchema, BaseUpdateSchema


class PaymentStatus(str, Enum):
    """Payment status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentMethod(str, Enum):
    """Payment method enumeration."""
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    PAYPAL = "paypal"
    STRIPE = "stripe"
    BANK_TRANSFER = "bank_transfer"


class PaymentBaseSchema(BaseCreateSchema):
    """Base payment schema with common fields."""
    
    order_id: UUID = Field(..., description="Order ID")
    amount: Decimal = Field(..., gt=0, description="Payment amount")
    currency: str = Field(default="USD", min_length=3, max_length=3, description="Payment currency")
    payment_method: PaymentMethod = Field(..., description="Payment method")
    description: Optional[str] = Field(None, max_length=500, description="Payment description")


class PaymentCreate(PaymentBaseSchema):
    """Schema for payment creation."""
    
    pass


class PaymentUpdate(BaseUpdateSchema):
    """Schema for payment updates."""
    
    status: Optional[PaymentStatus] = Field(None, description="Payment status")
    transaction_id: Optional[str] = Field(None, max_length=100, description="External transaction ID")
    gateway_response: Optional[dict] = Field(None, description="Payment gateway response")


class PaymentResponse(BaseResponseSchema):
    """Schema for payment response data."""
    
    order_id: UUID = Field(..., description="Order ID")
    payer_id: UUID = Field(..., description="Payer ID")
    payee_id: UUID = Field(..., description="Payee ID")
    amount: Decimal = Field(..., description="Payment amount")
    currency: str = Field(..., description="Payment currency")
    status: PaymentStatus = Field(..., description="Payment status")
    payment_method: PaymentMethod = Field(..., description="Payment method")
    description: Optional[str] = Field(None, description="Payment description")
    transaction_id: Optional[str] = Field(None, description="External transaction ID")
    gateway_response: Optional[dict] = Field(None, description="Payment gateway response")
    processed_at: Optional[str] = Field(None, description="Payment processing timestamp")


class PaymentStatus(BaseCreateSchema):
    """Schema for payment status response."""
    
    status: PaymentStatus = Field(..., description="Current payment status")
    transaction_id: Optional[str] = Field(None, description="External transaction ID")
    gateway_status: Optional[str] = Field(None, description="Gateway-specific status")
    last_updated: str = Field(..., description="Last status update timestamp")
