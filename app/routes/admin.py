"""
Admin management routes.

This module contains admin-only endpoints for managing the platform.
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
import math

from app.database import get_db
from app.security import get_current_user_id
from app.models.user import User
from app.models.product import Product
from app.models.category import MainCategory
from app.schemas.admin import (
    StatsOverviewResponse,
    AdminProductResponse,
    AdminProductListResponse,
    AdminProductUpdateRequest,
    AdminUserResponse,
    AdminUserListResponse,
    AdminUserUpdateRequest
)
from app.schemas.report import (
    ReportedProductListResponse,
    AdminReportListResponse
)
from app.services.report import ProductReportService

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
        user_id_int = int(current_user_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user identifier. Expected integer ID."
        )
    
    user = db.query(User).filter(User.id == user_id_int).first()
    
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
        # Filter by category name - use left join to handle NULL category_ids
        query = query.outerjoin(MainCategory, Product.category_id == MainCategory.id).filter(
            MainCategory.name.ilike(f"%{category}%")
        )
    
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
        # Get category name from relationship
        category_name = product.category.name if product.category else None
        
        product_list.append(AdminProductResponse(
            id=str(product.id),
            title=product.title,
            price=product.price,
            category=category_name,
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


@router.put("/products/{product_id}", response_model=AdminProductResponse)
async def update_admin_product(
    product_id: str,
    update_data: AdminProductUpdateRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Update product fields (Admin only).
    
    Allows admins to update product fields including title, price, condition,
    is_active, is_verified, is_flagged, and stock_status.
    
    Args:
        product_id: Product ID (integer)
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
        product_id_int = int(product_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid product ID format. Expected integer ID."
        )
    
    product = db.query(Product).filter(Product.id == product_id_int).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Update fields
    update_dict = update_data.model_dump(exclude_unset=True)
    
    # Update title if provided
    if "title" in update_dict:
        title = update_dict["title"]
        if title and title.strip():
            product.title = title.strip()
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Title cannot be empty"
            )
    
    # Update price if provided
    if "price" in update_dict:
        price = update_dict["price"]
        if price is not None:
            if price < 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Price cannot be negative"
                )
            product.price = price
    
    # Update condition if provided
    if "condition" in update_dict:
        condition = update_dict["condition"]
        if condition:
            product.condition = condition.strip()
        else:
            product.condition = None
    
    # Update status fields
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
    
    # Get category name from relationship
    category_name = product.category.name if product.category else None
    
    return AdminProductResponse(
        id=str(product.id),
        title=product.title,
        price=product.price,
        category=category_name,
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
        product_id: Product ID (integer)
        current_user_id: Current authenticated user ID
        db: Database session
        
    Raises:
        HTTPException: If user is not admin or product not found
    """
    # Verify admin access
    verify_admin_access(current_user_id, db)
    
    # Get product
    try:
        product_id_int = int(product_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid product ID format. Expected integer ID."
        )
    
    product = db.query(Product).filter(Product.id == product_id_int).first()
    
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
            phone=user.phone,
            country_code=user.country_code,
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


@router.put("/users/{user_id}", response_model=AdminUserResponse)
async def update_admin_user(
    user_id: str,
    update_data: AdminUserUpdateRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Update user full profile (Admin only).
    
    Allows admins to update any user profile fields including email, username,
    personal information, and status fields.
    
    Args:
        user_id: User ID (integer as string)
        update_data: User update data
        current_user_id: Current authenticated user ID
        db: Database session
        
    Returns:
        AdminUserResponse: Updated user
        
    Raises:
        HTTPException: If user is not admin, user not found, or validation fails
    """
    # Verify admin access
    verify_admin_access(current_user_id, db)
    
    # Get user
    try:
        user_id_int = int(user_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format. Expected integer."
        )
    
    user = db.query(User).filter(User.id == user_id_int).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get update data (only fields that were provided)
    update_dict = update_data.model_dump(exclude_unset=True)
    
    # Validate and update email if provided
    if "email" in update_dict:
        email = update_dict["email"]
        if email and email.lower() != user.email.lower():
            # Check if email is taken by another user
            existing = db.query(User).filter(User.email == email.lower()).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email is already taken"
                )
            user.email = email.lower()
    
    # Validate and update username if provided
    if "username" in update_dict:
        username = update_dict["username"]
        if username:
            username = username.strip()
            if username.lower() != user.username.lower():
                # Check if username is taken by another user
                existing = db.query(User).filter(User.username == username.lower()).first()
                if existing:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Username is already taken"
                    )
            user.username = username.lower()
    
    # Update other fields
    updatable_fields = [
        "first_name", "last_name", "phone", "country_code", "bio",
        "avatar_url", "company_name", "sin_number", "is_active", "is_verified"
    ]
    
    for field in updatable_fields:
        if field in update_dict:
            value = update_dict[field]
            # Handle string fields - strip whitespace and convert empty strings to None
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
            detail=f"Failed to update user: {str(e)}"
        )
    
    return AdminUserResponse(
        id=str(user.id),
        email=user.email,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        phone=user.phone,
        country_code=user.country_code,
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
        user_id: User ID (integer as string)
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
        user_id_int = int(user_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format. Expected integer."
        )
    
    user = db.query(User).filter(User.id == user_id_int).first()
    
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
        phone=user.phone,
        country_code=user.country_code,
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
        user_id: User ID (integer as string)
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
        user_id_int = int(user_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format. Expected integer."
        )
    
    user = db.query(User).filter(User.id == user_id_int).first()
    
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
        phone=user.phone,
        country_code=user.country_code,
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
        user_id: User ID (integer as string)
        current_user_id: Current authenticated user ID
        db: Database session
        
    Raises:
        HTTPException: If user is not admin or user not found
    """
    # Verify admin access
    verify_admin_access(current_user_id, db)
    
    # Get user
    try:
        user_id_int = int(user_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format. Expected integer."
        )
    
    user = db.query(User).filter(User.id == user_id_int).first()
    
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


@router.get("/reports", response_model=ReportedProductListResponse)
async def list_reported_products(
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by report status (pending, active, approved, rejected, processing, inactive)"),
    product_id: Optional[str] = Query(None, description="Filter by product ID"),
    user_id: Optional[str] = Query(None, description="Filter by reporting user ID"),
    date_from: Optional[datetime] = Query(None, description="Filter reports from this date (ISO format)"),
    date_to: Optional[datetime] = Query(None, description="Filter reports to this date (ISO format)")
):
    """
    List reported products with aggregation (Admin only).
    
    Returns a paginated list of products that have been reported, grouped by product.
    Each product appears once with a count of total reports.
    
    Args:
        current_user_id: Current authenticated user ID
        db: Database session
        page: Page number (starts from 1)
        page_size: Number of items per page
        status: Filter by report status
        product_id: Filter by specific product ID
        user_id: Filter by reporting user ID
        date_from: Filter reports from this date
        date_to: Filter reports to this date
        
    Returns:
        ReportedProductListResponse: Paginated list of reported products
        
    Raises:
        HTTPException: If user is not admin
    """
    # Verify admin access
    verify_admin_access(current_user_id, db)
    
    service = ProductReportService(db)
    return service.get_reported_products(
        page=page,
        page_size=page_size,
        status_filter=status,
        product_id=product_id,
        user_id=user_id,
        date_from=date_from,
        date_to=date_to
    )


@router.get("/reports/all", response_model=AdminReportListResponse)
async def list_all_reports(
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by report status (pending, active, approved, rejected, processing, inactive)"),
    product_id: Optional[str] = Query(None, description="Filter by product ID"),
    user_id: Optional[str] = Query(None, description="Filter by reporting user ID"),
    date_from: Optional[datetime] = Query(None, description="Filter reports from this date (ISO format)"),
    date_to: Optional[datetime] = Query(None, description="Filter reports to this date (ISO format)")
):
    """
    List all reports with detailed information (Admin only).
    
    Returns a paginated list of all individual reports (not aggregated).
    Each report is shown separately with full details.
    
    Args:
        current_user_id: Current authenticated user ID
        db: Database session
        page: Page number (starts from 1)
        page_size: Number of items per page
        status: Filter by report status
        product_id: Filter by specific product ID
        user_id: Filter by reporting user ID
        date_from: Filter reports from this date
        date_to: Filter reports to this date
        
    Returns:
        AdminReportListResponse: Paginated list of all reports
        
    Raises:
        HTTPException: If user is not admin
    """
    # Verify admin access
    verify_admin_access(current_user_id, db)
    
    service = ProductReportService(db)
    return service.get_all_reports(
        page=page,
        page_size=page_size,
        status_filter=status,
        product_id=product_id,
        user_id=user_id,
        date_from=date_from,
        date_to=date_to
    )


@router.post("/reports/{report_id}/approve", status_code=status.HTTP_200_OK)
async def approve_report(
    report_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Approve a report and deactivate the product (Admin only).
    
    When a report is approved:
    - The report status is set to "approved"
    - The reported product's is_active is set to False
    
    Args:
        report_id: Report ID to approve
        current_user_id: Current authenticated user ID
        db: Database session
        
    Returns:
        Dict[str, str]: Success message
        
    Raises:
        HTTPException: If user is not admin or report not found
    """
    # Verify admin access
    verify_admin_access(current_user_id, db)
    
    service = ProductReportService(db)
    return service.approve_report(report_id)


@router.post("/reports/{report_id}/reject", status_code=status.HTTP_200_OK)
async def reject_report(
    report_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Reject a report and delete it (Admin only).
    
    When a report is rejected:
    - The report record is hard deleted from the database
    - The product remains unchanged
    
    Args:
        report_id: Report ID to reject/delete
        current_user_id: Current authenticated user ID
        db: Database session
        
    Returns:
        Dict[str, str]: Success message
        
    Raises:
        HTTPException: If user is not admin or report not found
    """
    # Verify admin access
    verify_admin_access(current_user_id, db)
    
    service = ProductReportService(db)
    return service.reject_report(report_id)

@router.post("/reports/{report_id}/review", status_code=status.HTTP_200_OK)
async def review_report(
    report_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Review a report and live the product again (Admin only).
    
    When a report is reviewed:
    - The product gets live again by setting is_active to True
    
    Args:
        report_id: Report ID to reject/delete
        current_user_id: Current authenticated user ID
        db: Database session
        
    Returns:
        Dict[str, str]: Success message
        
    Raises:
        HTTPException: If user is not admin or report not found
    """
    # Verify admin access
    verify_admin_access(current_user_id, db)
    
    service = ProductReportService(db)
    return service.review_report(report_id)
