"""
Moderator-related database models.

This module contains ModeratorPermission model for managing moderator permissions.
"""

from sqlalchemy import Column, Boolean, Integer, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.models.base import UserProductBaseModel


class ModeratorPermission(UserProductBaseModel):
    """ModeratorPermission model for storing moderator-specific permissions."""
    
    __tablename__ = "moderator_permissions"
    
    # User reference
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    
    # Dashboard permissions
    can_see_dashboard = Column(Boolean, default=True, nullable=False)
    
    # Users permissions
    can_see_users = Column(Boolean, default=True, nullable=False)
    can_manage_users = Column(Boolean, default=False, nullable=False)
    
    # Listings permissions
    can_see_listings = Column(Boolean, default=True, nullable=False)
    can_manage_listings = Column(Boolean, default=False, nullable=False)
    
    # Spotlight permissions
    can_see_spotlight_history = Column(Boolean, default=True, nullable=False)
    can_spotlight = Column(Boolean, default=True, nullable=False)
    can_remove_spotlight = Column(Boolean, default=False, nullable=False)
    
    # Flagged content permissions
    can_see_flagged_content = Column(Boolean, default=True, nullable=False)
    can_manage_flagged_content = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    
    __table_args__ = (
        Index('idx_moderator_permissions_user', 'user_id'),
    )

