"""
Audit log-related Pydantic schemas.

This module contains audit log request and response schemas.
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class AuditLogResponse(BaseModel):
    """Schema for a single audit log entry."""
    
    id: str = Field(..., description="Audit log ID")
    timestamp: datetime = Field(..., description="When the action was performed")
    admin: str = Field(..., description="Username of the admin/moderator who performed the action")
    is_admin: bool = Field(..., description="True if performer is admin, False if moderator")
    action: str = Field(..., description="Action performed (e.g., 'Suspended User', 'Removed Listing')")
    target: str = Field(..., description="Target identifier (e.g., user ID, product ID, product title)")
    target_type: str = Field(..., description="Type of target (user, product, spotlight, moderator)")
    action_type: str = Field(..., description="Type of action category")
    details: Optional[str] = Field(None, description="Additional details about the action")
    
    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    """Schema for paginated audit log list."""
    
    logs: list[AuditLogResponse] = Field(..., description="List of audit log entries")
    total: int = Field(..., description="Total number of audit log entries")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")
    available_actions: list[str] = Field(default_factory=list, description="List of all available action names for filtering")
    
    class Config:
        from_attributes = True

