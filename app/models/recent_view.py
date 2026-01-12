"""
Recent View database model.

This module contains the model for tracking products recently viewed by users.
"""

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func, UniqueConstraint, Index
from sqlalchemy.orm import relationship

from app.models.base import UserProductBaseModel


class RecentView(UserProductBaseModel):
    """RecentView model for storing user product browsing history."""
    
    __tablename__ = "recent_views"
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    ip_address = Column(String(45), nullable=True, index=True) # supports IPv6
    viewed_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Unique constraints:
    # 1. (user_id, product_id) when user is logged in
    # 2. (ip_address, product_id) when guest
    __table_args__ = (
        Index('idx_recent_views_user_viewed_at', 'user_id', 'viewed_at'),
        Index('idx_recent_views_ip_viewed_at', 'ip_address', 'viewed_at'),
    )
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    product = relationship("Product", foreign_keys=[product_id])
