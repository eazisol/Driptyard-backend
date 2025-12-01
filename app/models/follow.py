"""
Follow-related database models.

This module contains models for user-to-seller follows and user-to-product follows.
"""

from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint, CheckConstraint, Index
from sqlalchemy.orm import relationship

from app.models.base import UserProductBaseModel


class SellerFollow(UserProductBaseModel):
    """Seller follow model for storing user-to-seller follow relationships."""
    
    __tablename__ = "seller_follows"
    
    follower_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    followed_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Unique constraint: one follow relationship per user pair
    __table_args__ = (
        UniqueConstraint('follower_id', 'followed_user_id', name='uq_follower_followed_user'),
        CheckConstraint('follower_id != followed_user_id', name='ck_no_self_follow'),
        Index('idx_follower_id', 'follower_id'),
        Index('idx_followed_user_id', 'followed_user_id'),
    )
    
    # Relationships
    follower = relationship("User", foreign_keys=[follower_id])
    followed_user = relationship("User", foreign_keys=[followed_user_id])


class ProductFollow(UserProductBaseModel):
    """Product follow model for storing user-to-product follow relationships."""
    
    __tablename__ = "product_follows"
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    
    # Unique constraint: one follow relationship per user-product pair
    __table_args__ = (
        UniqueConstraint('user_id', 'product_id', name='uq_user_product_follow'),
        Index('idx_user_id', 'user_id'),
        Index('idx_product_id', 'product_id'),
    )
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    product = relationship("Product", foreign_keys=[product_id])

