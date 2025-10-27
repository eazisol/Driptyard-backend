"""
Authentication-related Pydantic schemas.

This module contains all authentication-related request and response schemas.
"""

import re
from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.base import BaseCreateSchema
from app.schemas.user import UserResponse


class UserLogin(BaseCreateSchema):
    """Schema for user login."""
    
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="Password")


class ResendVerificationRequest(BaseCreateSchema):
    """Schema for resend verification request."""
    
    email: EmailStr = Field(..., description="User email address")


class UserRegister(BaseCreateSchema):
    """Schema for user registration."""
    
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, max_length=100, description="Password")
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    phone: str = Field(..., description="Phone number with country code")
    country_code: str = Field(..., min_length=2, max_length=3, description="Country code")
    
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


class EmailVerificationRequest(BaseCreateSchema):
    """Schema for email verification request."""
    
    email: EmailStr = Field(..., description="User email address")
    verification_code: str = Field(..., min_length=6, max_length=6, description="6-digit verification code")
    
    @field_validator('verification_code')
    @classmethod
    def validate_verification_code(cls, v):
        """Validate verification code format."""
        if not v.isdigit():
            raise ValueError('Verification code must contain only digits')
        return v


class RegistrationResponse(BaseModel):
    """Schema for registration response."""
    
    message: str = Field(..., description="Success message")
    email: str = Field(..., description="User email address")
    expires_in: int = Field(..., description="Verification code expiry time in seconds")


class TokenResponse(BaseModel):
    """Schema for authentication token response."""
    
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    user: UserResponse = Field(..., description="User information")


class PasswordResetRequest(BaseCreateSchema):
    """Schema for password reset request."""
    
    email: EmailStr = Field(..., description="User email address")


class PasswordResetVerify(BaseCreateSchema):
    """Schema for password reset verification."""
    
    email: EmailStr = Field(..., description="User email address")
    reset_token: str = Field(..., min_length=6, max_length=6, description="6-digit reset token")
    new_password: str = Field(..., min_length=8, max_length=100, description="New password")
    
    @field_validator('reset_token')
    @classmethod
    def validate_reset_token(cls, v):
        """Validate reset token format."""
        if not v.isdigit():
            raise ValueError('Reset token must contain only digits')
        return v
    
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


class PasswordResetResponse(BaseModel):
    """Schema for password reset response."""
    
    message: str = Field(..., description="Success message")
    email: str = Field(..., description="User email address")
    expires_in: int = Field(..., description="Reset token expiry time in seconds")
