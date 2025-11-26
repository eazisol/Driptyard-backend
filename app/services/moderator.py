"""
Moderator service for business logic operations.

This module provides moderator-related business logic including managing
moderator roles and permissions.
"""

from typing import Optional
import math
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.moderator import ModeratorPermission
from app.schemas.moderator import (
    ModeratorResponse,
    ModeratorListResponse,
    ModeratorPermissionResponse,
    ModeratorPermissionRequest
)


class ModeratorService:
    """Service class for moderator operations."""
    
    def __init__(self, db: Session):
        """
        Initialize moderator service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def get_all_moderators(
        self,
        page: int = 1,
        page_size: int = 10
    ) -> ModeratorListResponse:
        """
        Get all moderators with pagination.
        
        Args:
            page: Page number
            page_size: Items per page
            
        Returns:
            ModeratorListResponse: Paginated list of moderators
        """
        # Query moderators
        query = self.db.query(User).filter(User.is_moderator == True)
        
        # Get total count
        total = query.count()
        
        # Calculate pagination
        offset = (page - 1) * page_size
        total_pages = math.ceil(total / page_size) if total > 0 else 0
        
        # Get paginated results
        moderators = query.order_by(User.created_at.desc()).offset(offset).limit(page_size).all()
        
        # Build response
        moderator_list = []
        for moderator in moderators:
            # Get permissions
            permissions = self.db.query(ModeratorPermission).filter(
                ModeratorPermission.user_id == moderator.id
            ).first()
            
            permissions_response = None
            if permissions:
                permissions_response = ModeratorPermissionResponse(
                user_id=str(moderator.id),
                can_see_dashboard=permissions.can_see_dashboard,
                can_see_users=permissions.can_see_users,
                can_manage_users=permissions.can_manage_users,
                can_see_listings=permissions.can_see_listings,
                can_manage_listings=permissions.can_manage_listings,
                can_see_spotlight_history=permissions.can_see_spotlight_history,
                can_spotlight=permissions.can_spotlight,
                can_remove_spotlight=permissions.can_remove_spotlight,
                can_see_flagged_content=permissions.can_see_flagged_content,
                can_manage_flagged_content=permissions.can_manage_flagged_content,
                created_at=permissions.created_at,
                updated_at=permissions.updated_at
            )
            
            moderator_list.append(ModeratorResponse(
                id=str(moderator.id),
                email=moderator.email,
                username=moderator.username,
                first_name=moderator.first_name,
                last_name=moderator.last_name,
                phone=moderator.phone,
                country_code=moderator.country_code,
                is_active=moderator.is_active,
                is_verified=moderator.is_verified,
                is_moderator=moderator.is_moderator,
                avatar_url=moderator.avatar_url,
                permissions=permissions_response,
                created_at=moderator.created_at
            ))
        
        return ModeratorListResponse(
            moderators=moderator_list,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    
    def get_moderator_by_id(self, user_id: int) -> ModeratorResponse:
        """
        Get single moderator by ID with permissions.
        
        Args:
            user_id: User ID
            
        Returns:
            ModeratorResponse: Moderator details with permissions
            
        Raises:
            HTTPException: If moderator not found
        """
        # Get user
        user = self.db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if not user.is_moderator:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User is not a moderator"
            )
        
        # Get permissions
        permissions = self.db.query(ModeratorPermission).filter(
            ModeratorPermission.user_id == user_id
        ).first()
        
        permissions_response = None
        if permissions:
            permissions_response = ModeratorPermissionResponse(
                user_id=str(user.id),
                can_see_dashboard=permissions.can_see_dashboard,
                can_see_users=permissions.can_see_users,
                can_manage_users=permissions.can_manage_users,
                can_see_listings=permissions.can_see_listings,
                can_manage_listings=permissions.can_manage_listings,
                can_see_spotlight_history=permissions.can_see_spotlight_history,
                can_spotlight=permissions.can_spotlight,
                can_remove_spotlight=permissions.can_remove_spotlight,
                can_see_flagged_content=permissions.can_see_flagged_content,
                can_manage_flagged_content=permissions.can_manage_flagged_content,
                created_at=permissions.created_at,
                updated_at=permissions.updated_at
            )
        
        return ModeratorResponse(
            id=str(user.id),
            email=user.email,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            phone=user.phone,
            country_code=user.country_code,
            is_active=user.is_active,
            is_verified=user.is_verified,
            is_moderator=user.is_moderator,
            avatar_url=user.avatar_url,
            permissions=permissions_response,
            created_at=user.created_at
        )
    
    def assign_moderator_role(
        self,
        user_id: int,
        can_see_dashboard: Optional[bool] = None,
        can_see_users: Optional[bool] = None,
        can_manage_users: Optional[bool] = None,
        can_see_listings: Optional[bool] = None,
        can_manage_listings: Optional[bool] = None,
        can_see_spotlight_history: Optional[bool] = None,
        can_spotlight: Optional[bool] = None,
        can_remove_spotlight: Optional[bool] = None,
        can_see_flagged_content: Optional[bool] = None,
        can_manage_flagged_content: Optional[bool] = None
    ) -> ModeratorResponse:
        """
        Assign moderator role to a user and create default permissions.
        
        Args:
            user_id: User ID to assign moderator role
            can_spotlight: Optional override for can_spotlight (default: True)
            can_remove_spotlight: Optional override for can_remove_spotlight (default: False)
            
        Returns:
            ModeratorResponse: Updated moderator with permissions
            
        Raises:
            HTTPException: If user not found or already a moderator
        """
        # Get user
        user = self.db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if user.is_moderator:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already a moderator"
            )
        
        # Set moderator flag
        user.is_moderator = True
        
        # Create default permissions
        permissions = ModeratorPermission(
            user_id=user_id,
            can_see_dashboard=can_see_dashboard if can_see_dashboard is not None else True,
            can_see_users=can_see_users if can_see_users is not None else True,
            can_manage_users=can_manage_users if can_manage_users is not None else False,
            can_see_listings=can_see_listings if can_see_listings is not None else True,
            can_manage_listings=can_manage_listings if can_manage_listings is not None else False,
            can_see_spotlight_history=can_see_spotlight_history if can_see_spotlight_history is not None else True,
            can_spotlight=can_spotlight if can_spotlight is not None else True,
            can_remove_spotlight=can_remove_spotlight if can_remove_spotlight is not None else False,
            can_see_flagged_content=can_see_flagged_content if can_see_flagged_content is not None else True,
            can_manage_flagged_content=can_manage_flagged_content if can_manage_flagged_content is not None else False
        )
        self.db.add(permissions)
        
        # Commit changes
        self.db.commit()
        self.db.refresh(user)
        self.db.refresh(permissions)
        
        # Build response
        permissions_response = ModeratorPermissionResponse(
            user_id=str(user.id),
            can_see_dashboard=permissions.can_see_dashboard,
            can_see_users=permissions.can_see_users,
            can_manage_users=permissions.can_manage_users,
            can_see_listings=permissions.can_see_listings,
            can_manage_listings=permissions.can_manage_listings,
            can_see_spotlight_history=permissions.can_see_spotlight_history,
            can_spotlight=permissions.can_spotlight,
            can_remove_spotlight=permissions.can_remove_spotlight,
            can_see_flagged_content=permissions.can_see_flagged_content,
            can_manage_flagged_content=permissions.can_manage_flagged_content,
            created_at=permissions.created_at,
            updated_at=permissions.updated_at
        )
        
        return ModeratorResponse(
            id=str(user.id),
            email=user.email,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            phone=user.phone,
            country_code=user.country_code,
            is_active=user.is_active,
            is_verified=user.is_verified,
            is_moderator=user.is_moderator,
            avatar_url=user.avatar_url,
            permissions=permissions_response,
            created_at=user.created_at
        )
    
    def remove_moderator_role(self, user_id: int) -> dict:
        """
        Remove moderator role from a user and delete permissions.
        
        Args:
            user_id: User ID to remove moderator role from
            
        Returns:
            dict: Success message
            
        Raises:
            HTTPException: If user not found or not a moderator
        """
        # Get user
        user = self.db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if not user.is_moderator:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not a moderator"
            )
        
        # Remove moderator flag
        user.is_moderator = False
        
        # Delete permissions
        permissions = self.db.query(ModeratorPermission).filter(
            ModeratorPermission.user_id == user_id
        ).first()
        
        if permissions:
            self.db.delete(permissions)
        
        # Commit changes
        self.db.commit()
        
        return {"message": "Moderator role removed successfully"}
    
    def update_moderator_permissions(
        self,
        user_id: int,
        permissions_data: ModeratorPermissionRequest
    ) -> ModeratorPermissionResponse:
        """
        Update moderator permissions (admin only).
        
        Args:
            user_id: Moderator user ID
            permissions_data: Permission update data
            
        Returns:
            ModeratorPermissionResponse: Updated permissions
            
        Raises:
            HTTPException: If moderator not found or permissions don't exist
        """
        # Get user
        user = self.db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if not user.is_moderator:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not a moderator"
            )
        
        # Get permissions
        permissions = self.db.query(ModeratorPermission).filter(
            ModeratorPermission.user_id == user_id
        ).first()
        
        if not permissions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Moderator permissions not found"
            )
        
        # Update permissions
        update_dict = permissions_data.model_dump(exclude_unset=True)
        
        # Dashboard permissions
        if "can_see_dashboard" in update_dict:
            permissions.can_see_dashboard = update_dict["can_see_dashboard"]
        
        # Users permissions
        if "can_see_users" in update_dict:
            permissions.can_see_users = update_dict["can_see_users"]
        if "can_manage_users" in update_dict:
            permissions.can_manage_users = update_dict["can_manage_users"]
        
        # Listings permissions
        if "can_see_listings" in update_dict:
            permissions.can_see_listings = update_dict["can_see_listings"]
        if "can_manage_listings" in update_dict:
            permissions.can_manage_listings = update_dict["can_manage_listings"]
        
        # Spotlight permissions
        if "can_see_spotlight_history" in update_dict:
            permissions.can_see_spotlight_history = update_dict["can_see_spotlight_history"]
        if "can_spotlight" in update_dict:
            permissions.can_spotlight = update_dict["can_spotlight"]
        if "can_remove_spotlight" in update_dict:
            permissions.can_remove_spotlight = update_dict["can_remove_spotlight"]
        
        # Flagged content permissions
        if "can_see_flagged_content" in update_dict:
            permissions.can_see_flagged_content = update_dict["can_see_flagged_content"]
        if "can_manage_flagged_content" in update_dict:
            permissions.can_manage_flagged_content = update_dict["can_manage_flagged_content"]
        
        # Commit changes
        self.db.commit()
        self.db.refresh(permissions)
        
        return ModeratorPermissionResponse(
            user_id=str(user.id),
            can_see_dashboard=permissions.can_see_dashboard,
            can_see_users=permissions.can_see_users,
            can_manage_users=permissions.can_manage_users,
            can_see_listings=permissions.can_see_listings,
            can_manage_listings=permissions.can_manage_listings,
            can_see_spotlight_history=permissions.can_see_spotlight_history,
            can_spotlight=permissions.can_spotlight,
            can_remove_spotlight=permissions.can_remove_spotlight,
            can_see_flagged_content=permissions.can_see_flagged_content,
            can_manage_flagged_content=permissions.can_manage_flagged_content,
            created_at=permissions.created_at,
            updated_at=permissions.updated_at
        )
    
    def get_moderator_permissions(self, user_id: int) -> ModeratorPermissionResponse:
        """
        Get permissions for a moderator.
        
        Args:
            user_id: Moderator user ID
            
        Returns:
            ModeratorPermissionResponse: Moderator permissions
            
        Raises:
            HTTPException: If moderator not found or permissions don't exist
        """
        # Get user
        user = self.db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if not user.is_moderator:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not a moderator"
            )
        
        # Get permissions
        permissions = self.db.query(ModeratorPermission).filter(
            ModeratorPermission.user_id == user_id
        ).first()
        
        if not permissions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Moderator permissions not found"
            )
        
        return ModeratorPermissionResponse(
            user_id=str(user.id),
            can_see_dashboard=permissions.can_see_dashboard,
            can_see_users=permissions.can_see_users,
            can_manage_users=permissions.can_manage_users,
            can_see_listings=permissions.can_see_listings,
            can_manage_listings=permissions.can_manage_listings,
            can_see_spotlight_history=permissions.can_see_spotlight_history,
            can_spotlight=permissions.can_spotlight,
            can_remove_spotlight=permissions.can_remove_spotlight,
            can_see_flagged_content=permissions.can_see_flagged_content,
            can_manage_flagged_content=permissions.can_manage_flagged_content,
            created_at=permissions.created_at,
            updated_at=permissions.updated_at
        )

