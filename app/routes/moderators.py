"""
Moderator management routes.

This module contains admin-only endpoints for managing moderators and their permissions.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional

from app.database import get_db
from app.security import get_current_user_id
from app.models.user import User
from app.routes.admin import verify_admin_access
from app.services.moderator import ModeratorService
from app.schemas.moderator import (
    ModeratorResponse,
    ModeratorListResponse,
    ModeratorPermissionResponse,
    ModeratorPermissionRequest,
    AssignModeratorRequest
)

router = APIRouter()


@router.get("", response_model=ModeratorListResponse)
async def get_all_moderators(
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by email, username, first name, or last name"),
    status: Optional[str] = Query(None, description="Filter by status: 'active' or 'inactive'"),
    is_verified: Optional[bool] = Query(None, description="Filter by verified status")
):
    """
    Get all moderators with pagination, search, and filtering (Admin only).
    
    Returns a paginated list of all moderators with their permissions.
    Supports searching by email, username, first name, or last name.
    Supports filtering by active status and verification status.
    
    Args:
        current_user_id: Current authenticated user ID
        db: Database session
        page: Page number (starts from 1)
        page_size: Number of items per page
        search: Search term for email, username, first name, or last name
        status: Filter by status ('active' maps to is_active=True, 'inactive' maps to is_active=False)
        is_verified: Filter by verified status
        
    Returns:
        ModeratorListResponse: Paginated list of moderators
        
    Raises:
        HTTPException: If user is not admin
    """
    # Verify admin access
    verify_admin_access(current_user_id, db)
    
    # Get all moderators with search and filters
    service = ModeratorService(db)
    return service.get_all_moderators(
        page=page,
        page_size=page_size,
        search=search,
        status=status,
        is_verified=is_verified
    )


@router.get("/{user_id}", response_model=ModeratorResponse)
async def get_moderator_by_id(
    user_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get moderator details by ID (Admin only).
    
    Returns detailed information about a specific moderator including permissions.
    
    Args:
        user_id: Moderator user ID
        current_user_id: Current authenticated user ID
        db: Database session
        
    Returns:
        ModeratorResponse: Moderator details with permissions
        
    Raises:
        HTTPException: If user is not admin or moderator not found
    """
    # Verify admin access
    verify_admin_access(current_user_id, db)
    
    # Convert user_id to int
    try:
        user_id_int = int(user_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format. Expected integer."
        )
    
    # Get moderator
    service = ModeratorService(db)
    return service.get_moderator_by_id(user_id_int)


@router.post("/{user_id}/assign", response_model=ModeratorResponse)
async def assign_moderator_role(
    user_id: str,
    request: Optional[AssignModeratorRequest] = None,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Assign moderator role to a user (Admin only).
    
    Assigns the moderator role to a user and creates default permissions.
    Optionally allows setting custom permissions during assignment.
    
    Args:
        user_id: User ID to assign moderator role
        request: Optional permission overrides
        current_user_id: Current authenticated user ID
        db: Database session
        
    Returns:
        ModeratorResponse: New moderator with permissions
        
    Raises:
        HTTPException: If user is not admin, user not found, or user already a moderator
    """
    # Verify admin access
    verify_admin_access(current_user_id, db)
    
    # Convert user_id to int
    try:
        user_id_int = int(user_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format. Expected integer."
        )
    
    # Assign moderator role
    service = ModeratorService(db)
    return service.assign_moderator_role(
        user_id_int,
        can_see_dashboard=request.can_see_dashboard if request else None,
        can_see_users=request.can_see_users if request else None,
        can_manage_users=request.can_manage_users if request else None,
        can_see_listings=request.can_see_listings if request else None,
        can_manage_listings=request.can_manage_listings if request else None,
        can_see_spotlight_history=request.can_see_spotlight_history if request else None,
        can_spotlight=request.can_spotlight if request else None,
        can_remove_spotlight=request.can_remove_spotlight if request else None,
        can_see_flagged_content=request.can_see_flagged_content if request else None,
        can_manage_flagged_content=request.can_manage_flagged_content if request else None
    )


@router.delete("/{user_id}/remove", status_code=status.HTTP_200_OK)
async def remove_moderator_role(
    user_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Remove moderator role from a user (Admin only).
    
    Removes the moderator role from a user and deletes their permissions.
    
    Args:
        user_id: User ID to remove moderator role from
        current_user_id: Current authenticated user ID
        db: Database session
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: If user is not admin, user not found, or user not a moderator
    """
    # Verify admin access
    verify_admin_access(current_user_id, db)
    
    # Convert user_id to int
    try:
        user_id_int = int(user_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format. Expected integer."
        )
    
    # Remove moderator role
    service = ModeratorService(db)
    return service.remove_moderator_role(user_id_int)


@router.get("/{user_id}/permissions", response_model=ModeratorPermissionResponse)
async def get_moderator_permissions(
    user_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get moderator permissions (Admin only).
    
    Returns the permissions for a specific moderator.
    
    Args:
        user_id: Moderator user ID
        current_user_id: Current authenticated user ID
        db: Database session
        
    Returns:
        ModeratorPermissionResponse: Moderator permissions
        
    Raises:
        HTTPException: If user is not admin or moderator not found
    """
    # Verify admin access
    verify_admin_access(current_user_id, db)
    
    # Convert user_id to int
    try:
        user_id_int = int(user_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format. Expected integer."
        )
    
    # Get permissions
    service = ModeratorService(db)
    return service.get_moderator_permissions(user_id_int)


@router.put("/{user_id}/permissions", response_model=ModeratorPermissionResponse)
async def update_moderator_permissions(
    user_id: str,
    permissions_data: ModeratorPermissionRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Update moderator permissions (Admin only).
    
    Allows admins to update the permissions for a moderator.
    Only provided fields will be updated.
    
    Args:
        user_id: Moderator user ID
        permissions_data: Permission update data
        current_user_id: Current authenticated user ID
        db: Database session
        
    Returns:
        ModeratorPermissionResponse: Updated permissions
        
    Raises:
        HTTPException: If user is not admin, moderator not found, or permissions don't exist
    """
    # Verify admin access
    verify_admin_access(current_user_id, db)
    
    # Convert user_id to int
    try:
        user_id_int = int(user_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format. Expected integer."
        )
    
    # Update permissions
    service = ModeratorService(db)
    return service.update_moderator_permissions(user_id_int, permissions_data)

