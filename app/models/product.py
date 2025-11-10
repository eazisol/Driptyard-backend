"""
Product-related database models.

This module contains Product models for the e-commerce platform.
"""

from sqlalchemy import Column, String, Text, Numeric, Boolean, Integer, Float, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Product(BaseModel):
    """Product model for storing product information."""
    
    __tablename__ = "products"
    
    # Basic product information
    title = Column(String(255), nullable=False, index=True)  # Changed from name to title
    description = Column(Text, nullable=True)
    price = Column(Numeric(10, 2), nullable=False)
    category = Column(String(100), nullable=True, index=True)
    condition = Column(String(50), nullable=True)  # Like New, Excellent, Brand New, Good, Fair
    
    # Deal method and meetup details
    deal_method = Column(String(20), nullable=False, default="delivery")  # delivery or meetup
    meetup_date = Column(String(10), nullable=True)  # YYYY-MM-DD format
    meetup_location = Column(String(255), nullable=True)
    meetup_time = Column(String(5), nullable=True)  # HH:MM format
    
    # Product status
    is_active = Column(Boolean, default=True, nullable=False)
    is_sold = Column(Boolean, default=False, nullable=False)
    is_featured = Column(Boolean, default=False, nullable=False, index=True)
    is_verified = Column(Boolean, default=False, nullable=False, index=True)
    verification_code = Column(String(6), nullable=True)
    verification_expires_at = Column(DateTime, nullable=True)
    verification_attempts = Column(Integer, default=0, nullable=False)
    
    # Stock management
    stock_quantity = Column(Integer, default=1, nullable=False)
    stock_status = Column(String(50), default="In Stock", nullable=False)  # In Stock, Out of Stock, Limited
    
    # Location and shipping
    location = Column(String(255), nullable=True)
    shipping_cost = Column(Numeric(10, 2), nullable=True)
    delivery_days = Column(String(50), nullable=True)  # e.g., "2-3 business days"
    
    # Owner information
    owner_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Product details
    brand = Column(String(100), nullable=True)
    model = Column(String(100), nullable=True)
    year = Column(Integer, nullable=True)
    sku = Column(String(100), nullable=True, unique=True)
    gender = Column(String(20), nullable=True)
    product_type = Column(String(100), nullable=True)
    sub_category = Column(String(100), nullable=True)
    designer = Column(String(100), nullable=True)
    size = Column(String(50), nullable=True)
    colors = Column(JSON, nullable=True)
    product_style = Column(String(50), nullable=True)
    measurement_chest = Column(String(50), nullable=True)
    measurement_sleeve_length = Column(String(50), nullable=True)
    measurement_length = Column(String(50), nullable=True)
    measurement_hem = Column(String(50), nullable=True)
    measurement_shoulders = Column(String(50), nullable=True)
    purchase_button_enabled = Column(Boolean, default=True, nullable=False)
    delivery_method = Column(String(20), nullable=True)
    delivery_time = Column(String(20), nullable=True)
    delivery_fee = Column(Numeric(10, 2), nullable=True)
    delivery_fee_type = Column(String(20), nullable=True)
    tracking_provided = Column(Boolean, default=False, nullable=False)
    shipping_address = Column(String(255), nullable=True)
    meetup_locations = Column(JSON, nullable=True)
    
    # Ratings and reviews
    rating = Column(Float, default=0.0, nullable=False)
    review_count = Column(Integer, default=0, nullable=False)
    
    # Images (stored as JSON array of URLs)
    images = Column(JSON, nullable=True)  # Array of image URLs
    
    # Additional details (stored as JSON)
    specifications = Column(JSON, nullable=True)  # Product specs (weight, dimensions, material, etc.)
    key_features = Column(JSON, nullable=True)  # Array of key features
    tags = Column(JSON, nullable=True)  # Array of tags
    
    # Seller policies
    return_policy = Column(String(255), default="30-day return policy", nullable=True)
    warranty_info = Column(String(255), nullable=True)
    packaging_info = Column(String(255), default="Secure packaging for safe delivery", nullable=True)
    
    # Search and filtering
    condition_badge = Column(String(50), nullable=True)  # "Like New", "Excellent", "Brand New"
    
    # TODO: Add relationships when other models are ready
    # owner = relationship("User", back_populates="products")
    # orders = relationship("Order", back_populates="product")
    # reviews = relationship("Review", back_populates="product")