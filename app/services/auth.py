"""
Authentication service for user operations.

This module provides authentication business logic including registration,
email verification, and user management.
"""

import random
import string
from datetime import datetime, timedelta
from typing import Any, Dict
from sqlalchemy.orm import Session
from sqlalchemy import and_
from fastapi import HTTPException, status

from app.database import settings
from app.security import get_password_hash, create_token_response
from app.services.email import email_service
from app.models.user import User, EmailVerification, RegistrationData


class AuthService:
    """Service class for authentication operations."""
    
    def __init__(self, db: Session):
        """
        Initialize authentication service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    async def register_user(self, user_data) -> Dict[str, Any]:
        """
        Register a new user and send verification email.
        
        Args:
            user_data: User registration data
            
        Returns:
            Dict[str, Any]: Registration confirmation with verification details
            
        Raises:
            HTTPException: If registration fails
        """
        try:
            # Check if user already exists
            existing_user = self.db.query(User).filter(
                (User.email == user_data.email) | (User.username == user_data.username) | (User.phone == user_data.phone)
            ).first()
            
            if existing_user:
                if existing_user.email == user_data.email:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Email already registered"
                    )
                elif existing_user.phone == user_data.phone:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Phone number already registered"
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Username already taken"
                    )
            
            # Generate verification code
            verification_code = self._generate_verification_code()
            
            # Create email verification record
            email_verification = EmailVerification.create_verification(
                email=user_data.email,
                code=verification_code,
                expiry_minutes=settings.VERIFICATION_CODE_EXPIRY_MINUTES
            )
            
            # Hash password with proper error handling
            try:
                hashed_password = get_password_hash(user_data.password)
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Password hashing failed: {str(e)}"
                )
            
            # Store registration data temporarily
            registration_data = RegistrationData(
                email=user_data.email,
                username=user_data.username,
                hashed_password=hashed_password,
                phone=user_data.phone,
                country_code=user_data.country_code,
                company_name=user_data.company_name,
                sin_number=user_data.sin_number
            )
            
            # Store verification record and registration data
            self.db.add(email_verification)
            self.db.add(registration_data)
            self.db.commit()
            
            # Send verification email
            email_sent = email_service.send_verification_email(
                user_data.email, 
                verification_code
            )
            
            if not email_sent:
                # Email failed but keep the registration (useful for development/testing)
                # In production, you might want to be stricter
                print(f"⚠️  WARNING: Failed to send verification email to {user_data.email}")
                print(f"   Verification code: {verification_code}")
                # Don't roll back - allow registration to proceed for testing
            
            return {
                "message": "Registration successful. Please check your email for verification code.",
                "email": user_data.email,
                "expires_in": settings.VERIFICATION_CODE_EXPIRY_MINUTES * 60
            }
        except HTTPException:
            # Re-raise HTTP exceptions as-is
            raise
        except Exception as e:
            # Catch any other unexpected errors and return a user-friendly message
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Registration failed: {str(e)}"
            )
    
    async def verify_email(self, verification_data) -> Dict[str, Any]:
        """
        Verify email and create user account.
        
        Args:
            verification_data: Email and verification code
            
        Returns:
            Dict[str, Any]: Access token and user information
            
        Raises:
            HTTPException: If verification fails
        """
        # Find verification record
        verification = self.db.query(EmailVerification).filter(
            and_(
                EmailVerification.email == verification_data.email,
                EmailVerification.verification_code == verification_data.verification_code,
                EmailVerification.is_used == False
            )
        ).first()
        
        if not verification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid verification code"
            )
        
        # Check if code is expired
        if verification.is_expired():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification code has expired"
            )
        
        # Check if user already exists (in case of duplicate verification attempts)
        existing_user = self.db.query(User).filter(User.email == verification_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User already exists"
            )
        
        # Get registration data
        registration_data = self.db.query(RegistrationData).filter(
            RegistrationData.email == verification_data.email
        ).first()
        
        if not registration_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Registration data not found"
            )
        
        # Create user account
        user = User(
            email=registration_data.email,
            username=registration_data.username,
            hashed_password=registration_data.hashed_password,
            phone=registration_data.phone,
            country_code=registration_data.country_code,
            company_name=registration_data.company_name,
            sin_number=registration_data.sin_number,
            is_verified=True,
            is_active=True
        )
        
        # Save user and mark verification as used
        self.db.add(user)
        verification.is_used = True
        
        # Clean up registration data
        self.db.delete(registration_data)
        self.db.commit()
        
        # Generate JWT token
        token_response = create_token_response(str(user.id))
        
        # Create user response
        user_response = {
            "id": str(user.id),  # Convert integer ID to string for schema validation
            "email": user.email,
            "username": user.username,
            "phone": user.phone,
            "country_code": user.country_code,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "is_admin": user.is_admin,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "bio": user.bio,
            "avatar_url": user.avatar_url,
            "company_name": user.company_name,
            "sin_number": user.sin_number,
            "created_at": user.created_at,
            "updated_at": user.updated_at
        }
        
        return {
            "access_token": token_response["access_token"],
            "token_type": token_response["token_type"],
            "expires_in": token_response["expires_in"],
            "user": user_response
        }
    
    async def resend_verification(self, email: str) -> Dict[str, str]:
        """
        Resend verification code.
        
        Args:
            email: User email address
            
        Returns:
            Dict[str, str]: Success message
            
        Raises:
            HTTPException: If resend fails
        """
        # Find existing verification record
        verification = self.db.query(EmailVerification).filter(
            and_(
                EmailVerification.email == email,
                EmailVerification.is_used == False
            )
        ).first()
        
        if not verification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No pending verification found for this email"
            )
        
        # Check if previous code is still valid (not expired)
        if not verification.is_expired():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Previous verification code is still valid. Please wait before requesting a new one."
            )
        
        # Generate new verification code
        new_code = self._generate_verification_code()
        
        # Update verification record
        verification.verification_code = new_code
        verification.expires_at = datetime.utcnow() + timedelta(
            minutes=settings.VERIFICATION_CODE_EXPIRY_MINUTES
        )
        verification.is_used = False
        
        self.db.commit()
        
        # Send new verification email
        email_sent = email_service.send_verification_email(email, new_code)
        
        if not email_sent:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send verification email"
            )
        
        return {"message": "Verification code resent successfully"}
    
    def _generate_verification_code(self) -> str:
        """
        Generate a 6-digit verification code.
        
        Returns:
            str: 6-digit verification code
        """
        return ''.join(random.choices(string.digits, k=6))
