"""
User-related Pydantic schemas.

This module contains all user-related request and response schemas.
"""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.base import BaseCreateSchema, BaseUpdateSchema, BaseResponseSchema


class UserBaseSchema(BaseCreateSchema):
    """Base user schema with common fields."""
    
    email: EmailStr = Field(..., description="User email address")
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    first_name: Optional[str] = Field(None, max_length=100, description="First name")
    last_name: Optional[str] = Field(None, max_length=100, description="Last name")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    bio: Optional[str] = Field(None, max_length=500, description="User bio")
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        """Validate username format."""
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username can only contain letters, numbers, underscores, and hyphens')
        return v.lower()


class UserCreate(UserBaseSchema):
    """Schema for user registration."""
    
    password: str = Field(..., min_length=8, max_length=100, description="Password")
    confirm_password: str = Field(..., description="Password confirmation")
    
    @field_validator('confirm_password')
    @classmethod
    def passwords_match(cls, v, info):
        """Validate that passwords match."""
        if hasattr(info, 'data') and 'password' in info.data and v != info.data['password']:
            raise ValueError('Passwords do not match')
        return v


class UserUpdate(BaseUpdateSchema):
    """Schema for user profile updates."""
    
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="Username")
    first_name: Optional[str] = Field(None, max_length=100, description="First name")
    last_name: Optional[str] = Field(None, max_length=100, description="Last name")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    country_code: Optional[str] = Field(None, min_length=2, max_length=3, description="Country code")
    bio: Optional[str] = Field(None, max_length=500, description="User bio")
    avatar_url: Optional[str] = Field(None, max_length=500, description="Avatar URL")
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        """Validate username format."""
        if v is None:
            return v
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username can only contain letters, numbers, underscores, and hyphens')
        return v.lower()


class UserResponse(BaseResponseSchema):
    """Schema for user response data."""
    
    email: str = Field(..., description="User email address")
    username: str = Field(..., description="Username")
    first_name: Optional[str] = Field(None, description="First name")
    last_name: Optional[str] = Field(None, description="Last name")
    phone: Optional[str] = Field(None, description="Phone number")
    bio: Optional[str] = Field(None, description="User bio")
    avatar_url: Optional[str] = Field(None, description="Avatar URL")
    company_name: Optional[str] = Field(None, description="Company name")
    sin_number: Optional[str] = Field(None, description="Social Insurance Number")
    is_active: bool = Field(..., description="Whether user is active")
    is_verified: bool = Field(..., description="Whether user is verified")
    is_admin: bool = Field(..., description="Whether user is an admin")
    is_moderator: bool = Field(..., description="Whether user is a moderator")


class UserPublicResponse(BaseResponseSchema):
    """Schema for public user data (limited information)."""
    
    username: str = Field(..., description="Username")
    first_name: Optional[str] = Field(None, description="First name")
    last_name: Optional[str] = Field(None, description="Last name")
    bio: Optional[str] = Field(None, description="User bio")
    avatar_url: Optional[str] = Field(None, description="Avatar URL")
