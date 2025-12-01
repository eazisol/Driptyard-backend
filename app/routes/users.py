"""
User management routes.

This module contains user profile management endpoints.
"""

from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.security import get_current_user_id
from app.schemas.user import UserResponse, UserUpdate
from app.schemas.follow import (
    FollowedSellersListResponse,
    FollowedProductsListResponse
)
from app.services.user import UserService
from app.services.follow import FollowService

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


@router.get("/{user_id}/followed-sellers", response_model=FollowedSellersListResponse)
async def get_user_followed_sellers(
    user_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(12, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    Get list of sellers that a particular user follows (public endpoint).
    
    Args:
        user_id: ID of the user
        page: Page number (starts from 1)
        page_size: Number of items per page
        db: Database session
        
    Returns:
        FollowedSellersListResponse: Paginated list of followed sellers
        
    Raises:
        HTTPException: If user not found
    """
    try:
        uid = int(user_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    service = FollowService(db)
    return service.get_user_followed_sellers(uid, page, page_size)


@router.get("/{user_id}/followed-products", response_model=FollowedProductsListResponse)
async def get_user_followed_products(
    user_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(12, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    Get list of products that a particular user follows (public endpoint).
    
    Args:
        user_id: ID of the user
        page: Page number (starts from 1)
        page_size: Number of items per page
        db: Database session
        
    Returns:
        FollowedProductsListResponse: Paginated list of followed products
        
    Raises:
        HTTPException: If user not found
    """
    try:
        uid = int(user_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    service = FollowService(db)
    return service.get_user_followed_products(uid, page, page_size)
