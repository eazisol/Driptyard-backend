"""
Audit log service for logging admin and moderator actions.

This module provides functionality to log and retrieve audit trail information.
"""

from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from app.models.audit_log import AuditLog
from app.models.user import User


class AuditLogService:
    """Service class for audit log operations."""
    
    def __init__(self, db: Session):
        """
        Initialize audit log service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def log_action(
        self,
        performed_by_id: int,
        action: str,
        action_type: str,
        target_type: str,
        target_id: str,
        target_identifier: Optional[str] = None,
        details: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """
        Log an admin or moderator action.
        
        Args:
            performed_by_id: ID of the admin/moderator performing the action
            action: Action description (e.g., "Suspended User", "Removed Listing")
            action_type: Type of action category (user, product, spotlight, moderator, report)
            target_type: Type of target (user, product, spotlight, moderator)
            target_id: ID of the target (user_id, product_id, etc.)
            target_identifier: Human-readable identifier (username, product title, etc.)
            details: Additional context about the action
            ip_address: IP address of the requester
            user_agent: User agent string
            
        Returns:
            AuditLog: Created audit log entry
        """
        # Get user info
        user = self.db.query(User).filter(User.id == performed_by_id).first()
        if not user:
            raise ValueError(f"User with ID {performed_by_id} not found")
        
        # Determine if admin or moderator
        admin_type = "admin" if user.is_admin else "moderator"
        
        # Create audit log entry
        audit_log = AuditLog(
            performed_by_id=performed_by_id,
            performed_by_username=user.username,
            is_admin=admin_type,
            action=action,
            action_type=action_type,
            target_type=target_type,
            target_id=str(target_id),
            target_identifier=target_identifier,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.db.add(audit_log)
        self.db.commit()
        self.db.refresh(audit_log)
        
        return audit_log
    
    def get_audit_logs(
        self,
        page: int = 1,
        page_size: int = 10,
        action_type: Optional[str] = None,
        target_type: Optional[str] = None,
        performed_by_id: Optional[int] = None,
        search: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        is_admin: Optional[bool] = None,
        action: Optional[str] = None,
        date: Optional[datetime] = None
    ) -> tuple[list[AuditLog], int]:
        """
        Get paginated audit logs with filtering.
        
        Args:
            page: Page number (starts from 1)
            page_size: Items per page
            action_type: Filter by action type (user, product, spotlight, moderator, report)
            target_type: Filter by target type (user, product, spotlight, moderator)
            performed_by_id: Filter by admin/moderator ID
            search: Search in action, target_identifier, or performed_by_username
            date_from: Filter logs from this date
            date_to: Filter logs to this date
            is_admin: Filter by role (True for admin, False for moderator)
            action: Filter by specific action name (e.g., "Applied Spotlight", "Updated Listing")
            date: Filter by specific date (will filter logs on that date)
            
        Returns:
            tuple: (list of audit logs, total count)
        """
        query = self.db.query(AuditLog)
        
        # Apply filters
        if action_type:
            query = query.filter(AuditLog.action_type == action_type)
        
        if target_type:
            query = query.filter(AuditLog.target_type == target_type)
        
        if performed_by_id:
            query = query.filter(AuditLog.performed_by_id == performed_by_id)
        
        # Filter by role (admin or moderator)
        if is_admin is not None:
            if is_admin:
                query = query.filter(AuditLog.is_admin == "admin")
            else:
                query = query.filter(AuditLog.is_admin == "moderator")
        
        # Filter by specific action name
        if action:
            query = query.filter(AuditLog.action == action)
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    AuditLog.action.ilike(search_term),
                    AuditLog.target_identifier.ilike(search_term),
                    AuditLog.performed_by_username.ilike(search_term)
                )
            )
        
        # Filter by specific date (if provided, filter logs on that date)
        if date:
            # Set time range for the entire day
            date_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
            date_end = date_start + timedelta(days=1)
            query = query.filter(
                and_(
                    AuditLog.created_at >= date_start,
                    AuditLog.created_at < date_end
                )
            )
        else:
            # Use date_from and date_to if date is not provided
            if date_from:
                query = query.filter(AuditLog.created_at >= date_from)
            
            if date_to:
                query = query.filter(AuditLog.created_at <= date_to)
        
        # Get total count
        total = query.count()
        
        # Apply pagination and ordering
        offset = (page - 1) * page_size
        logs = query.order_by(desc(AuditLog.created_at)).offset(offset).limit(page_size).all()
        
        return logs, total

