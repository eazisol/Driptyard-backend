"""
User service for business logic operations.

This module provides user-related business logic including profile management,
validation, and data transformations.
"""

from typing import Dict
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate
from app.services.s3 import get_s3_service


class UserService:
    """Service class for user operations."""
    
    def __init__(self, db: Session):
        """
        Initialize user service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def _user_to_response(self, user: User) -> Dict:
        """Convert User model to UserResponse dictionary."""
        return {
            "id": str(user.id),  # Convert integer ID to string for schema validation
            "email": user.email,
            "username": user.username,
            "phone": user.phone,
            "country_code": user.country_code,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "is_admin": user.is_admin,
            "is_moderator": user.is_moderator,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "bio": user.bio,
            "avatar_url": user.avatar_url,
            "company_name": user.company_name,
            "sin_number": user.sin_number,
            "created_at": user.created_at,
            "updated_at": user.updated_at
        }
    
    def get_current_user(self, user_id: str) -> Dict:
        """
        Get current user profile.
        
        Args:
            user_id: User ID string (integer as string)
            
        Returns:
            Dict: User information as UserResponse dictionary
            
        Raises:
            HTTPException: If user not found
        """
        try:
            user_id_int = int(user_id)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user identifier"
            )
        
        user = self.db.query(User).filter(User.id == user_id_int).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return self._user_to_response(user)
    
    def update_user_profile(self, user_id: str, user_update: UserUpdate) -> Dict:
        """
        Update user profile with JSON data.
        
        Args:
            user_id: User ID string (integer as string)
            user_update: User update data
            
        Returns:
            Dict: Updated user information as UserResponse dictionary
            
        Raises:
            HTTPException: If user not found or validation fails
        """
        try:
            user_id_int = int(user_id)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user identifier"
            )
        
        user = self.db.query(User).filter(User.id == user_id_int).first()
        
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
                    existing = self.db.query(User).filter(User.username == username.lower()).first()
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
            self.db.commit()
            self.db.refresh(user)
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update user profile: {str(e)}"
            )
        
        return self._user_to_response(user)
    
    def upload_avatar(self, user_id: str, avatar: UploadFile) -> Dict:
        """
        Upload user avatar image.
        
        Args:
            user_id: User ID string (integer as string)
            avatar: Avatar image file
            
        Returns:
            Dict: Updated user information as UserResponse dictionary
            
        Raises:
            HTTPException: If user not found, upload fails, or invalid file type
        """
        try:
            user_id_int = int(user_id)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user identifier"
            )
        
        user = self.db.query(User).filter(User.id == user_id_int).first()
        
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
            result = s3_service.upload_file(avatar, "avatars", user_id)
            user.avatar_url = result["url"]
            
            self.db.commit()
            self.db.refresh(user)
            
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload avatar: {str(e)}"
            )
        
        return self._user_to_response(user)

