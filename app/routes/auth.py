"""
Authentication API endpoints.

This module contains all authentication-related endpoints including
user registration, login, logout, and token management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.auth import AuthService
from app.security import get_current_user_id, verify_password, create_token_response, get_password_hash
from app.models.user import User, PasswordResetToken
from app.models.moderator import ModeratorPermission
from app.schemas.auth import UserLogin
from app.schemas.auth import (
    UserRegister, EmailVerificationRequest, RegistrationResponse, TokenResponse, ResendVerificationRequest,
    PasswordResetRequest, PasswordResetVerify, PasswordResetResponse, UserPermissionsResponse
)
from app.services.email import email_service
import secrets
from datetime import datetime, timedelta

router = APIRouter()


@router.post("/register", response_model=RegistrationResponse, status_code=status.HTTP_202_ACCEPTED)
async def register(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    """
    Register a new user and send verification email.
    
    Args:
        user_data: User registration data
        db: Database session
        
    Returns:
        RegistrationResponse: Registration confirmation with verification details
        
    Raises:
        HTTPException: If registration fails
    """
    auth_service = AuthService(db)
    return await auth_service.register_user(user_data)


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return access token.
    
    Args:
        credentials: User login credentials
        db: Database session
        
    Returns:
        TokenResponse: Access token and user info
        
    Raises:
        HTTPException: If authentication fails
    """
    # Find user by email
    user = db.query(User).filter(User.email == credentials.email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is suspended or inactive. Please contact support."
        )
    
    # Check if user is suspended
    if hasattr(user, 'is_suspended') and user.is_suspended:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is suspended. Please contact support for assistance."
        )
    
    # Verify password
    if not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Update last_login timestamp
    from datetime import datetime
    if hasattr(user, 'last_login'):
        user.last_login = datetime.utcnow()
        db.commit()
        db.refresh(user)
    
    # Generate JWT token
    token_response = create_token_response(str(user.id))
    
    # Get permissions
    permissions = None
    if user.is_admin:
        # Admin has all permissions
        permissions = UserPermissionsResponse(
            can_see_dashboard=True,
            can_see_users=True,
            can_manage_users=True,
            can_see_listings=True,
            can_manage_listings=True,
            can_see_spotlight_history=True,
            can_spotlight=True,
            can_remove_spotlight=True,
            can_see_flagged_content=True,
            can_manage_flagged_content=True
        )
    elif user.is_moderator:
        # Get moderator permissions from database
        moderator_permissions = db.query(ModeratorPermission).filter(
            ModeratorPermission.user_id == user.id
        ).first()
        
        if moderator_permissions:
            permissions = UserPermissionsResponse(
                can_see_dashboard=moderator_permissions.can_see_dashboard,
                can_see_users=moderator_permissions.can_see_users,
                can_manage_users=moderator_permissions.can_manage_users,
                can_see_listings=moderator_permissions.can_see_listings,
                can_manage_listings=moderator_permissions.can_manage_listings,
                can_see_spotlight_history=moderator_permissions.can_see_spotlight_history,
                can_spotlight=moderator_permissions.can_spotlight,
                can_remove_spotlight=moderator_permissions.can_remove_spotlight,
                can_see_flagged_content=moderator_permissions.can_see_flagged_content,
                can_manage_flagged_content=moderator_permissions.can_manage_flagged_content
            )
        else:
            # If no permissions record exists, return all False
            permissions = UserPermissionsResponse(
                can_see_dashboard=False,
                can_see_users=False,
                can_manage_users=False,
                can_see_listings=False,
                can_manage_listings=False,
                can_see_spotlight_history=False,
                can_spotlight=False,
                can_remove_spotlight=False,
                can_see_flagged_content=False,
                can_manage_flagged_content=False
            )
    
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
        "updated_at": user.updated_at,
        "is_moderator": user.is_moderator
    }
    
    return {
        "access_token": token_response["access_token"],
        "token_type": token_response["token_type"],
        "expires_in": token_response["expires_in"],
        "user": user_response,
        "permissions": permissions.model_dump() if permissions else None
    }


@router.post("/logout")
async def logout(
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Logout current user (invalidate token).
    
    Args:
        current_user_id: Current authenticated user ID
        
    Returns:
        dict: Success message
    """
    # TODO: Implement token invalidation logic
    return {"message": "Logout successful"}


@router.post("/verify-email", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def verify_email(
    verification_data: EmailVerificationRequest,
    db: Session = Depends(get_db)
):
    """
    Verify email and create user account.
    
    Args:
        verification_data: Email and verification code
        db: Database session
        
    Returns:
        TokenResponse: Access token and user information
        
    Raises:
        HTTPException: If verification fails
    """
    auth_service = AuthService(db)
    return await auth_service.verify_email(verification_data)


@router.post("/resend-verification", response_model=dict, status_code=status.HTTP_200_OK)
async def resend_verification(
    request: ResendVerificationRequest,
    db: Session = Depends(get_db)
):
    """
    Resend verification code.
    
    Args:
        request: Request body containing email
        db: Database session
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: If resend fails
    """
    auth_service = AuthService(db)
    return await auth_service.resend_verification(request.email)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Refresh access token.
    
    Args:
        current_user_id: Current authenticated user ID
        db: Database session
        
    Returns:
        TokenResponse: New access token
        
    Raises:
        HTTPException: If token refresh fails
    """
    try:
        user_id_int = int(current_user_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user identifier"
        )
    
    user = db.query(User).filter(User.id == user_id_int).first()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Generate new JWT token
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
        "updated_at": user.updated_at,
        "is_moderator": user.is_moderator
    }
    
    return {
        "access_token": token_response["access_token"],
        "token_type": token_response["token_type"],
        "expires_in": token_response["expires_in"],
        "user": user_response
    }


@router.post("/password-reset/request", response_model=PasswordResetResponse, status_code=status.HTTP_200_OK)
async def request_password_reset(
    request: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """
    Request password reset link/code.
    
    Args:
        request: Password reset request with email
        db: Database session
        
    Returns:
        PasswordResetResponse: Success message with expiry info
        
    Raises:
        HTTPException: If request fails
    """
    # Check if user exists
    user = db.query(User).filter(User.email == request.email).first()
    
    if not user:
        # Return success even if user doesn't exist (security best practice)
        return {
            "message": "If an account with that email exists, a password reset code has been sent",
            "email": request.email,
            "expires_in": 900  # 15 minutes
        }
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is deactivated. Please contact support."
        )
    
    # Invalidate any existing unused reset tokens for this email
    db.query(PasswordResetToken).filter(
        PasswordResetToken.email == request.email,
        PasswordResetToken.is_used == False
    ).update({"is_used": True})
    db.commit()
    
    # Generate 6-digit reset token
    reset_token = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
    
    # Create new reset token record
    expiry_minutes = 15
    token_record = PasswordResetToken.create_reset_token(
        email=request.email,
        token=reset_token,
        expiry_minutes=expiry_minutes
    )
    
    db.add(token_record)
    db.commit()
    
    # Send reset email
    email_sent = email_service.send_password_reset_email(request.email, reset_token)
    
    if not email_sent:
        # Don't fail the request if email fails, but log it
        print(f"Warning: Failed to send password reset email to {request.email}")
    
    return {
        "message": "If an account with that email exists, a password reset code has been sent",
        "email": request.email,
        "expires_in": expiry_minutes * 60  # Convert to seconds
    }


@router.post("/password-reset/verify", response_model=dict, status_code=status.HTTP_200_OK)
async def verify_password_reset(
    request: PasswordResetVerify,
    db: Session = Depends(get_db)
):
    """
    Verify reset token and update password.
    For admin users: verify current password instead of reset token.
    
    Args:
        request: Reset verification with email, token, and new password
        db: Database session
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: If verification or password update fails
    """
    try:
        # Special handling for admin users
        if request.is_admin:
            # Find admin user by email
            user = db.query(User).filter(
                User.email == request.email,
                User.is_admin == True
            ).first()

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Admin user not found"
                )

            # Check if user is active
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Account is suspended or inactive. Please contact support."
                )

            # Verify current password
            if not request.current_password:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Current password is required for admin password reset"
                )

            if not verify_password(request.current_password, user.hashed_password):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Current password is incorrect"
                )

            # Update password directly (no token needed)
            user.hashed_password = get_password_hash(request.new_password)
            user.updated_at = datetime.utcnow()
            db.commit()

            return {
                "message": "Password has been updated successfully. You can now login with your new password."
            }

        # Normal flow for non-admin users
        # Validate reset token is provided
        if not request.reset_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reset token is required for password reset"
            )

        # Find the reset token
        token_record = db.query(PasswordResetToken).filter(
            PasswordResetToken.email == request.email,
            PasswordResetToken.reset_token == request.reset_token,
            PasswordResetToken.is_used == False
        ).first()

        if not token_record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )

        # Check if token is expired
        if token_record.is_expired():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reset token has expired. Please request a new one."
            )

        # Find the user
        user = db.query(User).filter(User.email == request.email).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Update user's password
        user.hashed_password = get_password_hash(request.new_password)
        user.updated_at = datetime.utcnow()

        # Mark token as used
        token_record.is_used = True

        db.commit()

        return {
            "message": "Password has been reset successfully. You can now login with your new password."
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while resetting the password."
        )
