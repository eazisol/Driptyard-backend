"""
Audit log database models.

This module contains AuditLog model for tracking admin and moderator actions.
"""

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import relationship

from app.models.base import UserProductBaseModel


class AuditLog(UserProductBaseModel):
    """Audit log model for tracking admin and moderator actions."""
    
    __tablename__ = "audit_logs"
    
    # Admin/Moderator information
    performed_by_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    performed_by_username = Column(String(100), nullable=False)  # Store username for historical reference
    is_admin = Column(String(20), nullable=False, default="admin")  # "admin" or "moderator"
    
    # Action information
    action = Column(String(100), nullable=False, index=True)  # e.g., "Suspended User", "Removed Listing", "Applied Spotlight"
    action_type = Column(String(50), nullable=False, index=True)  # user, product, spotlight, moderator, report
    
    # Target information
    target_type = Column(String(50), nullable=False, index=True)  # user, product, spotlight, moderator
    target_id = Column(String(100), nullable=False, index=True)  # ID of the target (user_id, product_id, etc.)
    target_identifier = Column(String(255), nullable=True)  # Human-readable identifier (username, product title, etc.)
    
    # Additional details (stored as JSON-like text for flexibility)
    details = Column(Text, nullable=True)  # Additional context about the action
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6 address
    user_agent = Column(Text, nullable=True)  # User agent string
    
    # Relationships
    performed_by = relationship("User", foreign_keys=[performed_by_id])
    
    __table_args__ = (
        Index('idx_audit_log_performed_by', 'performed_by_id'),
        Index('idx_audit_log_action', 'action'),
        Index('idx_audit_log_action_type', 'action_type'),
        Index('idx_audit_log_target', 'target_type', 'target_id'),
        Index('idx_audit_log_created_at', 'created_at'),
    )
    
    def __repr__(self) -> str:
        """String representation of the audit log entry."""
        return f"<AuditLog(id={self.id}, action='{self.action}', target='{self.target_type}:{self.target_id}')>"

