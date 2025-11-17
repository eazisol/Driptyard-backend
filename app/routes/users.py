"""
User management routes.

This module contains user profile management endpoints.
"""

from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session

from app.database import get_db
from app.security import get_current_user_id
from app.schemas.user import UserResponse, UserUpdate
from app.services.user import UserService

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
    service = UserService(db)
    return service.get_current_user(current_user_id)


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
    service = UserService(db)
    return service.update_user_profile(current_user_id, user_update)


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
    service = UserService(db)
    return service.upload_avatar(current_user_id, avatar)
