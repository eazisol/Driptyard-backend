"""
Authentication API endpoints.

This module contains all authentication-related endpoints including
user registration, login, logout, and token management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.auth import AuthService
from app.security import get_current_user_id, verify_password, create_token_response
from app.models.user import User
from app.schemas.auth import UserLogin
from app.schemas.auth import (
    UserRegister, EmailVerificationRequest, RegistrationResponse, TokenResponse, ResendVerificationRequest
)

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
            detail="Account is deactivated"
        )
    
    # Verify password
    if not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Generate JWT token
    token_response = create_token_response(str(user.id))
    
    # Create user response
    user_response = {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "phone": user.phone,
        "country_code": user.country_code,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "bio": user.bio,
        "avatar_url": user.avatar_url,
        "created_at": user.created_at,
        "updated_at": user.updated_at
    }
    
    return {
        "access_token": token_response["access_token"],
        "token_type": token_response["token_type"],
        "expires_in": token_response["expires_in"],
        "user": user_response
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


@router.get("/me", response_model=dict)
async def get_current_user(
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get current user profile.
    
    Args:
        current_user_id: Current authenticated user ID
        db: Database session
        
    Returns:
        dict: Current user information
    """
    user = db.query(User).filter(User.id == current_user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "phone": user.phone,
        "country_code": user.country_code,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "bio": user.bio,
        "avatar_url": user.avatar_url,
        "created_at": user.created_at,
        "updated_at": user.updated_at
    }


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
    user = db.query(User).filter(User.id == current_user_id).first()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Generate new JWT token
    token_response = create_token_response(str(user.id))
    
    # Create user response
    user_response = {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "phone": user.phone,
        "country_code": user.country_code,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "bio": user.bio,
        "avatar_url": user.avatar_url,
        "created_at": user.created_at,
        "updated_at": user.updated_at
    }
    
    return {
        "access_token": token_response["access_token"],
        "token_type": token_response["token_type"],
        "expires_in": token_response["expires_in"],
        "user": user_response
    }
