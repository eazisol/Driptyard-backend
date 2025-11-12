"""
Admin-related Pydantic schemas.

This module contains admin-related request and response schemas.
"""

from pydantic import BaseModel, Field


class StatsOverviewResponse(BaseModel):
    """Schema for admin stats overview response."""
    
    total_users: int = Field(..., description="Total number of users")
    users_change: float = Field(..., description="Percentage change in users compared to previous period")
    total_products: int = Field(..., description="Total number of products (listings)")
    products_change: float = Field(..., description="Percentage change in products compared to previous period")
    pending_verifications: int = Field(..., description="Number of users pending verification")
    flagged_content_count: int = Field(..., description="Number of flagged content items (unverified products)")

