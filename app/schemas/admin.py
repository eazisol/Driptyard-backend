"""
Admin-related Pydantic schemas.

This module contains admin-related request and response schemas.
"""

import re
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, EmailStr, field_validator, model_validator

from app.schemas.base import BaseCreateSchema


class FlaggedContentItem(BaseModel):
    """Schema for flagged content item in stats overview."""
    
    id: str = Field(..., description="Product ID")
    title: str = Field(..., description="Product title")
    owner_id: str = Field(..., description="Owner/seller ID")
    owner_name: Optional[str] = Field(None, description="Owner/seller username")
    created_at: datetime = Field(..., description="Creation timestamp")


class PendingVerificationItem(BaseModel):
    """Schema for pending verification user in stats overview."""
    
    id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    username: str = Field(..., description="Username")
    created_at: datetime = Field(..., description="Creation timestamp")


class ChartDataPoint(BaseModel):
    """Schema for a single data point in a chart."""
    
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    count: int = Field(..., description="Count for this date")
    cumulative: int = Field(..., description="Cumulative count up to this date")


class StatsOverviewResponse(BaseModel):
    """Schema for admin stats overview response."""
    
    total_users: int = Field(..., description="Total number of users")
    users_change: float = Field(..., description="Percentage change in users compared to previous period")
    total_products: int = Field(..., description="Total number of products (listings)")
    products_change: float = Field(..., description="Percentage change in products compared to previous period")
    pending_verifications: int = Field(..., description="Number of users pending verification")
    pending_verifications_change: float = Field(..., description="Percentage change in pending verifications compared to previous period")
    flagged_content_count: int = Field(..., description="Number of flagged content items (unverified products)")
    flagged_content_change: float = Field(..., description="Percentage change in flagged content compared to previous period")
    total_listings_removed: int = Field(..., description="Total number of listings removed (product_reports with status_id = 3)")
    listings_removed_change: float = Field(..., description="Percentage change in listings removed compared to previous period")
    flagged_content: List[FlaggedContentItem] = Field(default_factory=list, description="List of flagged content items")
    pending_verification_users: List[PendingVerificationItem] = Field(default_factory=list, description="List of users pending verification")
    users_growth_data: List[ChartDataPoint] = Field(default_factory=list, description="Daily user growth data for the last 30 days")
    products_growth_data: List[ChartDataPoint] = Field(default_factory=list, description="Daily product growth data for the last 30 days")


class AdminProductResponse(BaseModel):
    """Schema for admin product list item."""
    
    id: str = Field(..., description="Product ID")
    title: str = Field(..., description="Product title")
    price: Decimal = Field(..., description="Product price")
    category: Optional[str] = Field(None, description="Product category")
    condition: Optional[str] = Field(None, description="Product condition")
    stock_quantity: int = Field(..., description="Stock quantity")
    stock_status: str = Field(..., description="Stock status")
    is_active: bool = Field(..., description="Whether product is active")
    is_sold: bool = Field(..., description="Whether product is sold")
    is_verified: bool = Field(..., description="Whether product is verified")
    is_flagged: bool = Field(..., description="Whether product is flagged")
    images: List[str] = Field(default_factory=list, description="Product images")
    owner_id: str = Field(..., description="Owner/seller ID")
    owner_name: Optional[str] = Field(None, description="Owner/seller username")
    created_at: datetime = Field(..., description="Creation timestamp")


class AdminProductListResponse(BaseModel):
    """Schema for admin product list with pagination."""
    
    products: List[AdminProductResponse] = Field(..., description="List of products")
    total: int = Field(..., description="Total number of products")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")
    
    class Config:
        from_attributes = True


class AdminProductUpdateRequest(BaseModel):
    """Schema for admin product update."""
    
    title: Optional[str] = Field(None, min_length=1, max_length=255, description="Product title")
    price: Optional[Decimal] = Field(None, ge=0, description="Product price")
    condition: Optional[str] = Field(None, max_length=50, description="Product condition")
    is_active: Optional[bool] = Field(None, description="Whether product is active")
    is_verified: Optional[bool] = Field(None, description="Whether product is verified")
    is_flagged: Optional[bool] = Field(None, description="Whether product is flagged")
    stock_status: Optional[str] = Field(None, description="Stock status: In Stock, Out of Stock, Limited")


class AdminUserResponse(BaseModel):
    """Schema for admin user list item."""
    
    id: str = Field(..., description="User ID")
    user_id: str = Field(..., description="User ID (alias for id)")
    email: str = Field(..., description="User email")
    username: str = Field(..., description="Username")
    first_name: Optional[str] = Field(None, description="First name")
    last_name: Optional[str] = Field(None, description="Last name")
    phone: Optional[str] = Field(None, description="Phone number")
    country_code: Optional[str] = Field(None, description="Country code")
    bio: Optional[str] = Field(None, description="User bio")
    is_active: bool = Field(..., description="Whether user is active")
    is_verified: bool = Field(..., description="Whether user is verified")
    is_banned: bool = Field(..., description="Whether user is banned (is_active=False)")
    is_suspended: bool = Field(..., description="Whether user is suspended")
    is_admin: bool = Field(..., description="Whether user is admin")
    is_moderator: bool = Field(..., description="Whether user is moderator")
    avatar_url: Optional[str] = Field(None, description="Avatar URL")
    listings_count: int = Field(0, description="Count of user's active listings")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")


class AdminUserListResponse(BaseModel):
    """Schema for admin user list with pagination."""
    
    users: List[AdminUserResponse] = Field(..., description="List of users")
    total: int = Field(..., description="Total number of users")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")
    
    class Config:
        from_attributes = True


class AdminUserUpdateRequest(BaseModel):
    """Schema for admin user full profile update."""
    
    email: Optional[EmailStr] = Field(None, description="User email address")
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="Username")
    first_name: Optional[str] = Field(None, max_length=100, description="First name")
    last_name: Optional[str] = Field(None, max_length=100, description="Last name")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    country_code: Optional[str] = Field(None, min_length=2, max_length=3, description="Country code")
    bio: Optional[str] = Field(None, max_length=500, description="User bio")
    avatar_url: Optional[str] = Field(None, max_length=500, description="Avatar URL")
    company_name: Optional[str] = Field(None, max_length=200, description="Company name")
    sin_number: Optional[str] = Field(None, max_length=20, description="Social Insurance Number")
    is_active: Optional[bool] = Field(None, description="Whether user is active")
    is_verified: Optional[bool] = Field(None, description="Whether user is verified")
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        """Validate username format."""
        if v is None:
            return v
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username can only contain letters, numbers, underscores, and hyphens')
        return v.lower()


class AdminUserCreateRequest(BaseCreateSchema):
    """Schema for creating a user/moderator/admin (admin only)."""
    
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, max_length=100, description="User password")
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    phone: str = Field(..., description="Phone number with country code")
    country_code: str = Field(..., min_length=2, max_length=3, description="Country code")
    company_name: str | None = Field(None, max_length=200, description="Company name (optional)")
    sin_number: str | None = Field(None, max_length=20, description="Social Insurance Number (optional)")
    is_admin: bool = Field(False, description="Set to true to create an admin user (stored in DB)")
    is_moderator: bool = Field(False, description="Set to true to create a moderator user (stored in DB)")
    is_customer: bool = Field(True, description="Set to true to create a regular customer user (NOT stored in DB - sets both is_admin and is_moderator to False)")
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        """Validate username format."""
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username can only contain letters, numbers, underscores, and hyphens')
        if v.startswith(('_', '-')) or v.endswith(('_', '-')):
            raise ValueError('Username cannot start or end with underscore or hyphen')
        return v.lower()
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        """Validate phone number format."""
        if not re.match(r'^\+[1-9]\d{1,14}$', v):
            raise ValueError('Phone number must be in international format (+1234567890)')
        return v
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        # Check byte length (bcrypt has a 72-byte limit)
        if len(v.encode('utf-8')) > 72:
            raise ValueError('Password is too long (maximum 72 bytes when encoded)')
        
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v
    
    @model_validator(mode='after')
    def validate_user_type_flags(self):
        """
        Validate that exactly one user type flag is true.
        
        Note: is_customer is only used for validation and is NOT stored in the database.
        When is_customer=true, both is_admin and is_moderator will be set to False in DB.
        """
        is_admin = self.is_admin
        is_moderator = self.is_moderator
        is_customer = self.is_customer
        
        # Count how many flags are True
        true_count = sum([is_admin, is_moderator, is_customer])
        
        if true_count != 1:
            raise ValueError('Exactly one of is_admin, is_moderator, or is_customer must be true (and the others false)')
        
        return self


class AdminUserCreateResponse(BaseModel):
    """Schema for user creation response."""
    
    id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    username: str = Field(..., description="Username")
    phone: str = Field(..., description="Phone number")
    country_code: str = Field(..., description="Country code")
    is_active: bool = Field(..., description="Whether user is active")
    is_verified: bool = Field(..., description="Whether user is verified")
    is_moderator: bool = Field(..., description="Whether user is moderator")
    is_admin: bool = Field(..., description="Whether user is admin")
    created_at: datetime = Field(..., description="Creation timestamp")
    message: str = Field(..., description="Success message")


class SuspendUserResponse(BaseModel):
    """Schema for suspend user response."""
    
    success: bool = Field(True, description="Operation success status")
    message: str = Field(..., description="Success message")
    user_id: str = Field(..., description="User ID")
    suspended_at: datetime = Field(..., description="Suspension timestamp")


class UnsuspendUserResponse(BaseModel):
    """Schema for unsuspend user response."""
    
    success: bool = Field(True, description="Operation success status")
    message: str = Field(..., description="Success message")
    user_id: str = Field(..., description="User ID")
    unsuspended_at: datetime = Field(..., description="Unsuspension timestamp")


class ResetPasswordRequest(BaseModel):
    """Schema for password reset request."""
    
    new_password: str = Field(..., min_length=8, max_length=100, description="New password for the user")
    
    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        # Check byte length (bcrypt has a 72-byte limit)
        if len(v.encode('utf-8')) > 72:
            raise ValueError('Password is too long (maximum 72 bytes when encoded)')
        
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v


class ResetPasswordResponse(BaseModel):
    """Schema for password reset response."""
    
    success: bool = Field(True, description="Operation success status")
    message: str = Field(..., description="Success message")
    user_id: str = Field(..., description="User ID")


class DeleteUserResponse(BaseModel):
    """Schema for delete user response."""
    
    success: bool = Field(True, description="Operation success status")
    message: str = Field(..., description="Success message")
    user_id: str = Field(..., description="User ID")
    deleted_at: datetime = Field(..., description="Deletion timestamp")


# ============================================================================
# BULK ACTION SCHEMAS
# ============================================================================

class BulkDeleteUsersRequest(BaseModel):
    """Schema for bulk delete users request."""
    
    user_ids: List[int] = Field(..., min_length=1, max_length=100, description="List of user IDs to delete")
    
    @field_validator('user_ids')
    @classmethod
    def validate_user_ids(cls, v):
        """Validate that all IDs are positive integers."""
        if not v:
            raise ValueError('user_ids cannot be empty')
        if len(v) > 100:
            raise ValueError('Cannot delete more than 100 users at once')
        for user_id in v:
            if user_id <= 0:
                raise ValueError('All user IDs must be positive integers')
        return v


class BulkDeleteUsersResponse(BaseModel):
    """Schema for bulk delete users response."""
    
    message: str = Field(..., description="Success message")
    deleted_count: int = Field(..., description="Number of users deleted")
    deleted_ids: List[int] = Field(..., description="List of deleted user IDs")


class BulkUpdateUserStatusRequest(BaseModel):
    """Schema for bulk update user status request."""
    
    user_ids: List[int] = Field(..., min_length=1, max_length=100, description="List of user IDs to update")
    is_active: bool = Field(..., description="Active status to set")
    
    @field_validator('user_ids')
    @classmethod
    def validate_user_ids(cls, v):
        """Validate that all IDs are positive integers."""
        if not v:
            raise ValueError('user_ids cannot be empty')
        if len(v) > 100:
            raise ValueError('Cannot update more than 100 users at once')
        for user_id in v:
            if user_id <= 0:
                raise ValueError('All user IDs must be positive integers')
        return v


class BulkUpdateUserStatusResponse(BaseModel):
    """Schema for bulk update user status response."""
    
    message: str = Field(..., description="Success message")
    updated_count: int = Field(..., description="Number of users updated")
    updated_ids: List[int] = Field(..., description="List of updated user IDs")
    is_active: bool = Field(..., description="New active status")


class BulkDeleteProductsRequest(BaseModel):
    """Schema for bulk delete products request."""
    
    product_ids: List[int] = Field(..., min_length=1, max_length=100, description="List of product IDs to delete")
    
    @field_validator('product_ids')
    @classmethod
    def validate_product_ids(cls, v):
        """Validate that all IDs are positive integers."""
        if not v:
            raise ValueError('product_ids cannot be empty')
        if len(v) > 100:
            raise ValueError('Cannot delete more than 100 products at once')
        for product_id in v:
            if product_id <= 0:
                raise ValueError('All product IDs must be positive integers')
        return v


class BulkDeleteProductsResponse(BaseModel):
    """Schema for bulk delete products response."""
    
    message: str = Field(..., description="Success message")
    deleted_count: int = Field(..., description="Number of products deleted")
    deleted_ids: List[int] = Field(..., description="List of deleted product IDs")


class BulkUpdateProductStatusRequest(BaseModel):
    """Schema for bulk update product status request."""
    
    product_ids: List[int] = Field(..., min_length=1, max_length=100, description="List of product IDs to update")
    is_active: bool = Field(..., description="Active status to set")
    
    @field_validator('product_ids')
    @classmethod
    def validate_product_ids(cls, v):
        """Validate that all IDs are positive integers."""
        if not v:
            raise ValueError('product_ids cannot be empty')
        if len(v) > 100:
            raise ValueError('Cannot update more than 100 products at once')
        for product_id in v:
            if product_id <= 0:
                raise ValueError('All product IDs must be positive integers')
        return v


class BulkUpdateProductStatusResponse(BaseModel):
    """Schema for bulk update product status response."""
    
    message: str = Field(..., description="Success message")
    updated_count: int = Field(..., description="Number of products updated")
    updated_ids: List[int] = Field(..., description="List of updated product IDs")
    is_active: bool = Field(..., description="New active status")


class BulkUpdateProductVerificationRequest(BaseModel):
    """Schema for bulk update product verification request."""
    
    product_ids: List[int] = Field(..., min_length=1, max_length=100, description="List of product IDs to update")
    is_verified: bool = Field(..., description="Verification status to set")
    
    @field_validator('product_ids')
    @classmethod
    def validate_product_ids(cls, v):
        """Validate that all IDs are positive integers."""
        if not v:
            raise ValueError('product_ids cannot be empty')
        if len(v) > 100:
            raise ValueError('Cannot update more than 100 products at once')
        for product_id in v:
            if product_id <= 0:
                raise ValueError('All product IDs must be positive integers')
        return v


class BulkUpdateProductVerificationResponse(BaseModel):
    """Schema for bulk update product verification response."""
    
    message: str = Field(..., description="Success message")
    updated_count: int = Field(..., description="Number of products updated")
    updated_ids: List[int] = Field(..., description="List of updated product IDs")
    is_verified: bool = Field(..., description="New verification status")


class BulkApproveReportsRequest(BaseModel):
    """Schema for bulk approve reports request."""
    
    report_ids: List[int] = Field(..., min_length=1, max_length=100, description="List of report IDs to approve")
    
    @field_validator('report_ids')
    @classmethod
    def validate_report_ids(cls, v):
        """Validate that all IDs are positive integers."""
        if not v:
            raise ValueError('report_ids cannot be empty')
        if len(v) > 100:
            raise ValueError('Cannot approve more than 100 reports at once')
        for report_id in v:
            if report_id <= 0:
                raise ValueError('All report IDs must be positive integers')
        return v


class BulkApproveReportsResponse(BaseModel):
    """Schema for bulk approve reports response."""
    
    message: str = Field(..., description="Success message")
    approved_count: int = Field(..., description="Number of reports approved")
    approved_ids: List[int] = Field(..., description="List of approved report IDs")
    status: str = Field("approved", description="New status of reports")


class BulkRejectReportsRequest(BaseModel):
    """Schema for bulk reject reports request."""
    
    report_ids: List[int] = Field(..., min_length=1, max_length=100, description="List of report IDs to reject")
    
    @field_validator('report_ids')
    @classmethod
    def validate_report_ids(cls, v):
        """Validate that all IDs are positive integers."""
        if not v:
            raise ValueError('report_ids cannot be empty')
        if len(v) > 100:
            raise ValueError('Cannot reject more than 100 reports at once')
        for report_id in v:
            if report_id <= 0:
                raise ValueError('All report IDs must be positive integers')
        return v


class BulkRejectReportsResponse(BaseModel):
    """Schema for bulk reject reports response."""
    
    message: str = Field(..., description="Success message")
    rejected_count: int = Field(..., description="Number of reports rejected")
    rejected_ids: List[int] = Field(..., description="List of rejected report IDs")
    status: str = Field("rejected", description="New status of reports")

