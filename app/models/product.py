"""
Product-related database models.

This module contains Product models for the e-commerce platform.
"""

from sqlalchemy import Column, String, Text, Numeric, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import BaseModel


class Product(BaseModel):
    """Product model for storing product information."""
    
    __tablename__ = "products"
    
    # Basic product information
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    price = Column(Numeric(10, 2), nullable=False)
    category = Column(String(100), nullable=True, index=True)
    condition = Column(String(50), nullable=True)  # new, like_new, good, fair, poor
    
    # Product status
    is_active = Column(Boolean, default=True, nullable=False)
    is_sold = Column(Boolean, default=False, nullable=False)
    
    # Location and shipping
    location = Column(String(255), nullable=True)
    shipping_cost = Column(Numeric(10, 2), nullable=True)
    
    # Owner information
    owner_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Product details
    brand = Column(String(100), nullable=True)
    model = Column(String(100), nullable=True)
    year = Column(Integer, nullable=True)
    
    # Images (stored as JSON array of URLs)
    images = Column(Text, nullable=True)  # JSON string of image URLs
    
    # Search and filtering
    tags = Column(Text, nullable=True)  # JSON string of tags
    
    # TODO: Add relationships when other models are ready
    # owner = relationship("User", back_populates="products")
    # orders = relationship("Order", back_populates="product")