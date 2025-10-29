"""
User management routes.

This module contains user profile management endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.security import get_current_user_id
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate
from app.services.s3 import get_s3_service

router = APIRouter()


@router.get("/me", response_model=UserResponse)
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
        UserResponse: Current user information
        
    Raises:
        HTTPException: If user not found
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
        "company_name": user.company_name,
        "sin_number": user.sin_number,
        "created_at": user.created_at,
        "updated_at": user.updated_at
    }


@router.put("/me", response_model=UserResponse)
async def update_user_profile(
    user_update: UserUpdate,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Update user profile with JSON data.
    
    Send as JSON (application/json).
    All fields are optional - only send what you want to update.
    
    For avatar uploads, use POST /users/me/avatar endpoint.
    
    Frontend example:
        fetch('/users/me', {
            method: 'PUT',
            headers: { 
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                first_name: 'Rehan',
                last_name: 'Khan',
                bio: 'test'
            })
        });
    
    Args:
        user_update: User update data (JSON)
        current_user_id: Current authenticated user ID
        db: Database session
        
    Returns:
        UserResponse: Updated user information
        
    Raises:
        HTTPException: If validation fails
    """
    # Get user
    user = db.query(User).filter(User.id == current_user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get update data (only fields that were provided)
    update_data = user_update.model_dump(exclude_unset=True)
    
    # Validate username if being updated
    if 'username' in update_data:
        username = update_data['username']
        
        if username:
            username = username.strip()
            
            # Validate format
            if not username.replace('_', '').replace('-', '').isalnum():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username can only contain letters, numbers, underscores, and hyphens"
                )
            
            # Check if username is taken by another user
            if username.lower() != user.username.lower():
                existing = db.query(User).filter(User.username == username.lower()).first()
                if existing:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Username is already taken"
                    )
            
            update_data['username'] = username.lower()
    
    # Update user fields
    for field, value in update_data.items():
        if isinstance(value, str):
            value = value.strip() if value.strip() else None
        setattr(user, field, value)
    
    # Commit changes
    try:
        db.commit()
        db.refresh(user)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user profile: {str(e)}"
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
        "company_name": user.company_name,
        "sin_number": user.sin_number,
        "created_at": user.created_at,
        "updated_at": user.updated_at
    }


@router.post("/me/avatar", response_model=UserResponse)
async def upload_avatar(
    avatar: UploadFile = File(...),
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Upload user avatar image.
    
    Send as multipart/form-data with avatar file.
    Supported formats: JPG, JPEG, PNG, GIF, WEBP
    
    Frontend example:
        const formData = new FormData();
        formData.append('avatar', avatarFile);
        
        fetch('/users/me/avatar', {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` },
            body: formData
        });
    
    Args:
        avatar: Avatar image file
        current_user_id: Current authenticated user ID
        db: Database session
        
    Returns:
        UserResponse: Updated user information with new avatar
        
    Raises:
        HTTPException: If upload fails or invalid file type
    """
    # Get user
    user = db.query(User).filter(User.id == current_user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Validate file type
    allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
    
    if not avatar.content_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not determine file type"
        )
    
    if avatar.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: JPG, JPEG, PNG, GIF, WEBP. Got: {avatar.content_type}"
        )
    
    # Validate file extension
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    file_ext = avatar.filename.lower().split('.')[-1] if '.' in avatar.filename else ''
    
    if f'.{file_ext}' not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file extension. Allowed: {', '.join(allowed_extensions)}"
        )
    
    try:
        # Upload to S3
        s3_service = get_s3_service()
        result = s3_service.upload_file(avatar, "avatars", current_user_id)
        user.avatar_url = result["url"]
        
        db.commit()
        db.refresh(user)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload avatar: {str(e)}"
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
        "company_name": user.company_name,
        "sin_number": user.sin_number,
        "created_at": user.created_at,
        "updated_at": user.updated_at
    }

