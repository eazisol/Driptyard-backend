"""
User-related database models.

This module contains User, EmailVerification, and RegistrationData models.
"""

from datetime import datetime, timedelta
from sqlalchemy import Column, String, Boolean, Text, DateTime, Index
from sqlalchemy.dialects.postgresql import JSON

from app.models.base import UserProductBaseModel


class User(UserProductBaseModel):
    """User model for storing user information."""
    
    __tablename__ = "users"
    
    # Basic user information
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    country_code = Column(String(3), nullable=True)
    company_name = Column(String(200), nullable=True)
    sin_number = Column(String(20), nullable=True)
    
    # User status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    is_moderator = Column(Boolean, default=False, nullable=False)
    
    # Profile information
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    bio = Column(Text, nullable=True)
    avatar_url = Column(String(500), nullable=True)
    
    # Relationships
    # products = relationship("Product", back_populates="owner")
    # orders_as_buyer = relationship("Order", foreign_keys="Order.buyer_id", back_populates="buyer")
    # orders_as_seller = relationship("Order", foreign_keys="Order.seller_id", back_populates="seller")
    # conversations = relationship("Conversation", back_populates="participants")


class EmailVerification(UserProductBaseModel):
    """Email verification model for storing verification codes."""
    
    __tablename__ = "email_verifications"
    
    # Email and verification details
    email = Column(String(255), nullable=False, index=True)
    verification_code = Column(String(6), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)
    
    # Create composite index for efficient lookups
    __table_args__ = (
        Index('idx_email_code', 'email', 'verification_code'),
        Index('idx_email_active', 'email', 'is_used'),
    )
    
    def is_expired(self) -> bool:
        """Check if the verification code is expired."""
        return datetime.utcnow() > self.expires_at
    
    def is_valid(self) -> bool:
        """Check if the verification code is valid (not expired and not used)."""
        return not self.is_expired() and not self.is_used
    
    @classmethod
    def create_verification(cls, email: str, code: str, expiry_minutes: int = 15) -> 'EmailVerification':
        """Create a new email verification record."""
        return cls(
            email=email,
            verification_code=code,
            expires_at=datetime.utcnow() + timedelta(minutes=expiry_minutes)
        )


class RegistrationData(UserProductBaseModel):
    """Registration data model for temporary storage during verification."""
    
    __tablename__ = "registration_data"
    
    # Email and verification details
    email = Column(String(255), nullable=False, index=True)
    username = Column(String(50), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    country_code = Column(String(3), nullable=True)
    company_name = Column(String(200), nullable=True)
    sin_number = Column(String(20), nullable=True)
    
    # Store additional data as JSON
    additional_data = Column(JSON, nullable=True)


class PasswordResetToken(UserProductBaseModel):
    """Password reset token model for password recovery."""
    
    __tablename__ = "password_reset_tokens"
    
    # Email and reset details
    email = Column(String(255), nullable=False, index=True)
    reset_token = Column(String(6), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)
    
    # Create composite index for efficient lookups
    __table_args__ = (
        Index('idx_email_reset_token', 'email', 'reset_token'),
        Index('idx_email_reset_active', 'email', 'is_used'),
    )
    
    def is_expired(self) -> bool:
        """Check if the reset token is expired."""
        return datetime.utcnow() > self.expires_at
    
    def is_valid(self) -> bool:
        """Check if the reset token is valid (not expired and not used)."""
        return not self.is_expired() and not self.is_used
    
    @classmethod
    def create_reset_token(cls, email: str, token: str, expiry_minutes: int = 15) -> 'PasswordResetToken':
        """Create a new password reset token record."""
        return cls(
            email=email,
            reset_token=token,
            expires_at=datetime.utcnow() + timedelta(minutes=expiry_minutes)
        )