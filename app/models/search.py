"""
Search-related database models.

This module contains models for user recent searches and search analytics.
"""

from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Index, UniqueConstraint, func
from sqlalchemy.orm import relationship

from app.models.base import UserProductBaseModel


class UserRecentSearch(UserProductBaseModel):
    """Model for storing user's recent search queries."""
    
    __tablename__ = "user_recent_searches"
    
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    query = Column(String(255), nullable=False)
    searched_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Unique constraint on user_id and lowercase query
    __table_args__ = (
        UniqueConstraint('user_id', 'query', name='uq_user_recent_search_user_query'),
        Index('idx_user_recent_searches_user_id', 'user_id'),
        Index('idx_user_recent_searches_searched_at', 'searched_at'),
    )
    
    # Relationship
    user = relationship("User", foreign_keys=[user_id])


class SearchAnalytics(UserProductBaseModel):
    """Model for tracking search analytics (for popular searches)."""
    
    __tablename__ = "search_analytics"
    
    query = Column(String(255), nullable=False, index=True)
    searched_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    result_count = Column(Integer, nullable=True)
    
    # Indexes for efficient queries
    __table_args__ = (
        Index('idx_search_analytics_query', 'query'),
        Index('idx_search_analytics_searched_at', 'searched_at'),
        Index('idx_search_analytics_user_id', 'user_id'),
    )
    
    # Relationship
    user = relationship("User", foreign_keys=[user_id])

