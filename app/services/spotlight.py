"""
Spotlight service for business logic operations.

This module provides spotlight-related business logic including applying,
removing, tracking history, and automatic expiry.
"""

from typing import Optional, Dict, List
from datetime import datetime, timedelta, timezone
import math
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.spotlight import Spotlight, SpotlightHistory
from app.models.product import Product
from app.models.user import User
from app.services.audit_log import AuditLogService
from app.security import check_spotlight_permission, check_remove_spotlight_permission
from app.schemas.spotlight import (
    SpotlightResponse,
    ActiveSpotlightResponse,
    ActiveSpotlightListResponse,
    SpotlightHistoryResponse,
    SpotlightHistoryListResponse,
    SpotlightWithHistoryResponse,
    ProductSpotlightStatusResponse,
    SpotlightedProductResponse,
    FailedProductResponse
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
            action="active",
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
        spotlight.status = "expired"
        
        # Update product
        product.is_spotlighted = False
        product.spotlight_end_time = None
        
        # Create history entry
        history = SpotlightHistory(
            spotlight_id=spotlight.id,
            product_id=product_id,
            action="expired",
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
    
    def pause_spotlight(self, product_id: int, reason: str, admin_user_id: Optional[int] = None, auto_commit: bool = True) -> bool:
        """
        Pause spotlight for a product.
        
        Args:
            product_id: Product ID to pause spotlight for
            reason: Reason for pausing
            admin_user_id: ID of admin/moderator (optional)
            auto_commit: Whether to commit changes (default True)
            
        Returns:
            bool: True if paused, False otherwise
        """
        # Get active spotlight
        spotlight = self.db.query(Spotlight).filter(
            and_(
                Spotlight.product_id == product_id,
                Spotlight.status == "active"
            )
        ).first()
        
        if not spotlight:
            return False
            
        # Get product
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return False
            
        # Update spotlight status
        spotlight.status = "paused"
        
        # Update product
        product.is_spotlighted = False
        
        # Create history entry
        history = SpotlightHistory(
            spotlight_id=spotlight.id,
            product_id=product_id,
            action="paused",
            applied_by=spotlight.applied_by,
            removed_by=admin_user_id,
            start_time=spotlight.start_time,
            end_time=spotlight.end_time,
            duration_hours=spotlight.duration_hours
        )
        self.db.add(history)
        
        # Log to Audit Logs if admin_user_id provided
        if admin_user_id:
            try:
                audit_log = AuditLogService(self.db)
                audit_log.log_action(
                    performed_by_id=admin_user_id,
                    action="Spotlight status changed to Paused",
                    action_type="spotlight",
                    target_type="product",
                    target_id=str(product_id),
                    target_identifier=product.title,
                    details=f"Reason: {reason}"
                )
            except Exception as e:
                # Log error but don't fail the operation
                print(f"Failed to log audit action: {e}")
        
        if auto_commit:
            self.db.commit()
        return True

    def resume_spotlight(self, product_id: int, reason: str, admin_user_id: Optional[int] = None, auto_commit: bool = True) -> bool:
        """
        Resume a paused spotlight for a product.
        
        Args:
            product_id: Product ID to resume spotlight for
            reason: Reason for resuming
            admin_user_id: ID of admin/moderator (optional)
            auto_commit: Whether to commit changes (default True)
            
        Returns:
            bool: True if resumed, False otherwise
        """
        # Get paused spotlight
        spotlight = self.db.query(Spotlight).filter(
            and_(
                Spotlight.product_id == product_id,
                Spotlight.status == "paused"
            )
        ).first()
        
        if not spotlight:
            return False
            
        # Check if expired
        now = datetime.now(timezone.utc)
        if spotlight.end_time <= now:
            spotlight.status = "expired"
            self.db.commit()
            return False
            
        # Get product
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return False
            
        # Product must be verified and active to resume
        if not product.is_verified or not product.is_active:
            return False
            
        # Update spotlight status
        spotlight.status = "active"
        
        # Update product
        product.is_spotlighted = True
        
        # Create history entry
        history = SpotlightHistory(
            spotlight_id=spotlight.id,
            product_id=product_id,
            action="resumed",
            applied_by=spotlight.applied_by,
            removed_by=admin_user_id,
            start_time=spotlight.start_time,
            end_time=spotlight.end_time,
            duration_hours=spotlight.duration_hours
        )
        self.db.add(history)
        
        # Log to Audit Logs if admin_user_id provided
        if admin_user_id:
            try:
                audit_log = AuditLogService(self.db)
                audit_log.log_action(
                    performed_by_id=admin_user_id,
                    action="Spotlight status changed to Unpaused / Resumed",
                    action_type="spotlight",
                    target_type="product",
                    target_id=str(product_id),
                    target_identifier=product.title,
                    details=f"Reason: {reason}"
                )
            except Exception as e:
                # Log error but don't fail the operation
                print(f"Failed to log audit action: {e}")
        
        if auto_commit:
            self.db.commit()
        return True
    
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
        Returns spotlights (parent) with nested arrays of related products from spotlight_history (child).
        
        Args:
            page: Page number
            page_size: Items per page
            product_id: Filter by product ID (filters spotlights by product_id)
            status: Filter by spotlight status (active, expired, removed)
            date_from: Filter from date (filters by spotlight start_time)
            date_to: Filter to date (filters by spotlight end_time)
            
        Returns:
            SpotlightHistoryListResponse: Paginated spotlights with nested history entries
        """
        # Build query on Spotlight table (parent)
        query = self.db.query(Spotlight)
        
        # Apply filters to Spotlight table
        if product_id:
            query = query.filter(Spotlight.product_id == product_id)
        
        if status:
            query = query.filter(Spotlight.status == status)
        
        if date_from:
            query = query.filter(Spotlight.start_time >= date_from)
        
        if date_to:
            query = query.filter(Spotlight.end_time <= date_to)
        
        # Get total count
        total = query.count()
        
        # Calculate pagination
        offset = (page - 1) * page_size
        total_pages = math.ceil(total / page_size) if total > 0 else 0
        
        # Get paginated results
        spotlights = query.order_by(Spotlight.created_at.desc()).offset(offset).limit(page_size).all()
        
        # Build response with nested history entries
        spotlight_list = []
        for spotlight in spotlights:
            product = spotlight.product
            admin = spotlight.admin
            
            # Get related history entries for this spotlight
            history_entries = self.db.query(SpotlightHistory).filter(
                SpotlightHistory.spotlight_id == spotlight.id
            ).order_by(SpotlightHistory.created_at.desc()).all()
            
            # Build history entries list
            history_list = []
            for entry in history_entries:
                history_product = entry.product
                history_seller = history_product.owner
                applied_by_user = entry.applied_by_user
                removed_by_user = entry.removed_by_user if entry.removed_by else None
                
                history_list.append(SpotlightHistoryResponse(
                    id=str(entry.id),
                    spotlight_id=str(entry.spotlight_id) if entry.spotlight_id else None,
                    product_id=str(history_product.id),
                    product_title=history_product.title,
                    product_image=history_product.images[0] if history_product.images else None,
                    seller_username=history_seller.username,
                    action=entry.action,
                    applied_by_username=applied_by_user.username,
                    removed_by_username=removed_by_user.username if removed_by_user else None,
                    start_time=entry.start_time,
                    end_time=entry.end_time,
                    duration_hours=entry.duration_hours,
                    created_at=entry.created_at
                ))
            
            # Build spotlight with history response
            spotlight_list.append(SpotlightWithHistoryResponse(
                id=str(spotlight.id),
                product_id=str(product.id),
                product_title=product.title,
                product_image=product.images[0] if product.images else None,
                applied_by=str(spotlight.applied_by),
                applied_by_username=admin.username,
                start_time=spotlight.start_time,
                end_time=spotlight.end_time,
                duration_hours=spotlight.duration_hours,
                status=spotlight.status,
                created_at=spotlight.created_at,
                products=history_list
            ))
        
        return SpotlightHistoryListResponse(
            spotlights=spotlight_list,
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
    
    def bulk_spotlight_action(
        self,
        action: str,
        product_ids: List[int],
        admin_user_id: int,
        duration_hours: Optional[int] = None,
        custom_end_time: Optional[datetime] = None
    ) -> Dict:
        """
        Perform bulk spotlight action: add, edit, or remove.
        
        Args:
            action: Action to perform ('add', 'edit', or 'remove')
            product_ids: List of product IDs to process
            admin_user_id: Admin or moderator user ID performing the action
            duration_hours: Duration in hours (24, 72, or 168) - required for add/edit
            custom_end_time: Custom end time (overrides duration_hours) - required for add/edit
            
        Returns:
            dict: Response containing updated and failed products
            
        Raises:
            HTTPException: If validation fails or user doesn't have permission
        """
        # Validate action
        if action not in ['add', 'edit', 'remove']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid action. Must be one of: add, edit, remove"
            )
        
        # Check permissions based on action
        user = self.db.query(User).filter(User.id == admin_user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if action in ['add', 'edit']:
            if not check_spotlight_permission(user, self.db):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions: can_spotlight required"
                )
        elif action == 'remove':
            if not check_remove_spotlight_permission(user, self.db):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions: can_remove_spotlight required"
                )
        
        # Route to appropriate action handler
        if action == 'add':
            return self._bulk_add_spotlight(product_ids, admin_user_id, duration_hours, custom_end_time)
        elif action == 'edit':
            return self._bulk_edit_spotlight(product_ids, admin_user_id, duration_hours, custom_end_time)
        elif action == 'remove':
            return self._bulk_remove_spotlight(product_ids, admin_user_id)
    
    def _bulk_add_spotlight(
        self,
        product_ids: List[int],
        admin_user_id: int,
        duration_hours: Optional[int] = None,
        custom_end_time: Optional[datetime] = None
    ) -> Dict:
        """
        Apply spotlight to multiple products in bulk.
        
        Args:
            product_ids: List of product IDs to spotlight
            admin_user_id: Admin or moderator user ID applying the spotlight
            duration_hours: Duration in hours (24, 72, or 168)
            custom_end_time: Custom end time (overrides duration_hours)
            
        Returns:
            dict: Response containing spotlighted and failed products
        """
        # Validate input
        if not product_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="product_ids cannot be empty"
            )
        
        if len(product_ids) > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 100 products per request"
            )
        
        # Validate duration fields for add
        if custom_end_time is None and duration_hours is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either duration_hours or custom_end_time must be provided"
            )
        
        # Validate custom_end_time is in the future
        if custom_end_time:
            now = datetime.now(timezone.utc)
            if custom_end_time.tzinfo is None:
                custom_end_time = custom_end_time.replace(tzinfo=timezone.utc)
            if custom_end_time <= now:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Custom end time must be in the future"
                )
        
        # Validate duration_hours if provided
        if duration_hours is not None and duration_hours not in [24, 72, 168]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Duration must be 24, 72, or 168 hours"
            )
        
        # Check if all products exist
        products = self.db.query(Product).filter(Product.id.in_(product_ids)).all()
        found_product_ids = {product.id for product in products}
        not_found_ids = [pid for pid in product_ids if pid not in found_product_ids]
        
        if not_found_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Some products not found: {not_found_ids}",
                headers={"not_found_ids": str(not_found_ids)}
            )
        
        # Calculate start and end times
        start_time = datetime.now(timezone.utc)
        if custom_end_time:
            end_time = custom_end_time
            duration = int((end_time - start_time).total_seconds() / 3600)
        else:
            duration = duration_hours
            end_time = start_time + timedelta(hours=duration)
        
        # Process each product
        spotlighted_products = []
        failed_products = []
        
        for product in products:
            try:
                # Check if product is verified
                if not product.is_verified:
                    failed_products.append(FailedProductResponse(
                        product_id=product.id,
                        error="Product is not verified"
                    ))
                    continue
                
                # Check if product already has active spotlight
                existing_spotlight = self.db.query(Spotlight).filter(
                    Spotlight.product_id == product.id
                ).first()
                
                if existing_spotlight and existing_spotlight.status == "active":
                    failed_products.append(FailedProductResponse(
                        product_id=product.id,
                        error="Product is already in spotlight"
                    ))
                    continue
                
                # Reuse existing spotlight record if expired/removed, or create new one
                if existing_spotlight and existing_spotlight.status in ["expired", "removed"]:
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
                        product_id=product.id,
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
                    product_id=product.id,
                    action="active",
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
                
                # Add to successful list
                spotlighted_products.append(SpotlightedProductResponse(
                    product_id=product.id,
                    spotlight_id=spotlight.id,
                    start_time=start_time,
                    end_time=end_time,
                    status="active"
                ))
                
            except Exception as e:
                # Add this product to failed list
                failed_products.append(FailedProductResponse(
                    product_id=product.id,
                    error=str(e) if str(e) else "Unknown error occurred"
                ))
        
        # Commit all changes
        if spotlighted_products:
            self.db.commit()
        
        # Build response message
        success_count = len(spotlighted_products)
        failed_count = len(failed_products)
        
        if failed_count == 0:
            message = f"{success_count} product(s) added to spotlight successfully"
        else:
            message = f"{success_count} product(s) added to spotlight successfully, {failed_count} failed"
        
        # Determine status code
        if success_count == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Failed to add products to spotlight",
                headers={"error": "processing_error"}
            )
        
        response_data = {
            "spotlighted_products": [p.model_dump() for p in spotlighted_products],
            "failed_products": [p.model_dump() for p in failed_products]
        }
        
        return {
            "message": message,
            "success": True,
            "updated_count": success_count,
            "failed_count": failed_count,
            "failed_product_ids": [f.product_id for f in failed_products],
            "data": response_data
        }
    
    def _bulk_edit_spotlight(
        self,
        product_ids: List[int],
        admin_user_id: int,
        duration_hours: Optional[int] = None,
        custom_end_time: Optional[datetime] = None
    ) -> Dict:
        """
        Edit existing spotlights for multiple products in bulk.
        
        Args:
            product_ids: List of product IDs to edit
            admin_user_id: Admin or moderator user ID editing the spotlight
            duration_hours: Duration in hours (24, 72, or 168)
            custom_end_time: Custom end time (overrides duration_hours)
            
        Returns:
            dict: Response containing updated and failed products
        """
        # Check if all products exist
        products = self.db.query(Product).filter(Product.id.in_(product_ids)).all()
        found_product_ids = {product.id for product in products}
        not_found_ids = [pid for pid in product_ids if pid not in found_product_ids]
        
        if not_found_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Some products not found: {not_found_ids}",
                headers={"not_found_ids": str(not_found_ids)}
            )
        
        # Process each product
        updated_products = []
        failed_products = []
        
        for product in products:
            try:
                # Find existing active spotlight
                existing_spotlight = self.db.query(Spotlight).filter(
                    and_(
                        Spotlight.product_id == product.id,
                        Spotlight.status == "active"
                    )
                ).first()
                
                if not existing_spotlight:
                    failed_products.append(FailedProductResponse(
                        product_id=product.id,
                        error="Product does not have an active spotlight"
                    ))
                    continue
                
                # Preserve original start_time
                original_start_time = existing_spotlight.start_time
                
                # Calculate new end_time
                if custom_end_time:
                    new_end_time = custom_end_time
                    duration = int((new_end_time - original_start_time).total_seconds() / 3600)
                else:
                    duration = duration_hours
                    new_end_time = original_start_time + timedelta(hours=duration)
                
                # Update spotlight
                existing_spotlight.end_time = new_end_time
                existing_spotlight.duration_hours = duration
                existing_spotlight.updated_at = datetime.now(timezone.utc)
                
                # Update status if end_time is in past
                now = datetime.now(timezone.utc)
                if new_end_time <= now:
                    existing_spotlight.status = "expired"
                    product.is_spotlighted = False
                    product.spotlight_end_time = None
                else:
                    product.spotlight_end_time = new_end_time
                
                # Create history entry
                history = SpotlightHistory(
                    spotlight_id=existing_spotlight.id,
                    product_id=product.id,
                    action="edited",
                    applied_by=existing_spotlight.applied_by,
                    removed_by=None,
                    start_time=original_start_time,
                    end_time=new_end_time,
                    duration_hours=duration
                )
                self.db.add(history)
                
                updated_products.append(SpotlightedProductResponse(
                    product_id=product.id,
                    spotlight_id=existing_spotlight.id,
                    start_time=original_start_time,
                    end_time=new_end_time,
                    status=existing_spotlight.status
                ))
                
            except Exception as e:
                failed_products.append(FailedProductResponse(
                    product_id=product.id,
                    error=str(e) if str(e) else "Unknown error occurred"
                ))
        
        # Commit all changes
        if updated_products:
            self.db.commit()
        
        # Build response
        updated_count = len(updated_products)
        failed_count = len(failed_products)
        
        if failed_count == 0:
            message = f"{updated_count} spotlight(s) updated successfully"
        else:
            message = f"{updated_count} spotlight(s) updated successfully, {failed_count} failed"
        
        if updated_count == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Failed to update spotlights",
                headers={"error": "processing_error"}
            )
        
        response_data = {
            "updated_products": [p.model_dump() for p in updated_products],
            "failed_products": [p.model_dump() for p in failed_products]
        }
        
        return {
            "message": message,
            "success": True,
            "updated_count": updated_count,
            "failed_count": failed_count,
            "failed_product_ids": [f.product_id for f in failed_products],
            "data": response_data
        }
    
    def _bulk_remove_spotlight(
        self,
        product_ids: List[int],
        admin_user_id: int
    ) -> Dict:
        """
        Remove spotlights from multiple products in bulk (soft delete).
        
        Args:
            product_ids: List of product IDs to remove spotlight from
            admin_user_id: Admin or moderator user ID removing the spotlight
            
        Returns:
            dict: Response containing removed and failed products
        """
        # Check if all products exist
        products = self.db.query(Product).filter(Product.id.in_(product_ids)).all()
        found_product_ids = {product.id for product in products}
        not_found_ids = [pid for pid in product_ids if pid not in found_product_ids]
        
        if not_found_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Some products not found: {not_found_ids}",
                headers={"not_found_ids": str(not_found_ids)}
            )
        
        # Process each product
        removed_products = []
        failed_products = []
        now = datetime.now(timezone.utc)
        
        for product in products:
            try:
                # Find existing active spotlight
                existing_spotlight = self.db.query(Spotlight).filter(
                    and_(
                        Spotlight.product_id == product.id,
                        Spotlight.status == "active"
                    )
                ).first()
                
                if not existing_spotlight:
                    failed_products.append(FailedProductResponse(
                        product_id=product.id,
                        error="Product does not have an active spotlight"
                    ))
                    continue
                
                # Soft delete: mark as removed
                existing_spotlight.status = "removed"
                existing_spotlight.updated_at = now
                
                # Update product
                product.is_spotlighted = False
                product.spotlight_end_time = None
                
                # Create history entry
                history = SpotlightHistory(
                    spotlight_id=existing_spotlight.id,
                    product_id=product.id,
                    action="removed",
                    applied_by=existing_spotlight.applied_by,
                    removed_by=admin_user_id,
                    start_time=existing_spotlight.start_time,
                    end_time=existing_spotlight.end_time,
                    duration_hours=existing_spotlight.duration_hours
                )
                self.db.add(history)
                
                removed_products.append(SpotlightedProductResponse(
                    product_id=product.id,
                    spotlight_id=existing_spotlight.id,
                    start_time=existing_spotlight.start_time,
                    end_time=existing_spotlight.end_time,
                    status="removed"
                ))
                
            except Exception as e:
                failed_products.append(FailedProductResponse(
                    product_id=product.id,
                    error=str(e) if str(e) else "Unknown error occurred"
                ))
        
        # Commit all changes
        if removed_products:
            self.db.commit()
        
        # Build response
        removed_count = len(removed_products)
        failed_count = len(failed_products)
        
        if failed_count == 0:
            message = f"{removed_count} spotlight(s) removed successfully"
        else:
            message = f"{removed_count} spotlight(s) removed successfully, {failed_count} failed"
        
        if removed_count == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Failed to remove spotlights",
                headers={"error": "processing_error"}
            )
        
        response_data = {
            "removed_products": [p.model_dump() for p in removed_products],
            "failed_products": [p.model_dump() for p in failed_products]
        }
        
        return {
            "message": message,
            "success": True,
            "updated_count": removed_count,
            "failed_count": failed_count,
            "failed_product_ids": [f.product_id for f in failed_products],
            "data": response_data
        }

