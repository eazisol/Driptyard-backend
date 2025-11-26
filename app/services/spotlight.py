"""
Spotlight service for business logic operations.

This module provides spotlight-related business logic including applying,
removing, tracking history, and automatic expiry.
"""

from typing import Optional, Dict
from datetime import datetime, timedelta, timezone
import math
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.spotlight import Spotlight, SpotlightHistory
from app.models.product import Product
from app.models.user import User
from app.security import check_spotlight_permission, check_remove_spotlight_permission
from app.schemas.spotlight import (
    SpotlightResponse,
    ActiveSpotlightResponse,
    ActiveSpotlightListResponse,
    SpotlightHistoryResponse,
    SpotlightHistoryListResponse,
    ProductSpotlightStatusResponse
)


class SpotlightService:
    """Service class for spotlight operations."""
    
    def __init__(self, db: Session):
        """
        Initialize spotlight service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def apply_spotlight(
        self,
        product_id: int,
        admin_user_id: int,
        duration_hours: Optional[int] = None,
        custom_end_time: Optional[datetime] = None
    ) -> SpotlightResponse:
        """
        Apply spotlight to a product.
        
        Args:
            product_id: Product ID to spotlight
            admin_user_id: Admin or moderator user ID applying the spotlight
            duration_hours: Duration in hours (24, 72, or 168)
            custom_end_time: Custom end time (overrides duration_hours)
            
        Returns:
            SpotlightResponse: Spotlight details
            
        Raises:
            HTTPException: If validation fails or user doesn't have permission
        """
        # Check permissions
        user = self.db.query(User).filter(User.id == admin_user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if not check_spotlight_permission(user, self.db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to apply spotlight"
            )
        
        # Validate input
        if custom_end_time is None and duration_hours is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either duration_hours or custom_end_time must be provided"
            )
        
        # Get product
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        # Check if product is verified
        if not product.is_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only verified products can be spotlighted"
            )
        
        # Check if product has any existing spotlight record
        existing_spotlight = self.db.query(Spotlight).filter(
            Spotlight.product_id == product_id
        ).first()
        
        # If there's an active spotlight, reject
        if existing_spotlight and existing_spotlight.status == "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Product is already spotlighted"
            )
        
        # Calculate start and end times
        start_time = datetime.now(timezone.utc)
        if custom_end_time:
            # Ensure custom_end_time is timezone-aware
            if custom_end_time.tzinfo is None:
                custom_end_time = custom_end_time.replace(tzinfo=timezone.utc)
            end_time = custom_end_time
            duration = int((end_time - start_time).total_seconds() / 3600)
        else:
            duration = duration_hours
            end_time = start_time + timedelta(hours=duration)
        
        # Reuse existing spotlight record if expired/removed, or create new one
        if existing_spotlight and existing_spotlight.status in ["expired", "removed"]:
            # Reactivate the existing spotlight with new times
            spotlight = existing_spotlight
            spotlight.applied_by = admin_user_id
            spotlight.start_time = start_time
            spotlight.end_time = end_time
            spotlight.duration_hours = duration
            spotlight.status = "active"
            spotlight.updated_at = start_time
        else:
            # Create new spotlight record
            spotlight = Spotlight(
                product_id=product_id,
                applied_by=admin_user_id,
                start_time=start_time,
                end_time=end_time,
                duration_hours=duration,
                status="active"
            )
            self.db.add(spotlight)
        
        # Update product
        product.is_spotlighted = True
        product.spotlight_end_time = end_time
        
        # Create history entry
        history = SpotlightHistory(
            spotlight_id=None,  # Will be updated after flush
            product_id=product_id,
            action="applied",
            applied_by=admin_user_id,
            removed_by=None,
            start_time=start_time,
            end_time=end_time,
            duration_hours=duration
        )
        self.db.add(history)
        
        # Flush to get spotlight ID
        self.db.flush()
        history.spotlight_id = spotlight.id
        
        # Commit changes
        self.db.commit()
        self.db.refresh(spotlight)
        self.db.refresh(product)
        
        # Get admin user
        admin = self.db.query(User).filter(User.id == admin_user_id).first()
        
        # Build response
        return SpotlightResponse(
            id=str(spotlight.id),
            product_id=str(product.id),
            product_title=product.title,
            product_image=product.images[0] if product.images else None,
            applied_by=str(admin.id),
            applied_by_username=admin.username,
            start_time=spotlight.start_time,
            end_time=spotlight.end_time,
            duration_hours=spotlight.duration_hours,
            status=spotlight.status,
            created_at=spotlight.created_at
        )
    
    def remove_spotlight(self, product_id: int, admin_user_id: int) -> Dict[str, str]:
        """
        Remove spotlight from a product.
        
        Args:
            product_id: Product ID to remove spotlight from
            admin_user_id: Admin or moderator user ID removing the spotlight
            
        Returns:
            dict: Success message
            
        Raises:
            HTTPException: If validation fails or user doesn't have permission
        """
        # Check permissions
        user = self.db.query(User).filter(User.id == admin_user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if not check_remove_spotlight_permission(user, self.db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to remove spotlight"
            )
        
        # Get active spotlight
        spotlight = self.db.query(Spotlight).filter(
            and_(
                Spotlight.product_id == product_id,
                Spotlight.status == "active"
            )
        ).first()
        
        if not spotlight:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active spotlight found for this product"
            )
        
        # Get product
        product = self.db.query(Product).filter(Product.id == product_id).first()
        
        # Update spotlight status
        spotlight.status = "removed"
        
        # Update product
        product.is_spotlighted = False
        product.spotlight_end_time = None
        
        # Create history entry
        history = SpotlightHistory(
            spotlight_id=spotlight.id,
            product_id=product_id,
            action="removed",
            applied_by=spotlight.applied_by,
            removed_by=admin_user_id,
            start_time=spotlight.start_time,
            end_time=spotlight.end_time,
            duration_hours=spotlight.duration_hours
        )
        self.db.add(history)
        
        # Commit changes
        self.db.commit()
        
        return {"message": "Spotlight removed successfully"}
    
    def get_active_spotlights(
        self,
        page: int = 1,
        page_size: int = 10
    ) -> ActiveSpotlightListResponse:
        """
        Get active spotlights with pagination.
        
        Args:
            page: Page number
            page_size: Items per page
            
        Returns:
            ActiveSpotlightListResponse: Paginated active spotlights
        """
        # Query active spotlights
        query = self.db.query(Spotlight).filter(Spotlight.status == "active")
        
        # Get total count
        total = query.count()
        
        # Calculate pagination
        offset = (page - 1) * page_size
        total_pages = math.ceil(total / page_size) if total > 0 else 0
        
        # Get paginated results
        spotlights = query.order_by(Spotlight.created_at.desc()).offset(offset).limit(page_size).all()
        
        # Build response
        spotlight_list = []
        for spotlight in spotlights:
            product = spotlight.product
            seller = product.owner
            admin = spotlight.admin
            
            spotlight_list.append(ActiveSpotlightResponse(
                id=str(spotlight.id),
                product_id=str(product.id),
                product_title=product.title,
                product_price=product.price,
                product_image=product.images[0] if product.images else None,
                seller_username=seller.username,
                applied_by_username=admin.username,
                start_time=spotlight.start_time,
                end_time=spotlight.end_time,
                duration_hours=spotlight.duration_hours,
                created_at=spotlight.created_at
            ))
        
        return ActiveSpotlightListResponse(
            spotlights=spotlight_list,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    
    def get_spotlight_history(
        self,
        page: int = 1,
        page_size: int = 10,
        product_id: Optional[int] = None,
        status: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> SpotlightHistoryListResponse:
        """
        Get spotlight history with filters and pagination.
        
        Args:
            page: Page number
            page_size: Items per page
            product_id: Filter by product ID
            status: Filter by action (applied, expired, removed)
            date_from: Filter from date
            date_to: Filter to date
            
        Returns:
            SpotlightHistoryListResponse: Paginated history entries
        """
        # Build query
        query = self.db.query(SpotlightHistory)
        
        # Apply filters
        if product_id:
            query = query.filter(SpotlightHistory.product_id == product_id)
        
        if status:
            query = query.filter(SpotlightHistory.action == status)
        
        if date_from:
            query = query.filter(SpotlightHistory.created_at >= date_from)
        
        if date_to:
            query = query.filter(SpotlightHistory.created_at <= date_to)
        
        # Get total count
        total = query.count()
        
        # Calculate pagination
        offset = (page - 1) * page_size
        total_pages = math.ceil(total / page_size) if total > 0 else 0
        
        # Get paginated results
        history_entries = query.order_by(SpotlightHistory.created_at.desc()).offset(offset).limit(page_size).all()
        
        # Build response
        history_list = []
        for entry in history_entries:
            product = entry.product
            seller = product.owner
            applied_by_user = entry.applied_by_user
            removed_by_user = entry.removed_by_user if entry.removed_by else None
            
            history_list.append(SpotlightHistoryResponse(
                id=str(entry.id),
                spotlight_id=str(entry.spotlight_id) if entry.spotlight_id else None,
                product_id=str(product.id),
                product_title=product.title,
                product_image=product.images[0] if product.images else None,
                seller_username=seller.username,
                action=entry.action,
                applied_by_username=applied_by_user.username,
                removed_by_username=removed_by_user.username if removed_by_user else None,
                start_time=entry.start_time,
                end_time=entry.end_time,
                duration_hours=entry.duration_hours,
                created_at=entry.created_at
            ))
        
        return SpotlightHistoryListResponse(
            history=history_list,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    
    def check_and_expire_spotlights(self) -> int:
        """
        Check for expired spotlights and update them.
        
        Returns:
            int: Number of spotlights expired
        """
        now = datetime.now(timezone.utc)
        
        # Find active spotlights that have expired
        expired_spotlights = self.db.query(Spotlight).filter(
            and_(
                Spotlight.status == "active",
                Spotlight.end_time <= now
            )
        ).all()
        
        count = 0
        for spotlight in expired_spotlights:
            # Update spotlight status
            spotlight.status = "expired"
            
            # Get product
            product = self.db.query(Product).filter(Product.id == spotlight.product_id).first()
            if product:
                # Update product
                product.is_spotlighted = False
                product.spotlight_end_time = None
            
            # Create history entry
            history = SpotlightHistory(
                spotlight_id=spotlight.id,
                product_id=spotlight.product_id,
                action="expired",
                applied_by=spotlight.applied_by,
                removed_by=None,
                start_time=spotlight.start_time,
                end_time=spotlight.end_time,
                duration_hours=spotlight.duration_hours
            )
            self.db.add(history)
            count += 1
        
        if count > 0:
            self.db.commit()
        
        return count
    
    def get_product_spotlight_status(self, product_id: int) -> 'ProductSpotlightStatusResponse':
        """
        Get spotlight status for a specific product.
        
        Args:
            product_id: Product ID to check
            
        Returns:
            ProductSpotlightStatusResponse: Spotlight status and details
            
        Raises:
            HTTPException: If product not found
        """
        # Check and expire any spotlights first
        self.check_and_expire_spotlights()
        
        # Get product
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        # Check if product has active spotlight
        spotlight = self.db.query(Spotlight).filter(
            and_(
                Spotlight.product_id == product_id,
                Spotlight.status == "active"
            )
        ).first()
        
        # Build response
        spotlight_response = None
        if spotlight:
            admin = spotlight.admin
            spotlight_response = SpotlightResponse(
                id=str(spotlight.id),
                product_id=str(product.id),
                product_title=product.title,
                product_image=product.images[0] if product.images else None,
                applied_by=str(admin.id),
                applied_by_username=admin.username,
                start_time=spotlight.start_time,
                end_time=spotlight.end_time,
                duration_hours=spotlight.duration_hours,
                status=spotlight.status,
                created_at=spotlight.created_at
            )
        
        return ProductSpotlightStatusResponse(
            product_id=str(product.id),
            is_spotlighted=product.is_spotlighted and spotlight is not None,
            spotlight=spotlight_response,
            spotlight_end_time=product.spotlight_end_time
        )

