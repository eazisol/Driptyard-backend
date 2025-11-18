"""
Order-related database models.

This module contains Order models for the e-commerce platform.
"""

from sqlalchemy import Column, String, Text, Numeric, Boolean, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.models.base import UserProductBaseModel


class Order(UserProductBaseModel):
    """Order model for storing order information."""
    
    __tablename__ = "orders"
    
    # Order identification
    order_number = Column(String(50), unique=True, nullable=False, index=True)
    
    # Product and participants
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    buyer_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
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
    
    # Relationships
    product = relationship("Product", foreign_keys=[product_id])
    buyer = relationship("User", foreign_keys=[buyer_id])
    seller = relationship("User", foreign_keys=[seller_id])