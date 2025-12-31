"""
Spotlight-related database models.

This module contains Spotlight and SpotlightHistory models for tracking
admin-promoted product listings.
"""

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.models.base import UserProductBaseModel


class Spotlight(UserProductBaseModel):
    """Spotlight model for tracking active spotlighted listings."""
    
    __tablename__ = "spotlights"
    
    # Product and admin information
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, unique=True, index=True)
    applied_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Timing information
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False, index=True)
    duration_hours = Column(Integer, nullable=False)
    
    # Status tracking
    status = Column(String(20), nullable=False, default="active", index=True)  # active, expired, removed, paused
    
    # Relationships
    product = relationship("Product", foreign_keys=[product_id])
    admin = relationship("User", foreign_keys=[applied_by])
    
    __table_args__ = (
        Index('idx_spotlight_status_end_time', 'status', 'end_time'),
    )


class SpotlightHistory(UserProductBaseModel):
    """Spotlight history model for audit trail."""
    
    __tablename__ = "spotlight_history"
    
    # References
    spotlight_id = Column(Integer, ForeignKey("spotlights.id"), nullable=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    
    # Action information
    action = Column(String(20), nullable=False, index=True)  # applied, expired, removed, paused, resumed
    applied_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    removed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Timing information
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    duration_hours = Column(Integer, nullable=False)
    
    # Relationships
    spotlight = relationship("Spotlight", foreign_keys=[spotlight_id])
    product = relationship("Product", foreign_keys=[product_id])
    applied_by_user = relationship("User", foreign_keys=[applied_by])
    removed_by_user = relationship("User", foreign_keys=[removed_by])
    
    __table_args__ = (
        Index('idx_spotlight_history_created', 'created_at'),
        Index('idx_spotlight_history_action', 'action'),
    )

