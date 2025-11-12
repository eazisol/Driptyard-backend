"""
Admin management routes.

This module contains admin-only endpoints for managing the platform.
"""

from datetime import datetime, timedelta
from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
import math

from app.database import get_db
from app.security import get_current_user_id
from app.models.user import User
from app.models.product import Product
from app.schemas.admin import (
    StatsOverviewResponse,
    AdminProductResponse,
    AdminProductListResponse,
    AdminProductUpdateRequest,
    AdminUserResponse,
    AdminUserListResponse,
    AdminUserUpdateRequest
)

router = APIRouter()


def verify_admin_access(current_user_id: str, db: Session) -> User:
    """
    Verify that the current user is an admin.
    
    Args:
        current_user_id: Current authenticated user ID
        db: Database session
        
    Returns:
        User: The admin user object
        
    Raises:
        HTTPException: If user is not found or not admin
    """
    try:
        user_uuid = UUID(current_user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user identifier"
        )
    
    user = db.query(User).filter(User.id == user_uuid).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return user


def calculate_percentage_change(current: float, previous: float) -> float:
    """
    Calculate percentage change between two values.
    
    Args:
        current: Current period value
        previous: Previous period value
        
    Returns:
        float: Percentage change (can be negative)
    """
    if previous == 0:
        return 100.0 if current > 0 else 0.0
    return ((current - previous) / previous) * 100.0


@router.get("/stats/overview", response_model=StatsOverviewResponse)
async def get_stats_overview(
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get summary statistics for dashboard cards.
    
    Returns overview statistics including users, products (listings),
    and various change percentages compared to the previous period (month).
    
    Args:
        current_user_id: Current authenticated user ID
        db: Database session
        
    Returns:
        StatsOverviewResponse: Overview statistics
        
    Raises:
        HTTPException: If user is not admin
    """
    # Verify admin access
    verify_admin_access(current_user_id, db)
    
    # Get current date and calculate previous period (last month)
    now = datetime.utcnow()
    current_month_start = datetime(now.year, now.month, 1)
    
    # Calculate last month start and end
    if now.month == 1:
        last_month_start = datetime(now.year - 1, 12, 1)
    else:
        last_month_start = datetime(now.year, now.month - 1, 1)
    
    last_month_end = current_month_start - timedelta(seconds=1)
    
    # Total Users: Count of all users
    total_users = db.query(func.count(User.id)).scalar() or 0
    
    # Users for current month
    current_month_users = db.query(func.count(User.id)).filter(
        User.created_at >= current_month_start
    ).scalar() or 0
    
    # Users for last month
    last_month_users = db.query(func.count(User.id)).filter(
        and_(
            User.created_at >= last_month_start,
            User.created_at <= last_month_end
        )
    ).scalar() or 0
    
    # Calculate users change
    users_change = calculate_percentage_change(current_month_users, last_month_users)
    
    # Total Products: Count of all products
    total_products = db.query(func.count(Product.id)).scalar() or 0
    
    # Products for current month
    current_month_products = db.query(func.count(Product.id)).filter(
        Product.created_at >= current_month_start
    ).scalar() or 0
    
    # Products for last month
    last_month_products = db.query(func.count(Product.id)).filter(
        and_(
            Product.created_at >= last_month_start,
            Product.created_at <= last_month_end
        )
    ).scalar() or 0
    
    # Calculate products change
    products_change = calculate_percentage_change(current_month_products, last_month_products)
    
    # Pending Verifications: Count of users not verified
    pending_verifications = db.query(func.count(User.id)).filter(
        User.is_verified == False
    ).scalar() or 0
    
    # Flagged Content: Products that are flagged for review
    flagged_content_count = db.query(func.count(Product.id)).filter(
        Product.is_flagged == True
    ).scalar() or 0
    
    return StatsOverviewResponse(
        total_users=total_users,
        users_change=round(users_change, 1),
        total_products=total_products,
        products_change=round(products_change, 1),
        pending_verifications=pending_verifications,
        flagged_content_count=flagged_content_count
    )


@router.get("/products", response_model=AdminProductListResponse)
async def list_admin_products(
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by title"),
    category: Optional[str] = Query(None, description="Filter by category"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_sold: Optional[bool] = Query(None, description="Filter by sold status"),
    is_verified: Optional[bool] = Query(None, description="Filter by verified status"),
    is_flagged: Optional[bool] = Query(None, description="Filter by flagged status"),
    stock_status: Optional[str] = Query(None, description="Filter by stock status")
):
    """
    List all products with filtering and pagination (Admin only).
    
    Returns a paginated list of products with various filter options.
    
    Args:
        current_user_id: Current authenticated user ID
        db: Database session
        page: Page number (starts from 1)
        page_size: Number of items per page
        search: Search term for product title
        category: Filter by category
        is_active: Filter by active status
        is_sold: Filter by sold status
        is_verified: Filter by verified status
        is_flagged: Filter by flagged status
        stock_status: Filter by stock status (In Stock, Out of Stock, Limited)
        
    Returns:
        AdminProductListResponse: Paginated list of products
        
    Raises:
        HTTPException: If user is not admin
    """
    # Verify admin access
    verify_admin_access(current_user_id, db)
    
    # Build query
    query = db.query(Product)
    
    # Apply filters
    if search:
        search_term = f"%{search}%"
        query = query.filter(Product.title.ilike(search_term))
    
    if category:
        query = query.filter(Product.category == category)
    
    if is_active is not None:
        query = query.filter(Product.is_active == is_active)
    
    if is_sold is not None:
        query = query.filter(Product.is_sold == is_sold)
    
    if is_verified is not None:
        query = query.filter(Product.is_verified == is_verified)
    
    if is_flagged is not None:
        query = query.filter(Product.is_flagged == is_flagged)
    
    if stock_status:
        query = query.filter(Product.stock_status == stock_status)
    
    # Get total count
    total = query.count()
    
    # Calculate offset and pagination
    offset = (page - 1) * page_size
    total_pages = math.ceil(total / page_size) if total > 0 else 0
    
    # Get paginated results
    products = query.order_by(Product.created_at.desc()).offset(offset).limit(page_size).all()
    
    # Convert to response format
    product_list = []
    for product in products:
        product_list.append(AdminProductResponse(
            id=str(product.id),
            title=product.title,
            price=product.price,
            category=product.category,
            condition=product.condition,
            stock_quantity=product.stock_quantity,
            stock_status=product.stock_status,
            is_active=product.is_active,
            is_sold=product.is_sold,
            is_verified=product.is_verified,
            is_flagged=product.is_flagged,
            images=product.images or [],
            owner_id=str(product.owner_id),
            created_at=product.created_at
        ))
    
    return AdminProductListResponse(
        products=product_list,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.patch("/products/{product_id}", response_model=AdminProductResponse)
async def update_admin_product(
    product_id: str,
    update_data: AdminProductUpdateRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Update product status fields (Admin only).
    
    Allows admins to update product status fields like is_active, is_verified,
    is_flagged, and stock_status.
    
    Args:
        product_id: Product UUID
        update_data: Product update data
        current_user_id: Current authenticated user ID
        db: Database session
        
    Returns:
        AdminProductResponse: Updated product
        
    Raises:
        HTTPException: If user is not admin or product not found
    """
    # Verify admin access
    verify_admin_access(current_user_id, db)
    
    # Get product
    try:
        product_uuid = UUID(product_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid product ID format"
        )
    
    product = db.query(Product).filter(Product.id == product_uuid).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Update fields
    update_dict = update_data.model_dump(exclude_unset=True)
    
    if "is_active" in update_dict:
        product.is_active = update_dict["is_active"]
    
    if "is_verified" in update_dict:
        product.is_verified = update_dict["is_verified"]
    
    if "is_flagged" in update_dict:
        product.is_flagged = update_dict["is_flagged"]
    
    if "stock_status" in update_dict:
        # Validate stock_status
        valid_statuses = ["In Stock", "Out of Stock", "Limited"]
        if update_dict["stock_status"] not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid stock_status. Must be one of: {', '.join(valid_statuses)}"
            )
        product.stock_status = update_dict["stock_status"]
    
    db.commit()
    db.refresh(product)
    
    return AdminProductResponse(
        id=str(product.id),
        title=product.title,
        price=product.price,
        category=product.category,
        condition=product.condition,
        stock_quantity=product.stock_quantity,
        stock_status=product.stock_status,
        is_active=product.is_active,
        is_sold=product.is_sold,
        is_verified=product.is_verified,
        is_flagged=product.is_flagged,
        images=product.images or [],
        owner_id=str(product.owner_id),
        created_at=product.created_at
    )


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_admin_product(
    product_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Delete a product (Admin only).
    
    Permanently deletes a product from the database.
    
    Args:
        product_id: Product UUID
        current_user_id: Current authenticated user ID
        db: Database session
        
    Raises:
        HTTPException: If user is not admin or product not found
    """
    # Verify admin access
    verify_admin_access(current_user_id, db)
    
    # Get product
    try:
        product_uuid = UUID(product_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid product ID format"
        )
    
    product = db.query(Product).filter(Product.id == product_uuid).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Delete product
    db.delete(product)
    db.commit()
    
    return None


@router.get("/users", response_model=AdminUserListResponse)
async def list_admin_users(
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by email or username"),
    status: Optional[str] = Query(None, description="Filter by status: 'active' or 'inactive'"),
    is_verified: Optional[bool] = Query(None, description="Filter by verified status")
):
    """
    List all users with filtering and pagination (Admin only).
    
    Returns a paginated list of users with various filter options.
    
    Args:
        current_user_id: Current authenticated user ID
        db: Database session
        page: Page number (starts from 1)
        page_size: Number of items per page
        search: Search term for email or username
        status: Filter by status ('active' maps to is_active=True, 'inactive' maps to is_active=False)
        is_verified: Filter by verified status
        
    Returns:
        AdminUserListResponse: Paginated list of users
        
    Raises:
        HTTPException: If user is not admin
    """
    # Verify admin access
    verify_admin_access(current_user_id, db)
    
    # Build query
    query = db.query(User)
    
    # Apply filters
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                User.email.ilike(search_term),
                User.username.ilike(search_term)
            )
        )
    
    if status:
        if status.lower() == "active":
            query = query.filter(User.is_active == True)
        elif status.lower() == "inactive":
            query = query.filter(User.is_active == False)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid status. Must be 'active' or 'inactive'"
            )
    
    if is_verified is not None:
        query = query.filter(User.is_verified == is_verified)
    
    # Get total count
    total = query.count()
    
    # Calculate offset and pagination
    offset = (page - 1) * page_size
    total_pages = math.ceil(total / page_size) if total > 0 else 0
    
    # Get paginated results
    users = query.order_by(User.created_at.desc()).offset(offset).limit(page_size).all()
    
    # Convert to response format
    user_list = []
    for user in users:
        user_list.append(AdminUserResponse(
            id=str(user.id),
            email=user.email,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            is_active=user.is_active,
            is_verified=user.is_verified,
            is_admin=user.is_admin,
            avatar_url=user.avatar_url,
            created_at=user.created_at
        ))
    
    return AdminUserListResponse(
        users=user_list,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.patch("/users/{user_id}", response_model=AdminUserResponse)
async def update_admin_user(
    user_id: str,
    update_data: AdminUserUpdateRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Update user status fields (Admin only).
    
    Allows admins to update user status fields like is_active and is_verified.
    
    Args:
        user_id: User UUID
        update_data: User update data
        current_user_id: Current authenticated user ID
        db: Database session
        
    Returns:
        AdminUserResponse: Updated user
        
    Raises:
        HTTPException: If user is not admin or user not found
    """
    # Verify admin access
    verify_admin_access(current_user_id, db)
    
    # Get user
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    user = db.query(User).filter(User.id == user_uuid).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update fields
    update_dict = update_data.model_dump(exclude_unset=True)
    
    if "is_active" in update_dict:
        user.is_active = update_dict["is_active"]
    
    if "is_verified" in update_dict:
        user.is_verified = update_dict["is_verified"]
    
    db.commit()
    db.refresh(user)
    
    return AdminUserResponse(
        id=str(user.id),
        email=user.email,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        is_active=user.is_active,
        is_verified=user.is_verified,
        is_admin=user.is_admin,
        avatar_url=user.avatar_url,
        created_at=user.created_at
    )


@router.post("/users/{user_id}/ban", response_model=AdminUserResponse)
async def ban_admin_user(
    user_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Ban a user (Admin only).
    
    Sets user's is_active to False (bans the user).
    
    Args:
        user_id: User UUID
        current_user_id: Current authenticated user ID
        db: Database session
        
    Returns:
        AdminUserResponse: Updated user
        
    Raises:
        HTTPException: If user is not admin or user not found
    """
    # Verify admin access
    verify_admin_access(current_user_id, db)
    
    # Get user
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    user = db.query(User).filter(User.id == user_uuid).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent admin from banning themselves
    if str(user.id) == current_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot ban yourself"
        )
    
    # Ban user (set is_active to False)
    user.is_active = False
    db.commit()
    db.refresh(user)
    
    return AdminUserResponse(
        id=str(user.id),
        email=user.email,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        is_active=user.is_active,
        is_verified=user.is_verified,
        is_admin=user.is_admin,
        avatar_url=user.avatar_url,
        created_at=user.created_at
    )


@router.post("/users/{user_id}/unban", response_model=AdminUserResponse)
async def unban_admin_user(
    user_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Unban a user (Admin only).
    
    Sets user's is_active to True (unbans the user).
    
    Args:
        user_id: User UUID
        current_user_id: Current authenticated user ID
        db: Database session
        
    Returns:
        AdminUserResponse: Updated user
        
    Raises:
        HTTPException: If user is not admin or user not found
    """
    # Verify admin access
    verify_admin_access(current_user_id, db)
    
    # Get user
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    user = db.query(User).filter(User.id == user_uuid).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Unban user (set is_active to True)
    user.is_active = True
    db.commit()
    db.refresh(user)
    
    return AdminUserResponse(
        id=str(user.id),
        email=user.email,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        is_active=user.is_active,
        is_verified=user.is_verified,
        is_admin=user.is_admin,
        avatar_url=user.avatar_url,
        created_at=user.created_at
    )


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_admin_user(
    user_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Delete a user (Admin only).
    
    Permanently deletes a user from the database.
    
    Args:
        user_id: User UUID
        current_user_id: Current authenticated user ID
        db: Database session
        
    Raises:
        HTTPException: If user is not admin or user not found
    """
    # Verify admin access
    verify_admin_access(current_user_id, db)
    
    # Get user
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    user = db.query(User).filter(User.id == user_uuid).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent admin from deleting themselves
    if str(user.id) == current_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself"
        )
    
    # Delete user
    db.delete(user)
    db.commit()
    
    return None

