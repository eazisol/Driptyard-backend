"""
Admin management routes.

This module contains admin-only endpoints for managing the platform.
"""

from datetime import datetime, timedelta
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.database import get_db
from app.security import get_current_user_id
from app.models.user import User
from app.models.product import Product
from app.schemas.admin import StatsOverviewResponse

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

