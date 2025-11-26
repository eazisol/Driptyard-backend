"""
Moderator-related Pydantic schemas.

This module contains moderator-related request and response schemas.
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class ModeratorPermissionRequest(BaseModel):
    """Schema for updating moderator permissions."""
    
    # Dashboard permissions
    can_see_dashboard: Optional[bool] = Field(None, description="Whether moderator can see dashboard")
    
    # Users permissions
    can_see_users: Optional[bool] = Field(None, description="Whether moderator can see users")
    can_manage_users: Optional[bool] = Field(None, description="Whether moderator can manage users")
    
    # Listings permissions
    can_see_listings: Optional[bool] = Field(None, description="Whether moderator can see listings")
    can_manage_listings: Optional[bool] = Field(None, description="Whether moderator can manage listings")
    
    # Spotlight permissions
    can_see_spotlight_history: Optional[bool] = Field(None, description="Whether moderator can see spotlight history")
    can_spotlight: Optional[bool] = Field(None, description="Whether moderator can apply spotlight")
    can_remove_spotlight: Optional[bool] = Field(None, description="Whether moderator can remove spotlight")
    
    # Flagged content permissions
    can_see_flagged_content: Optional[bool] = Field(None, description="Whether moderator can see flagged content")
    can_manage_flagged_content: Optional[bool] = Field(None, description="Whether moderator can manage flagged content")


class ModeratorPermissionResponse(BaseModel):
    """Schema for moderator permissions response."""
    
    user_id: str = Field(..., description="User ID")
    
    # Dashboard permissions
    can_see_dashboard: bool = Field(..., description="Whether moderator can see dashboard")
    
    # Users permissions
    can_see_users: bool = Field(..., description="Whether moderator can see users")
    can_manage_users: bool = Field(..., description="Whether moderator can manage users")
    
    # Listings permissions
    can_see_listings: bool = Field(..., description="Whether moderator can see listings")
    can_manage_listings: bool = Field(..., description="Whether moderator can manage listings")
    
    # Spotlight permissions
    can_see_spotlight_history: bool = Field(..., description="Whether moderator can see spotlight history")
    can_spotlight: bool = Field(..., description="Whether moderator can apply spotlight")
    can_remove_spotlight: bool = Field(..., description="Whether moderator can remove spotlight")
    
    # Flagged content permissions
    can_see_flagged_content: bool = Field(..., description="Whether moderator can see flagged content")
    can_manage_flagged_content: bool = Field(..., description="Whether moderator can manage flagged content")
    
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True


class ModeratorResponse(BaseModel):
    """Schema for moderator user info with permissions."""
    
    id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    username: str = Field(..., description="Username")
    first_name: Optional[str] = Field(None, description="First name")
    last_name: Optional[str] = Field(None, description="Last name")
    phone: Optional[str] = Field(None, description="Phone number")
    country_code: Optional[str] = Field(None, description="Country code")
    is_active: bool = Field(..., description="Whether user is active")
    is_verified: bool = Field(..., description="Whether user is verified")
    is_moderator: bool = Field(..., description="Whether user is moderator")
    avatar_url: Optional[str] = Field(None, description="Avatar URL")
    permissions: Optional[ModeratorPermissionResponse] = Field(None, description="Moderator permissions")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    class Config:
        from_attributes = True


class ModeratorListResponse(BaseModel):
    """Schema for moderator list with pagination."""
    
    moderators: List[ModeratorResponse] = Field(..., description="List of moderators")
    total: int = Field(..., description="Total number of moderators")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")
    
    class Config:
        from_attributes = True


class AssignModeratorRequest(BaseModel):
    """Schema for assigning moderator role (optional permissions override)."""
    
    # Dashboard permissions
    can_see_dashboard: Optional[bool] = Field(None, description="Whether moderator can see dashboard (default: True)")
    
    # Users permissions
    can_see_users: Optional[bool] = Field(None, description="Whether moderator can see users (default: True)")
    can_manage_users: Optional[bool] = Field(None, description="Whether moderator can manage users (default: False)")
    
    # Listings permissions
    can_see_listings: Optional[bool] = Field(None, description="Whether moderator can see listings (default: True)")
    can_manage_listings: Optional[bool] = Field(None, description="Whether moderator can manage listings (default: False)")
    
    # Spotlight permissions
    can_see_spotlight_history: Optional[bool] = Field(None, description="Whether moderator can see spotlight history (default: True)")
    can_spotlight: Optional[bool] = Field(None, description="Whether moderator can apply spotlight (default: True)")
    can_remove_spotlight: Optional[bool] = Field(None, description="Whether moderator can remove spotlight (default: False)")
    
    # Flagged content permissions
    can_see_flagged_content: Optional[bool] = Field(None, description="Whether moderator can see flagged content (default: True)")
    can_manage_flagged_content: Optional[bool] = Field(None, description="Whether moderator can manage flagged content (default: False)")

