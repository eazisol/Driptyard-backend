"""
Order-related database models.

This module contains Order models for the e-commerce platform.
"""

from sqlalchemy import Column, String, Text, Numeric, Boolean, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import BaseModel


class Order(BaseModel):
    """Order model for storing order information."""
    
    __tablename__ = "orders"
    
    # Order identification
    order_number = Column(String(50), unique=True, nullable=False, index=True)
    
    # Product and participants
    product_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    buyer_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    seller_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Order details
    quantity = Column(Integer, default=1, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False)
    shipping_cost = Column(Numeric(10, 2), nullable=True)
    
    # Order status
    status = Column(String(50), nullable=False, index=True)  # pending, confirmed, shipped, delivered, cancelled
    payment_status = Column(String(50), nullable=False, index=True)  # pending, paid, failed, refunded
    
    # Shipping information
    shipping_address = Column(Text, nullable=True)
    tracking_number = Column(String(100), nullable=True)
    estimated_delivery = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    
    # Communication
    notes = Column(Text, nullable=True)
    buyer_notes = Column(Text, nullable=True)
    seller_notes = Column(Text, nullable=True)
    
    # TODO: Add relationships when other models are ready
    # product = relationship("Product", back_populates="orders")
    # buyer = relationship("User", foreign_keys=[buyer_id], back_populates="orders_as_buyer")
    # seller = relationship("User", foreign_keys=[seller_id], back_populates="orders_as_seller")