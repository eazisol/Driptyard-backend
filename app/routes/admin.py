"""
Admin management routes.

This module contains admin-only endpoints for managing the platform.
"""

from datetime import datetime, timedelta, date
from typing import Optional, List, Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, cast, Date
from sqlalchemy.exc import IntegrityError
import math
import re
import logging

from app.database import get_db
from app.security import get_current_user_id, get_password_hash
from app.models.user import User
from app.models.product import Product
from app.models.category import MainCategory
from app.models.moderator import ModeratorPermission
from app.models.report import ProductReport, ReportStatus
from app.schemas.admin import (
    StatsOverviewResponse,
    FlaggedContentItem,
    PendingVerificationItem,
    ChartDataPoint,
    AdminProductResponse,
    AdminProductListResponse,
    AdminProductUpdateRequest,
    AdminUserResponse,
    AdminUserListResponse,
    AdminUserUpdateRequest,
    AdminUserCreateRequest,
    AdminUserCreateResponse,
    SuspendUserResponse,
    UnsuspendUserResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
    DeleteUserResponse
)
from app.schemas.report import (
    ReportedProductListResponse,
    AdminReportListResponse
)
from app.schemas.spotlight import (
    SpotlightApplyRequest,
    SpotlightResponse,
    ActiveSpotlightListResponse,
    SpotlightHistoryListResponse
)
from app.schemas.audit_log import (
    AuditLogResponse,
    AuditLogListResponse
)
from app.services.report import ProductReportService
from app.services.spotlight import SpotlightService
from app.services.audit_log import AuditLogService

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


def _get_user_and_permissions(current_user_id: str, db: Session) -> tuple[User, ModeratorPermission | None]:
    """
    Get user and their permissions.
    
    Args:
        current_user_id: Current authenticated user ID
        db: Database session
        
    Returns:
        tuple: (User object, ModeratorPermission object or None)
        
    Raises:
        HTTPException: If user is not found
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
    
    permissions = None
    if user.is_moderator:
        permissions = db.query(ModeratorPermission).filter(
            ModeratorPermission.user_id == user_id_int
        ).first()
    
    return user, permissions


def verify_admin_or_moderator_with_dashboard_permission(current_user_id: str, db: Session) -> User:
    """Verify that the current user is an admin or moderator with can_see_dashboard permission."""
    user, permissions = _get_user_and_permissions(current_user_id, db)
    
    if user.is_admin:
        return user
    
    if user.is_moderator and permissions and permissions.can_see_dashboard:
        return user
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You do not have permission to access the dashboard"
    )


def verify_admin_or_moderator_with_users_permission(current_user_id: str, db: Session, require_manage: bool = False) -> User:
    """
    Verify that the current user is an admin or moderator with users permission.
    
    Args:
        current_user_id: Current authenticated user ID
        db: Database session
        require_manage: If True, requires can_manage_users; if False, requires can_see_users
        
    Returns:
        User: The user object
        
    Raises:
        HTTPException: If user doesn't have permission
    """
    user, permissions = _get_user_and_permissions(current_user_id, db)
    
    if user.is_admin:
        return user
    
    if user.is_moderator and permissions:
        if require_manage:
            if permissions.can_manage_users:
                return user
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to manage users"
            )
        else:
            if permissions.can_see_users:
                return user
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to view users"
            )
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You do not have permission to access users"
    )


def verify_admin_or_moderator_with_listings_permission(current_user_id: str, db: Session, require_manage: bool = False) -> User:
    """
    Verify that the current user is an admin or moderator with listings permission.
    
    Args:
        current_user_id: Current authenticated user ID
        db: Database session
        require_manage: If True, requires can_manage_listings; if False, requires can_see_listings
        
    Returns:
        User: The user object
        
    Raises:
        HTTPException: If user doesn't have permission
    """
    user, permissions = _get_user_and_permissions(current_user_id, db)
    
    if user.is_admin:
        return user
    
    if user.is_moderator and permissions:
        if require_manage:
            if permissions.can_manage_listings:
                return user
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to manage listings"
            )
        else:
            if permissions.can_see_listings:
                return user
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to view listings"
            )
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You do not have permission to access listings"
    )


def verify_admin_or_moderator_with_spotlight_history_permission(current_user_id: str, db: Session) -> User:
    """Verify that the current user is an admin or moderator with can_see_spotlight_history permission."""
    user, permissions = _get_user_and_permissions(current_user_id, db)
    
    if user.is_admin:
        return user
    
    if user.is_moderator and permissions and permissions.can_see_spotlight_history:
        return user
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You do not have permission to view spotlight history"
    )


def verify_admin_or_moderator_with_flagged_content_permission(current_user_id: str, db: Session, require_manage: bool = False) -> User:
    """
    Verify that the current user is an admin or moderator with flagged content permission.
    
    Args:
        current_user_id: Current authenticated user ID
        db: Database session
        require_manage: If True, requires can_manage_flagged_content; if False, requires can_see_flagged_content
        
    Returns:
        User: The user object
        
    Raises:
        HTTPException: If user doesn't have permission
    """
    user, permissions = _get_user_and_permissions(current_user_id, db)
    
    if user.is_admin:
        return user
    
    if user.is_moderator and permissions:
        if require_manage:
            if permissions.can_manage_flagged_content:
                return user
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to manage flagged content"
            )
        else:
            if permissions.can_see_flagged_content:
                return user
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to view flagged content"
            )
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You do not have permission to access flagged content"
    )


def log_audit_action(
    db: Session,
    performed_by_id: int,
    action: str,
    action_type: str,
    target_type: str,
    target_id: str,
    target_identifier: Optional[str] = None,
    details: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> None:
    """
    Helper function to log audit actions.
    
    Args:
        db: Database session
        performed_by_id: ID of the admin/moderator performing the action
        action: Action description
        action_type: Type of action category
        target_type: Type of target
        target_id: ID of the target
        target_identifier: Human-readable identifier
        details: Additional context
        ip_address: IP address of the requester
        user_agent: User agent string
    """
    try:
        audit_service = AuditLogService(db)
        audit_service.log_action(
            performed_by_id=performed_by_id,
            action=action,
            action_type=action_type,
            target_type=target_type,
            target_id=target_id,
            target_identifier=target_identifier,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )
    except Exception as e:
        # Log error but don't fail the request
        logging.error(f"Failed to log audit action: {e}")


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


def generate_chart_data(db: Session, model_class, date_column, days: int = 30) -> List[ChartDataPoint]:
    """
    Generate chart data for the last N days.
    
    Args:
        db: Database session
        model_class: SQLAlchemy model class (User or Product)
        date_column: Column to use for date filtering (created_at)
        days: Number of days to include (default 30)
        
    Returns:
        List[ChartDataPoint]: List of chart data points with daily counts and cumulative totals
    """
    # Calculate date range
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=days - 1)
    
    # Query daily counts - cast timestamp to date for grouping
    daily_counts = db.query(
        func.date(date_column).label('date'),
        func.count(model_class.id).label('count')
    ).filter(
        func.date(date_column) >= start_date,
        func.date(date_column) <= end_date
    ).group_by(
        func.date(date_column)
    ).order_by(
        func.date(date_column)
    ).all()
    
    # Create a dictionary of date -> count
    counts_dict = {row.date: row.count for row in daily_counts}
    
    # Generate all dates in range and fill missing dates with 0
    chart_data = []
    cumulative = 0
    
    # Get total count before the date range for cumulative calculation
    total_before = db.query(func.count(model_class.id)).filter(
        func.date(date_column) < start_date
    ).scalar() or 0
    cumulative = total_before
    
    current_date = start_date
    while current_date <= end_date:
        count = counts_dict.get(current_date, 0)
        cumulative += count
        
        chart_data.append(ChartDataPoint(
            date=current_date.strftime('%Y-%m-%d'),
            count=count,
            cumulative=cumulative
        ))
        
        current_date += timedelta(days=1)
    
    return chart_data


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
        HTTPException: If user doesn't have dashboard access permission
    """
    # Verify admin or moderator with dashboard permission
    verify_admin_or_moderator_with_dashboard_permission(current_user_id, db)
    
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
    
    # Pending verifications for current month (users created this month that are unverified)
    current_month_pending = db.query(func.count(User.id)).filter(
        and_(
            User.is_verified == False,
            User.created_at >= current_month_start
        )
    ).scalar() or 0
    
    # Pending verifications for last month (users created last month that are unverified)
    last_month_pending = db.query(func.count(User.id)).filter(
        and_(
            User.is_verified == False,
            User.created_at >= last_month_start,
            User.created_at <= last_month_end
        )
    ).scalar() or 0
    
    # Calculate pending verifications change
    pending_verifications_change = calculate_percentage_change(current_month_pending, last_month_pending)
    
    # Get pending verification users (limit to 10 most recent)
    pending_verification_users_query = db.query(User).filter(
        User.is_verified == False
    ).order_by(User.created_at.desc()).limit(10).all()
    
    pending_verification_users = [
        PendingVerificationItem(
            id=str(user.id),
            email=user.email,
            username=user.username,
            created_at=user.created_at
        )
        for user in pending_verification_users_query
    ]
    
    # Flagged Content: Products that have pending reports
    # Get pending status
    pending_status = db.query(ReportStatus).filter(
        ReportStatus.status == "pending"
    ).first()
    
    if pending_status:
        # Count unique products with pending reports
        flagged_content_count = db.query(func.count(func.distinct(ProductReport.product_id))).filter(
            ProductReport.status_id == pending_status.id
        ).scalar() or 0
        
        # Flagged content for current month (reports created this month with pending status)
        current_month_flagged = db.query(func.count(func.distinct(ProductReport.product_id))).filter(
            and_(
                ProductReport.status_id == pending_status.id,
                ProductReport.created_at >= current_month_start
            )
        ).scalar() or 0
        
        # Flagged content for last month (reports created last month with pending status)
        last_month_flagged = db.query(func.count(func.distinct(ProductReport.product_id))).filter(
            and_(
                ProductReport.status_id == pending_status.id,
                ProductReport.created_at >= last_month_start,
                ProductReport.created_at <= last_month_end
            )
        ).scalar() or 0
        
        # Calculate flagged content change
        flagged_content_change = calculate_percentage_change(current_month_flagged, last_month_flagged)
        
        # Get flagged content items (products with pending reports, limit to 10 most recent)
        # Get distinct product IDs with pending reports, ordered by most recent report
        flagged_product_ids_query = db.query(
            ProductReport.product_id,
            func.max(ProductReport.created_at).label('latest_report_date')
        ).filter(
            ProductReport.status_id == pending_status.id
        ).group_by(ProductReport.product_id).order_by(
            func.max(ProductReport.created_at).desc()
        ).limit(10).all()
        
        flagged_content = []
        for product_id_result in flagged_product_ids_query:
            product_id_int = product_id_result.product_id
            product = db.query(Product).filter(Product.id == product_id_int).first()
            if product:
                flagged_content.append(FlaggedContentItem(
                    id=str(product.id),
                    title=product.title,
                    owner_id=str(product.owner_id),
                    owner_name=product.owner.username if product.owner else None,
                    created_at=product.created_at
                ))
    else:
        flagged_content_count = 0
        flagged_content_change = 0.0
        flagged_content = []
    
    # Total Listings Removed: Count of product_reports with status_id = 3 (approved/removed)
    total_listings_removed = db.query(func.count(ProductReport.id)).filter(
        ProductReport.status_id == 3
    ).scalar() or 0
    
    # Listings removed for current month (reports with status_id = 3 created this month)
    current_month_removed = db.query(func.count(ProductReport.id)).filter(
        and_(
            ProductReport.status_id == 3,
            ProductReport.created_at >= current_month_start
        )
    ).scalar() or 0
    
    # Listings removed for last month (reports with status_id = 3 created last month)
    last_month_removed = db.query(func.count(ProductReport.id)).filter(
        and_(
            ProductReport.status_id == 3,
            ProductReport.created_at >= last_month_start,
            ProductReport.created_at <= last_month_end
        )
    ).scalar() or 0
    
    # Calculate listings removed change
    listings_removed_change = calculate_percentage_change(current_month_removed, last_month_removed)
    
    # Generate chart data for the last 30 days
    users_growth_data = generate_chart_data(db, User, User.created_at, days=30)
    products_growth_data = generate_chart_data(db, Product, Product.created_at, days=30)
    
    return StatsOverviewResponse(
        total_users=total_users,
        users_change=round(users_change, 1),
        total_products=total_products,
        products_change=round(products_change, 1),
        pending_verifications=pending_verifications,
        pending_verifications_change=round(pending_verifications_change, 1),
        flagged_content_count=flagged_content_count,
        flagged_content_change=round(flagged_content_change, 1),
        total_listings_removed=total_listings_removed,
        listings_removed_change=round(listings_removed_change, 1),
        flagged_content=flagged_content,
        pending_verification_users=pending_verification_users,
        users_growth_data=users_growth_data,
        products_growth_data=products_growth_data
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
    List all products with filtering and pagination (Admin or Moderator with can_see_listings permission).
    
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
        HTTPException: If user doesn't have permission
    """
    # Verify admin or moderator with listings permission
    verify_admin_or_moderator_with_listings_permission(current_user_id, db, require_manage=False)
    
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
            owner_name=product.owner.username if product.owner else None,
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
    Update product fields (Admin or Moderator with can_manage_listings permission).
    
    Allows admins/moderators to update product fields including title, price, condition,
    is_active, is_verified, is_flagged, and stock_status.
    
    Args:
        product_id: Product ID (integer)
        update_data: Product update data
        current_user_id: Current authenticated user ID
        db: Database session
        
    Returns:
        AdminProductResponse: Updated product
        
    Raises:
        HTTPException: If user doesn't have permission or product not found
    """
    # Verify admin or moderator with manage listings permission
    verify_admin_or_moderator_with_listings_permission(current_user_id, db, require_manage=True)
    
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
    
    # Log audit action
    try:
        performed_by_id_int = int(current_user_id)
        log_audit_action(
            db=db,
            performed_by_id=performed_by_id_int,
            action="Updated Listing",
            action_type="product",
            target_type="product",
            target_id=str(product.id),
            target_identifier=product.title
        )
    except Exception as e:
        logging.error(f"Failed to log update product action: {e}")
    
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
    Delete a product (Admin or Moderator with can_manage_listings permission).
    
    Permanently deletes a product from the database.
    
    Args:
        product_id: Product ID (integer)
        current_user_id: Current authenticated user ID
        db: Database session
        
    Raises:
        HTTPException: If user doesn't have permission or product not found
    """
    # Verify admin or moderator with manage listings permission
    verify_admin_or_moderator_with_listings_permission(current_user_id, db, require_manage=True)
    
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
    
    # Store product info for audit log
    product_title = product.title
    product_id_str = str(product.id)
    
    # Delete product
    db.delete(product)
    db.commit()
    
    # Log audit action
    try:
        performed_by_id_int = int(current_user_id)
        log_audit_action(
            db=db,
            performed_by_id=performed_by_id_int,
            action="Removed Listing",
            action_type="product",
            target_type="product",
            target_id=product_id_str,
            target_identifier=product_title
        )
    except Exception as e:
        logging.error(f"Failed to log delete product action: {e}")
    
    return None


@router.get("/users", response_model=AdminUserListResponse)
async def list_admin_users(
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by email or username"),
    status: Optional[str] = Query(None, description="Filter by status: 'active' or 'inactive'"),
    is_verified: Optional[bool] = Query(None, description="Filter by verified status"),
    exclude_admins: bool = Query(True, description="Exclude admin users from results")
):
    """
    List all users with filtering and pagination (Admin or Moderator with can_see_users permission).
    
    Returns a paginated list of users with various filter options.
    
    Args:
        current_user_id: Current authenticated user ID
        db: Database session
        page: Page number (starts from 1)
        page_size: Number of items per page
        search: Search term for email or username
        status: Filter by status ('active' maps to is_active=True, 'inactive' maps to is_active=False)
        is_verified: Filter by verified status
        exclude_admins: Exclude admin users from results (default: True)
        
    Returns:
        AdminUserListResponse: Paginated list of users
        
    Raises:
        HTTPException: If user doesn't have permission
    """
    # Verify admin or moderator with users permission
    verify_admin_or_moderator_with_users_permission(current_user_id, db, require_manage=False)
    
    # Build query
    query = db.query(User)
    
    # Exclude admins if requested
    if exclude_admins:
        query = query.filter(User.is_admin == False)
    
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
        # Count user's active listings
        listings_count = db.query(func.count(Product.id)).filter(
            Product.owner_id == user.id,
            Product.is_active == True
        ).scalar() or 0
        
        user_list.append(AdminUserResponse(
            id=str(user.id),
            user_id=str(user.id),
            email=user.email,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            phone=user.phone,
            country_code=user.country_code,
            bio=user.bio,
            is_active=user.is_active,
            is_verified=user.is_verified,
            is_banned=not user.is_active,
            is_suspended=user.is_suspended if hasattr(user, 'is_suspended') else False,
            is_admin=user.is_admin,
            is_moderator=user.is_moderator,
            avatar_url=user.avatar_url,
            listings_count=listings_count,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login=user.last_login if hasattr(user, 'last_login') else None
        ))
    
    return AdminUserListResponse(
        users=user_list,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/users/{user_id}", response_model=AdminUserResponse)
async def get_admin_user(
    user_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get detailed user information (Admin or Moderator with can_see_users permission).
    
    Returns detailed information about a specific user including all fields.
    
    Args:
        user_id: User ID (integer as string)
        current_user_id: Current authenticated user ID
        db: Database session
        
    Returns:
        AdminUserResponse: Detailed user information
        
    Raises:
        HTTPException: If user doesn't have permission or user not found
    """
    # Verify admin or moderator with users permission
    verify_admin_or_moderator_with_users_permission(current_user_id, db, require_manage=False)
    
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
    
    # Count user's active listings
    listings_count = db.query(func.count(Product.id)).filter(
        Product.owner_id == user.id,
        Product.is_active == True
    ).scalar() or 0
    
    return AdminUserResponse(
        id=str(user.id),
        user_id=str(user.id),
        email=user.email,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        phone=user.phone,
        country_code=user.country_code,
        bio=user.bio,
        is_active=user.is_active,
        is_verified=user.is_verified,
        is_banned=not user.is_active,
        is_suspended=user.is_suspended if hasattr(user, 'is_suspended') else False,
        is_admin=user.is_admin,
        is_moderator=user.is_moderator,
        avatar_url=user.avatar_url,
        listings_count=listings_count,
        created_at=user.created_at,
        updated_at=user.updated_at,
        last_login=user.last_login if hasattr(user, 'last_login') else None
    )


@router.put("/users/{user_id}", response_model=AdminUserResponse)
async def update_admin_user(
    user_id: str,
    update_data: AdminUserUpdateRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Update user full profile (Admin or Moderator with can_manage_users permission).
    
    Allows admins/moderators to update any user profile fields including email, username,
    personal information, and status fields.
    
    Args:
        user_id: User ID (integer as string)
        update_data: User update data
        current_user_id: Current authenticated user ID
        db: Database session
        
    Returns:
        AdminUserResponse: Updated user
        
    Raises:
        HTTPException: If user doesn't have permission, user not found, or validation fails
    """
    # Verify admin or moderator with manage users permission
    verify_admin_or_moderator_with_users_permission(current_user_id, db, require_manage=True)
    
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
    except IntegrityError as e:
        db.rollback()
        error_msg = str(e.orig) if hasattr(e, 'orig') else str(e)
        if 'unique constraint' in error_msg.lower() or 'duplicate' in error_msg.lower():
            if 'email' in error_msg.lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email is already taken"
                )
            elif 'username' in error_msg.lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username is already taken"
                )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation failed: {error_msg}"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user: {str(e)}"
        )
    
    # Count user's active listings
    listings_count = db.query(func.count(Product.id)).filter(
        Product.owner_id == user.id,
        Product.is_active == True
    ).scalar() or 0
    
    # Log audit action
    try:
        performed_by_id_int = int(current_user_id)
        log_audit_action(
            db=db,
            performed_by_id=performed_by_id_int,
            action="Updated User",
            action_type="user",
            target_type="user",
            target_id=str(user.id),
            target_identifier=user.username
        )
    except Exception as e:
        logging.error(f"Failed to log update user action: {e}")
    
    return AdminUserResponse(
        id=str(user.id),
        user_id=str(user.id),
        email=user.email,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        phone=user.phone,
        country_code=user.country_code,
        bio=user.bio,
        is_active=user.is_active,
        is_verified=user.is_verified,
        is_banned=not user.is_active,
        is_suspended=user.is_suspended if hasattr(user, 'is_suspended') else False,
        is_admin=user.is_admin,
        is_moderator=user.is_moderator,
        avatar_url=user.avatar_url,
        listings_count=listings_count,
        created_at=user.created_at,
        updated_at=user.updated_at,
        last_login=user.last_login if hasattr(user, 'last_login') else None
    )


@router.post("/users/{user_id}/ban", response_model=AdminUserResponse)
async def ban_admin_user(
    user_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Ban a user (Admin or Moderator with can_manage_users permission).
    
    Sets user's is_active to False (bans the user).
    
    Args:
        user_id: User ID (integer as string)
        current_user_id: Current authenticated user ID
        db: Database session
        
    Returns:
        AdminUserResponse: Updated user
        
    Raises:
        HTTPException: If user doesn't have permission or user not found
    """
    # Verify admin or moderator with manage users permission
    verify_admin_or_moderator_with_users_permission(current_user_id, db, require_manage=True)
    
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
    
    # Log audit action
    try:
        performed_by_id_int = int(current_user_id)
        log_audit_action(
            db=db,
            performed_by_id=performed_by_id_int,
            action="Banned User",
            action_type="user",
            target_type="user",
            target_id=str(user.id),
            target_identifier=user.username
        )
    except Exception as e:
        logging.error(f"Failed to log ban action: {e}")
    
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
    Unban a user (Admin or Moderator with can_manage_users permission).
    
    Sets user's is_active to True (unbans the user).
    
    Args:
        user_id: User ID (integer as string)
        current_user_id: Current authenticated user ID
        db: Database session
        
    Returns:
        AdminUserResponse: Updated user
        
    Raises:
        HTTPException: If user doesn't have permission or user not found
    """
    # Verify admin or moderator with manage users permission
    verify_admin_or_moderator_with_users_permission(current_user_id, db, require_manage=True)
    
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
    
    # Log audit action
    try:
        performed_by_id_int = int(current_user_id)
        log_audit_action(
            db=db,
            performed_by_id=performed_by_id_int,
            action="Unbanned User",
            action_type="user",
            target_type="user",
            target_id=str(user.id),
            target_identifier=user.username
        )
    except Exception as e:
        logging.error(f"Failed to log unban action: {e}")
    
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


@router.post("/users/{user_id}/suspend", response_model=SuspendUserResponse)
async def suspend_user(
    user_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Suspend a user (Admin or Moderator with can_manage_users permission).
    
    Sets user's is_suspended to True and prevents login while suspended.
    Sends notification email to user.
    
    Args:
        user_id: User ID (integer as string)
        current_user_id: Current authenticated user ID
        db: Database session
        
    Returns:
        SuspendUserResponse: Suspension confirmation
        
    Raises:
        HTTPException: If user doesn't have permission or user not found
    """
    from app.services.email import email_service
    from datetime import datetime
    
    # Verify admin or moderator with manage users permission
    verify_admin_or_moderator_with_users_permission(current_user_id, db, require_manage=True)
    
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
    
    # Prevent admin from suspending themselves
    if str(user.id) == current_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot suspend yourself"
        )
    
    # Suspend user
    user.is_suspended = True
    user.is_active = False
    user.suspended_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    
    # Send notification email (asynchronously - don't wait for it)
    try:
        email_service.send_account_suspended_email(user.email, user.username)
    except Exception as e:
        # Log error but don't fail the request
        print(f"Failed to send suspension email: {e}")
    
    # Log audit action
    try:
        performed_by_id_int = int(current_user_id)
        log_audit_action(
            db=db,
            performed_by_id=performed_by_id_int,
            action="Suspended User",
            action_type="user",
            target_type="user",
            target_id=str(user.id),
            target_identifier=user.username
        )
    except Exception as e:
        logging.error(f"Failed to log suspend action: {e}")
    
    return SuspendUserResponse(
        success=True,
        message="User suspended successfully",
        user_id=str(user.id),
        suspended_at=user.suspended_at
    )


@router.post("/users/{user_id}/unsuspend", response_model=UnsuspendUserResponse)
async def unsuspend_user(
    user_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Unsuspend (reinstate) a user (Admin or Moderator with can_manage_users permission).
    
    Sets user's is_suspended to False and restores access.
    Sends notification email to user.
    
    Args:
        user_id: User ID (integer as string)
        current_user_id: Current authenticated user ID
        db: Database session
        
    Returns:
        UnsuspendUserResponse: Reinstatement confirmation
        
    Raises:
        HTTPException: If user doesn't have permission or user not found
    """
    from app.services.email import email_service
    from datetime import datetime
    
    # Verify admin or moderator with manage users permission
    verify_admin_or_moderator_with_users_permission(current_user_id, db, require_manage=True)
    
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
    
    # Unsuspend user
    user.is_suspended = False
    user.is_active = True
    user.suspended_at = None
    db.commit()
    db.refresh(user)
    
    unsuspended_at = datetime.utcnow()
    
    # Send notification email (asynchronously - don't wait for it)
    try:
        email_service.send_account_reinstated_email(user.email, user.username)
    except Exception as e:
        # Log error but don't fail the request
        print(f"Failed to send reinstatement email: {e}")
    
    # Log audit action
    try:
        performed_by_id_int = int(current_user_id)
        log_audit_action(
            db=db,
            performed_by_id=performed_by_id_int,
            action="Unsuspended User",
            action_type="user",
            target_type="user",
            target_id=str(user.id),
            target_identifier=user.username
        )
    except Exception as e:
        logging.error(f"Failed to log unsuspend action: {e}")
    
    return UnsuspendUserResponse(
        success=True,
        message="User reinstated successfully",
        user_id=str(user.id),
        unsuspended_at=unsuspended_at
    )


@router.post("/users/{user_id}/reset-password", response_model=ResetPasswordResponse)
async def reset_user_password(
    user_id: str,
    request: ResetPasswordRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Reset user password (Admin or Moderator with can_manage_users permission).
    
    Accepts a new password in the request body, hashes it, and sets it immediately.
    Sends email to user with the new password.
    
    Args:
        user_id: User ID (integer as string)
        request: Password reset request with new_password
        current_user_id: Current authenticated user ID
        db: Database session
        
    Returns:
        ResetPasswordResponse: Password reset confirmation
        
    Raises:
        HTTPException: If user doesn't have permission, user not found, or password validation fails
    """
    from app.services.email import email_service
    
    # Verify admin or moderator with manage users permission
    verify_admin_or_moderator_with_users_permission(current_user_id, db, require_manage=True)
    
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
    
    # Hash the new password
    try:
        hashed_password = get_password_hash(request.new_password)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password hashing failed: {str(e)}"
        )
    
    # Update user's password immediately
    user.hashed_password = hashed_password
    
    try:
        db.commit()
        db.refresh(user)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update password: {str(e)}"
        )
    
    # Send notification email with the new password (asynchronously - don't wait for it)
    try:
        email_service.send_admin_password_reset_email(user.email, user.username, request.new_password)
    except Exception as e:
        # Log error but don't fail the request
        print(f"Failed to send password reset email: {e}")
    
    # Log audit action
    try:
        performed_by_id_int = int(current_user_id)
        log_audit_action(
            db=db,
            performed_by_id=performed_by_id_int,
            action="Reset Password",
            action_type="user",
            target_type="user",
            target_id=str(user.id),
            target_identifier=user.username
        )
    except Exception as e:
        logging.error(f"Failed to log reset password action: {e}")
    
    return ResetPasswordResponse(
        success=True,
        message="Password reset successfully. Email sent to user with new password.",
        user_id=str(user.id)
    )


@router.delete("/users/{user_id}", response_model=DeleteUserResponse)
async def delete_admin_user(
    user_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Delete a user (Admin or Moderator with can_manage_users permission).
    
    Permanently deletes a user and all associated data including:
    - User's listings (products)
    - User's orders/transactions
    - User's profile data
    - Any other associated records
    
    Records the deletion event in system logs for auditing purposes.
    Sends notification email to user before deletion (if possible).
    
    Args:
        user_id: User ID (integer as string)
        current_user_id: Current authenticated user ID
        db: Database session
        
    Returns:
        DeleteUserResponse: Deletion confirmation
        
    Raises:
        HTTPException: If user doesn't have permission or user not found
    """
    from app.services.email import email_service
    from datetime import datetime
    import logging
    
    # Verify admin or moderator with manage users permission
    verify_admin_or_moderator_with_users_permission(current_user_id, db, require_manage=True)
    
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
    
    # Store user info for logging and email (before deletion)
    user_email = user.email
    user_username = user.username
    deleted_at = datetime.utcnow()
    
    # Send notification email before deletion (if possible)
    try:
        email_service.send_account_deleted_email(user_email, user_username)
    except Exception as e:
        # Log error but continue with deletion
        print(f"Failed to send deletion email: {e}")
    
    # Import all related models
    from app.models.follow import SellerFollow, ProductFollow
    from app.models.moderator import ModeratorPermission
    from app.models.spotlight import Spotlight, SpotlightHistory
    from app.models.report import ProductReport
    from app.models.user import EmailVerification, PasswordResetToken, RegistrationData
    
    # Get user's product IDs first
    user_product_ids = db.query(Product.id).filter(Product.owner_id == user_id_int).all()
    user_product_id_list = [p[0] for p in user_product_ids]
    
    # Helper function to safely delete records
    def safe_delete(query_func, error_message):
        """Safely execute a delete query, catching and logging any errors."""
        try:
            query_func()
        except Exception as e:
            # Rollback the transaction to reset the failed state
            db.rollback()
            error_str = str(e)
            # Check if it's a "table does not exist" error
            if "does not exist" in error_str.lower() or "undefinedtable" in error_str.lower():
                logger.warning(f"Skipping deletion - table may not exist: {error_message}")
            else:
                logger.warning(f"Could not delete {error_message}: {error_str}")
    
    logger = logging.getLogger(__name__)
    
    # Try to delete orders (table might not exist yet)
    try:
        from app.models.order import Order
        safe_delete(
            lambda: db.query(Order).filter(Order.product_id.in_(user_product_id_list)).delete() if user_product_id_list else None,
            "orders for user's products"
        )
        safe_delete(
            lambda: db.query(Order).filter(
                or_(Order.buyer_id == user_id_int, Order.seller_id == user_id_int)
            ).delete(),
            "orders where user is buyer or seller"
        )
    except ImportError:
        # Order model might not be imported - that's okay
        logger.warning("Order model not available, skipping order deletion")
    except Exception as e:
        db.rollback()
        logger.warning(f"Could not delete orders: {e}")
    
    # Delete product follows for user's products
    if user_product_id_list:
        safe_delete(
            lambda: db.query(ProductFollow).filter(ProductFollow.product_id.in_(user_product_id_list)).delete(),
            "product follows for user's products"
        )
    
    # Delete user's products (listings) - this will cascade to product-related records
    user_products = db.query(Product).filter(Product.owner_id == user_id_int).all()
    for product in user_products:
        db.delete(product)
    
    # Delete seller follows (where user is follower or followed)
    safe_delete(
        lambda: db.query(SellerFollow).filter(
            or_(SellerFollow.follower_id == user_id_int, SellerFollow.followed_user_id == user_id_int)
        ).delete(),
        "seller follows"
    )
    
    # Delete product follows
    safe_delete(
        lambda: db.query(ProductFollow).filter(ProductFollow.user_id == user_id_int).delete(),
        "product follows"
    )
    
    # Delete moderator permissions
    safe_delete(
        lambda: db.query(ModeratorPermission).filter(ModeratorPermission.user_id == user_id_int).delete(),
        "moderator permissions"
    )
    
    # Delete spotlights where user applied them
    try:
        # Note: We need to handle spotlight history first as it references spotlights
        spotlight_ids = db.query(Spotlight.id).filter(Spotlight.applied_by == user_id_int).all()
        spotlight_id_list = [s[0] for s in spotlight_ids]
        
        # Delete spotlight history entries where user applied or removed
        safe_delete(
            lambda: db.query(SpotlightHistory).filter(
                or_(
                    SpotlightHistory.applied_by == user_id_int,
                    SpotlightHistory.removed_by == user_id_int
                )
            ).delete(),
            "spotlight history (applied/removed by user)"
        )
        
        # Delete spotlight history entries that reference spotlights created by this user
        if spotlight_id_list:
            safe_delete(
                lambda: db.query(SpotlightHistory).filter(
                    SpotlightHistory.spotlight_id.in_(spotlight_id_list)
                ).delete(),
                "spotlight history (for user's spotlights)"
            )
        
        # Delete spotlight history entries for user's products
        if user_product_id_list:
            safe_delete(
                lambda: db.query(SpotlightHistory).filter(
                    SpotlightHistory.product_id.in_(user_product_id_list)
                ).delete(),
                "spotlight history (for user's products)"
            )
        
        # Delete spotlights
        safe_delete(
            lambda: db.query(Spotlight).filter(Spotlight.applied_by == user_id_int).delete(),
            "spotlights (applied by user)"
        )
        
        # Delete spotlights for user's products
        if user_product_id_list:
            safe_delete(
                lambda: db.query(Spotlight).filter(Spotlight.product_id.in_(user_product_id_list)).delete(),
                "spotlights (for user's products)"
            )
    except Exception as e:
        db.rollback()
        logger.warning(f"Error during spotlight deletion: {e}")
    
    # Delete product reports by this user
    safe_delete(
        lambda: db.query(ProductReport).filter(ProductReport.user_id == user_id_int).delete(),
        "product reports by user"
    )
    
    # Delete product reports about user's products
    if user_product_id_list:
        safe_delete(
            lambda: db.query(ProductReport).filter(ProductReport.product_id.in_(user_product_id_list)).delete(),
            "product reports about user's products"
        )
    
    # Delete email verifications
    safe_delete(
        lambda: db.query(EmailVerification).filter(EmailVerification.email == user_email).delete(),
        "email verifications"
    )
    
    # Delete password reset tokens
    safe_delete(
        lambda: db.query(PasswordResetToken).filter(PasswordResetToken.email == user_email).delete(),
        "password reset tokens"
    )
    
    # Delete registration data
    safe_delete(
        lambda: db.query(RegistrationData).filter(RegistrationData.email == user_email).delete(),
        "registration data"
    )
    
    # Finally, delete the user (this is the critical operation)
    try:
        db.delete(user)
        db.commit()
    except Exception as e:
        db.rollback()
        error_msg = str(e)
        logger.error(
            f"Failed to delete user {user_id_int}: {error_msg}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cannot perform this operation due to related records: {error_msg}"
        )
    
    # Log deletion event for auditing
    logger = logging.getLogger(__name__)
    logger.info(
        f"User deleted - User ID: {user_id_int}, "
        f"Email: {user_email}, "
        f"Username: {user_username}, "
        f"Deleted by: {current_user_id}, "
        f"Deleted at: {deleted_at.isoformat()}"
    )
    
    # Log audit action
    try:
        performed_by_id_int = int(current_user_id)
        log_audit_action(
            db=db,
            performed_by_id=performed_by_id_int,
            action="Deleted User",
            action_type="user",
            target_type="user",
            target_id=str(user_id_int),
            target_identifier=user_username
        )
    except Exception as e:
        logging.error(f"Failed to log delete user action: {e}")
    
    return DeleteUserResponse(
        success=True,
        message="User deleted successfully",
        user_id=str(user_id_int),
        deleted_at=deleted_at
    )


@router.get("/reports", response_model=ReportedProductListResponse)
async def list_reported_products(
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by product title or report reason"),
    status: Optional[str] = Query(None, description="Filter by report status (pending, active, approved, rejected, processing, inactive)"),
    product_id: Optional[str] = Query(None, description="Filter by product ID"),
    user_id: Optional[str] = Query(None, description="Filter by reporting user ID"),
    date_from: Optional[datetime] = Query(None, description="Filter reports from this date (ISO format)"),
    date_to: Optional[datetime] = Query(None, description="Filter reports to this date (ISO format)")
):
    """
    List reported products with aggregation, search, and filtering (Admin or Moderator with can_see_flagged_content permission).
    
    Returns a paginated list of products that have been reported, grouped by product.
    Each product appears once with a count of total reports.
    Supports searching by product title or report reason.
    
    Args:
        current_user_id: Current authenticated user ID
        db: Database session
        page: Page number (starts from 1)
        page_size: Number of items per page
        search: Search term for product title or report reason
        status: Filter by report status
        product_id: Filter by specific product ID
        user_id: Filter by reporting user ID
        date_from: Filter reports from this date
        date_to: Filter reports to this date
        
    Returns:
        ReportedProductListResponse: Paginated list of reported products
        
    Raises:
        HTTPException: If user doesn't have permission
    """
    # Verify admin or moderator with flagged content permission
    verify_admin_or_moderator_with_flagged_content_permission(current_user_id, db, require_manage=False)
    
    service = ProductReportService(db)
    return service.get_reported_products(
        page=page,
        page_size=page_size,
        search=search,
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
    search: Optional[str] = Query(None, description="Search by product title or report reason"),
    status: Optional[str] = Query(None, description="Filter by report status (pending, active, approved, rejected, processing, inactive)"),
    product_id: Optional[str] = Query(None, description="Filter by product ID"),
    user_id: Optional[str] = Query(None, description="Filter by reporting user ID"),
    date_from: Optional[datetime] = Query(None, description="Filter reports from this date (ISO format)"),
    date_to: Optional[datetime] = Query(None, description="Filter reports to this date (ISO format)")
):
    """
    List all reports with detailed information, search, and filtering (Admin or Moderator with can_see_flagged_content permission).
    
    Returns a paginated list of all individual reports (not aggregated).
    Each report is shown separately with full details.
    Supports searching by product title or report reason.
    
    Args:
        current_user_id: Current authenticated user ID
        db: Database session
        page: Page number (starts from 1)
        page_size: Number of items per page
        search: Search term for product title or report reason
        status: Filter by report status
        product_id: Filter by specific product ID
        user_id: Filter by reporting user ID
        date_from: Filter reports from this date
        date_to: Filter reports to this date
        
    Returns:
        AdminReportListResponse: Paginated list of all reports
        
    Raises:
        HTTPException: If user doesn't have permission
    """
    # Verify admin or moderator with flagged content permission
    verify_admin_or_moderator_with_flagged_content_permission(current_user_id, db, require_manage=False)
    
    service = ProductReportService(db)
    return service.get_all_reports(
        page=page,
        page_size=page_size,
        search=search,
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
    Approve a report and deactivate the product (Admin or Moderator with can_manage_flagged_content permission).
    
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
        HTTPException: If user doesn't have permission or report not found
    """
    # Verify admin or moderator with manage flagged content permission
    verify_admin_or_moderator_with_flagged_content_permission(current_user_id, db, require_manage=True)
    
    # Get report and product info for audit logging
    try:
        report_id_int = int(report_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid report ID format. Expected integer ID."
        )
    
    report = db.query(ProductReport).filter(ProductReport.id == report_id_int).first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    product = db.query(Product).filter(Product.id == report.product_id).first()
    product_title = product.title if product else f"Product #{report.product_id}"
    
    service = ProductReportService(db)
    result = service.approve_report(report_id)
    
    # Log audit action
    try:
        performed_by_id_int = int(current_user_id)
        log_audit_action(
            db=db,
            performed_by_id=performed_by_id_int,
            action="Approved Report",
            action_type="report",
            target_type="product",
            target_id=str(report.product_id),
            target_identifier=product_title,
            details=f"Report #{report_id} approved, product deactivated"
        )
    except Exception as e:
        logging.error(f"Failed to log approve report action: {e}")
    
    return result


@router.post("/reports/{report_id}/reject", status_code=status.HTTP_200_OK)
async def reject_report(
    report_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Reject a report and delete it (Admin or Moderator with can_manage_flagged_content permission).
    
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
        HTTPException: If user doesn't have permission or report not found
    """
    # Verify admin or moderator with manage flagged content permission
    verify_admin_or_moderator_with_flagged_content_permission(current_user_id, db, require_manage=True)
    
    # Get report and product info for audit logging
    try:
        report_id_int = int(report_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid report ID format. Expected integer ID."
        )
    
    report = db.query(ProductReport).filter(ProductReport.id == report_id_int).first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    product = db.query(Product).filter(Product.id == report.product_id).first()
    product_title = product.title if product else f"Product #{report.product_id}"
    
    service = ProductReportService(db)
    result = service.reject_report(report_id)
    
    # Log audit action
    try:
        performed_by_id_int = int(current_user_id)
        log_audit_action(
            db=db,
            performed_by_id=performed_by_id_int,
            action="Rejected Report",
            action_type="report",
            target_type="product",
            target_id=str(report.product_id),
            target_identifier=product_title,
            details=f"Report #{report_id} rejected and deleted"
        )
    except Exception as e:
        logging.error(f"Failed to log reject report action: {e}")
    
    return result

@router.post("/reports/{report_id}/review", status_code=status.HTTP_200_OK)
async def review_report(
    report_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Review a report and live the product again (Admin or Moderator with can_manage_flagged_content permission).
    
    When a report is reviewed:
    - The product gets live again by setting is_active to True
    
    Args:
        report_id: Report ID to reject/delete
        current_user_id: Current authenticated user ID
        db: Database session
        
    Returns:
        Dict[str, str]: Success message
        
    Raises:
        HTTPException: If user doesn't have permission or report not found
    """
    # Verify admin or moderator with manage flagged content permission
    verify_admin_or_moderator_with_flagged_content_permission(current_user_id, db, require_manage=True)
    
    # Get report and product info for audit logging
    try:
        report_id_int = int(report_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid report ID format. Expected integer ID."
        )
    
    report = db.query(ProductReport).filter(ProductReport.id == report_id_int).first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    product = db.query(Product).filter(Product.id == report.product_id).first()
    product_title = product.title if product else f"Product #{report.product_id}"
    
    service = ProductReportService(db)
    result = service.review_report(report_id)
    
    # Log audit action
    try:
        performed_by_id_int = int(current_user_id)
        log_audit_action(
            db=db,
            performed_by_id=performed_by_id_int,
            action="Reviewed Report",
            action_type="report",
            target_type="product",
            target_id=str(report.product_id),
            target_identifier=product_title,
            details=f"Report #{report_id} reviewed, product reactivated"
        )
    except Exception as e:
        logging.error(f"Failed to log review report action: {e}")
    
    return result


@router.post("/products/{product_id}/spotlight", response_model=SpotlightResponse, status_code=status.HTTP_201_CREATED)
async def apply_spotlight(
    product_id: str,
    request: SpotlightApplyRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Apply spotlight to a product (Admin or Moderator with permission).
    
    Spotlights a verified product by setting it as featured and prioritizing it
    in listings. The spotlight will automatically expire after the specified duration.
    
    Args:
        product_id: Product ID to spotlight
        request: Spotlight request with duration or custom end time
        current_user_id: Current authenticated user ID
        db: Database session
        
    Returns:
        SpotlightResponse: Spotlight details
        
    Raises:
        HTTPException: If user doesn't have permission, product not found, or validation fails
    """
    # Get user to verify they exist (permission check happens in service)
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
    
    # Check if user is admin or moderator
    if not user.is_admin and not user.is_moderator:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or moderator access required"
        )
    
    # Convert product_id to int
    try:
        product_id_int = int(product_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid product ID format. Expected integer ID."
        )
    
    # Get product for audit logging
    product = db.query(Product).filter(Product.id == product_id_int).first()
    product_title = product.title if product else f"Product #{product_id}"
    
    # Apply spotlight (service will check specific permissions)
    service = SpotlightService(db)
    result = service.apply_spotlight(
        product_id=product_id_int,
        admin_user_id=user_id_int,
        duration_hours=request.duration_hours,
        custom_end_time=request.custom_end_time
    )
    
    # Log audit action
    try:
        log_audit_action(
            db=db,
            performed_by_id=user_id_int,
            action="Applied Spotlight",
            action_type="spotlight",
            target_type="product",
            target_id=str(product_id_int),
            target_identifier=product_title
        )
    except Exception as e:
        logging.error(f"Failed to log apply spotlight action: {e}")
    
    return result


@router.delete("/products/{product_id}/spotlight", status_code=status.HTTP_200_OK)
async def remove_spotlight(
    product_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Remove spotlight from a product (Admin or Moderator with permission).
    
    Removes the active spotlight from a product, returning it to normal
    status (is_spotlighted = false).
    
    Args:
        product_id: Product ID to remove spotlight from
        current_user_id: Current authenticated user ID
        db: Database session
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: If user doesn't have permission or spotlight not found
    """
    # Get user to verify they exist (permission check happens in service)
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
    
    # Check if user is admin or moderator
    if not user.is_admin and not user.is_moderator:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or moderator access required"
        )
    
    # Convert product_id to int
    try:
        product_id_int = int(product_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid product ID format. Expected integer ID."
        )
    
    # Get product for audit logging
    product = db.query(Product).filter(Product.id == product_id_int).first()
    product_title = product.title if product else f"Product #{product_id}"
    
    # Remove spotlight (service will check specific permissions)
    service = SpotlightService(db)
    result = service.remove_spotlight(
        product_id=product_id_int,
        admin_user_id=user_id_int
    )
    
    # Log audit action
    try:
        log_audit_action(
            db=db,
            performed_by_id=user_id_int,
            action="Removed Spotlight",
            action_type="spotlight",
            target_type="product",
            target_id=str(product_id_int),
            target_identifier=product_title
        )
    except Exception as e:
        logging.error(f"Failed to log remove spotlight action: {e}")
    
    return result


@router.get("/spotlight/active", response_model=ActiveSpotlightListResponse)
async def get_active_spotlights(
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page")
):
    """
    Get all active spotlights (Admin or Moderator with can_see_spotlight_history permission).
    
    Returns a paginated list of currently active spotlighted products,
    showing when they were applied and when they will expire.
    
    Args:
        current_user_id: Current authenticated user ID
        db: Database session
        page: Page number
        page_size: Items per page
        
    Returns:
        ActiveSpotlightListResponse: Paginated list of active spotlights
        
    Raises:
        HTTPException: If user doesn't have permission
    """
    # Verify admin or moderator with spotlight history permission
    verify_admin_or_moderator_with_spotlight_history_permission(current_user_id, db)
    
    # Get active spotlights
    service = SpotlightService(db)
    return service.get_active_spotlights(page=page, page_size=page_size)


@router.get("/spotlight/history", response_model=SpotlightHistoryListResponse)
async def get_spotlight_history(
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    product_id: Optional[str] = Query(None, description="Filter by product ID"),
    status: Optional[str] = Query(None, description="Filter by action (applied, expired, removed)"),
    date_from: Optional[datetime] = Query(None, description="Filter from date (ISO format)"),
    date_to: Optional[datetime] = Query(None, description="Filter to date (ISO format)")
):
    """
    Get spotlight history (Admin or Moderator with can_see_spotlight_history permission).
    
    Returns a paginated list of spotlight history entries, including
    applied, expired, and removed spotlights. Supports filtering by
    product, action type, and date range.
    
    Args:
        current_user_id: Current authenticated user ID
        db: Database session
        page: Page number
        page_size: Items per page
        product_id: Filter by product ID
        status: Filter by action type
        date_from: Filter from date
        date_to: Filter to date
        
    Returns:
        SpotlightHistoryListResponse: Paginated list of history entries
        
    Raises:
        HTTPException: If user doesn't have permission
    """
    # Verify admin or moderator with spotlight history permission
    verify_admin_or_moderator_with_spotlight_history_permission(current_user_id, db)
    
    # Convert product_id to int if provided
    product_id_int = None
    if product_id:
        try:
            product_id_int = int(product_id)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid product ID format. Expected integer ID."
            )
    
    # Get spotlight history
    service = SpotlightService(db)
    return service.get_spotlight_history(
        page=page,
        page_size=page_size,
        product_id=product_id_int,
        status=status,
        date_from=date_from,
        date_to=date_to
    )


@router.post("/users/create", response_model=AdminUserCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: AdminUserCreateRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Create a new user, moderator, or admin (Admin only).
    
    Creates a new user account with all required fields. Use the boolean flags
    (is_admin, is_moderator, is_customer) to specify the user type. Exactly one
    of these flags must be true.
    
    Important Notes:
    - All admin-created users are automatically verified (is_verified=True)
    - NO verification emails are sent to users created through this endpoint
    - is_customer flag is only used for validation, NOT stored in database
    - When is_customer=true, both is_admin and is_moderator will be False in DB
    - Database only stores is_admin and is_moderator columns
    
    Args:
        user_data: User creation data including email, password, username, phone, etc.
                  Must include exactly one of: is_admin=true, is_moderator=true, or is_customer=true
        current_user_id: Current authenticated user ID
        db: Database session
        
    Returns:
        AdminUserCreateResponse: Created user information
        
    Raises:
        HTTPException: If user is not admin, email/username already exists, validation fails, or creation fails
    """
    # Verify admin access
    verify_admin_access(current_user_id, db)
    
    # Check if user with this email already exists
    existing_user = db.query(User).filter(User.email == user_data.email.lower()).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    
    # Check if username already exists
    existing_username = db.query(User).filter(User.username == user_data.username.lower()).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already taken"
        )
    
    # Hash password
    try:
        hashed_password = get_password_hash(user_data.password)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password hashing failed: {str(e)}"
        )
    
    # Use the boolean flags directly from the request
    # Validation ensures exactly one of is_admin, is_moderator, or is_customer is true
    # Note: is_customer is NOT stored in database - when is_customer=true,
    #       both is_admin and is_moderator will be False (which represents a customer)
    
    # Create user account
    # Admin-created users are automatically verified (no email verification needed)
    new_user = User(
        email=user_data.email.lower(),
        username=user_data.username.lower(),
        hashed_password=hashed_password,
        phone=user_data.phone,
        country_code=user_data.country_code,
        company_name=user_data.company_name,
        sin_number=user_data.sin_number,
        is_admin=user_data.is_admin,
        is_moderator=user_data.is_moderator,
        # is_customer is NOT stored - it's just for validation
        # When is_customer=true, both is_admin and is_moderator are False
        is_active=True,
        is_verified=True  # Admin-created users are automatically verified (NO email sent)
    )
    
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )
    
    # Generate success message based on user type flags
    if user_data.is_admin:
        user_type_name = "admin"
    elif user_data.is_moderator:
        user_type_name = "moderator"
    else:
        user_type_name = "customer"
    success_message = f"{user_type_name.capitalize()} created successfully"
    
    # Log audit action
    try:
        performed_by_id_int = int(current_user_id)
        log_audit_action(
            db=db,
            performed_by_id=performed_by_id_int,
            action=f"Created {user_type_name.capitalize()}",
            action_type="user",
            target_type="user",
            target_id=str(new_user.id),
            target_identifier=new_user.username
        )
    except Exception as e:
        logging.error(f"Failed to log create user action: {e}")
    
    return AdminUserCreateResponse(
        id=str(new_user.id),
        email=new_user.email,
        username=new_user.username,
        phone=new_user.phone,
        country_code=new_user.country_code,
        is_active=new_user.is_active,
        is_verified=new_user.is_verified,
        is_moderator=new_user.is_moderator,
        is_admin=new_user.is_admin,
        created_at=new_user.created_at,
        message=success_message
    )


@router.get("/logs", response_model=AuditLogListResponse)
async def get_audit_logs(
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    action_type: Optional[str] = Query(None, description="Filter by action type (user, product, spotlight, moderator, report)"),
    target_type: Optional[str] = Query(None, description="Filter by target type (user, product, spotlight, moderator)"),
    performed_by_id: Optional[int] = Query(None, description="Filter by admin/moderator ID"),
    search: Optional[str] = Query(None, description="Search in action, target, or admin username"),
    date_from: Optional[datetime] = Query(None, description="Filter logs from this date (ISO format)"),
    date_to: Optional[datetime] = Query(None, description="Filter logs to this date (ISO format)"),
    role: Optional[str] = Query(None, description="Filter by role: 'admin' or 'moderator'"),
    is_admin: Optional[bool] = Query(None, description="Filter by role: true for admin, false for moderator"),
    action: Optional[str] = Query(None, description="Filter by specific action name (e.g., 'Applied Spotlight', 'Updated Listing')"),
    date: Annotated[Optional[str], Query(
        description="Filter by specific date. Accepts YYYY-MM-DD format (e.g., 2025-12-05) or ISO datetime format"
    )] = None
):
    """
    Get audit logs with filtering and pagination (Admin or Moderator with dashboard permission).
    
    Returns a paginated list of audit log entries showing all admin and moderator actions.
    Supports filtering by role, action, date, action type, target type, performer, and search.
    
    Args:
        current_user_id: Current authenticated user ID
        db: Database session
        page: Page number (starts from 1)
        page_size: Number of items per page
        action_type: Filter by action type (user, product, spotlight, moderator, report)
        target_type: Filter by target type (user, product, spotlight, moderator)
        performed_by_id: Filter by admin/moderator ID
        search: Search term for action, target, or admin username
        date_from: Filter logs from this date (ISO format)
        date_to: Filter logs to this date (ISO format)
        role: Filter by role - 'admin' or 'moderator' (alternative to is_admin)
        is_admin: Filter by role - true for admin, false for moderator (takes precedence over role)
        action: Filter by specific action name (e.g., 'Applied Spotlight', 'Updated Listing', 'Suspended User')
        date: Filter by specific date (filters logs on that exact date)
        
    Returns:
        AuditLogListResponse: Paginated list of audit logs
        
    Raises:
        HTTPException: If user doesn't have permission
    """
    import math
    
    # Verify admin or moderator with dashboard permission
    verify_admin_or_moderator_with_dashboard_permission(current_user_id, db)
    
    # Determine role filter - is_admin takes precedence over role parameter
    is_admin_filter = None
    if is_admin is not None:
        # Use is_admin boolean parameter directly (FastAPI parses query params automatically)
        is_admin_filter = is_admin
    elif role:
        # Convert role string to boolean
        role_lower = role.lower()
        if role_lower == "admin":
            is_admin_filter = True
        elif role_lower == "moderator":
            is_admin_filter = False
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid role. Must be 'admin' or 'moderator'"
            )
    
    # Parse date parameter (can be YYYY-MM-DD or full datetime)
    parsed_date = None
    if date:
        try:
            # Try parsing as date-only first (YYYY-MM-DD)
            if len(date) == 10 and date.count('-') == 2:
                # Date-only format: YYYY-MM-DD
                from datetime import date as date_type
                date_obj = date_type.fromisoformat(date)
                # Convert to datetime at start of day
                parsed_date = datetime.combine(date_obj, datetime.min.time())
            else:
                # Full datetime format
                parsed_date = datetime.fromisoformat(date.replace('Z', '+00:00'))
        except (ValueError, AttributeError) as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid date format. Use YYYY-MM-DD or ISO datetime format. Error: {str(e)}"
            )
    
    # Get audit logs
    service = AuditLogService(db)
    logs, total = service.get_audit_logs(
        page=page,
        page_size=page_size,
        action_type=action_type,
        target_type=target_type,
        performed_by_id=performed_by_id,
        search=search,
        date_from=date_from,
        date_to=date_to,
        is_admin=is_admin_filter,
        action=action,
        date=parsed_date
    )
    
    # Calculate pagination
    total_pages = math.ceil(total / page_size) if total > 0 else 0
    
    # Convert to response format
    log_list = []
    for log in logs:
        # Determine if performer is admin (True) or moderator (False)
        is_admin_performer = log.is_admin == "admin"
        
        log_list.append(AuditLogResponse(
            id=str(log.id),
            timestamp=log.created_at,
            admin=log.performed_by_username,
            is_admin=is_admin_performer,
            action=log.action,
            target=log.target_identifier or log.target_id,
            target_type=log.target_type,
            action_type=log.action_type,
            details=log.details
        ))
    
    return AuditLogListResponse(
        logs=log_list,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )
