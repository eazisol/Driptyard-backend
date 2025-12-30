"""
Product report service for business logic operations.

This module provides product report-related business logic including creating reports,
listing reported products, and managing report approvals/rejections.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import math
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc

from app.models.report import ReportStatus, ProductReport
from app.models.product import Product
from app.models.user import User
from app.schemas.report import (
    ProductReportResponse,
    ReportedProductResponse,
    ReportedProductListResponse,
    AdminReportDetailResponse,
    AdminReportListResponse,
    ProductReportListItem
)


class ProductReportService:
    """Service class for product report operations."""
    
    def __init__(self, db: Session):
        """
        Initialize product report service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def _get_status_by_name(self, status_name: str) -> ReportStatus:
        """
        Get report status by name.
        
        Args:
            status_name: Status name (pending, active, approved, rejected, processing, inactive)
            
        Returns:
            ReportStatus: Status object
            
        Raises:
            HTTPException: If status not found
        """
        status_obj = self.db.query(ReportStatus).filter(
            ReportStatus.status == status_name.lower()
        ).first()
        
        if not status_obj:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Report status '{status_name}' not found in database"
            )
        
        return status_obj
    
    def report_product(self, user_id: str, product_id: str, reason: str) -> ProductReportResponse:
        """
        Create a product report.
        
        Args:
            user_id: User ID reporting the product
            product_id: Product ID being reported
            reason: Reason for reporting
            
        Returns:
            ProductReportResponse: Created report details
            
        Raises:
            HTTPException: If product not found, user not found, or report already exists
        """
        # Validate and convert IDs
        try:
            user_id_int = int(user_id)
            product_id_int = int(product_id)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user or product ID format. Expected integer ID."
            )
        
        # Check if user exists
        user = self.db.query(User).filter(User.id == user_id_int).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if product exists
        product = self.db.query(Product).filter(Product.id == product_id_int).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        # Check if user already reported this product
        existing_report = self.db.query(ProductReport).filter(
            and_(
                ProductReport.user_id == user_id_int,
                ProductReport.product_id == product_id_int
            )
        ).first()
        
        if existing_report:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You have already reported this product"
            )
        
        # Get pending status
        pending_status = self._get_status_by_name("pending")
        
        # Create report
        report = ProductReport(
            user_id=user_id_int,
            user_email=user.email,
            product_id=product_id_int,
            reason=reason.strip(),
            status_id=pending_status.id
        )
        
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        
        return ProductReportResponse(
            id=str(report.id),
            user_id=str(report.user_id),
            user_email=report.user_email,
            product_id=str(report.product_id),
            reason=report.reason,
            status=pending_status.status,
            created_at=report.created_at
        )
    
    def get_reported_products(
        self,
        page: int,
        page_size: int,
        search: Optional[str] = None,
        status_filter: Optional[str] = None,
        product_id: Optional[str] = None,
        user_id: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> ReportedProductListResponse:
        """
        Get reported products listing (aggregated by product) with pagination, search, and filters.
        
        Args:
            page: Page number (starts from 1)
            page_size: Number of items per page
            search: Search term for product title or report reason
            status_filter: Filter by report status
            product_id: Filter by specific product ID
            user_id: Filter by reporting user ID
            date_from: Filter reports from this date
            date_to: Filter reports to this date
            
        Returns:
            ReportedProductListResponse: Paginated list of reported products
        """
        offset = (page - 1) * page_size
        
        # If search is provided, first get matching product IDs
        matching_product_ids = None
        if search:
            search_term = f"%{search}%"
            # Find product IDs that match search in title or reports that match search in reason
            # Join reports with products to search both title and reason
            matching_product_ids_query = self.db.query(ProductReport.product_id).join(
                Product, ProductReport.product_id == Product.id
            ).filter(
                or_(
                    Product.title.ilike(search_term),
                )
            ).distinct()
            
            matching_product_ids = [row[0] for row in matching_product_ids_query.all()]
            
            # If no matches, return empty result
            if not matching_product_ids:
                return ReportedProductListResponse(
                    reports=[],
                    total=0,
                    page=page,
                    page_size=page_size,
                    total_pages=0
                )
        
        # Base query: group by product_id and get counts
        first_reported_at = func.min(ProductReport.created_at).label('first_reported_at')
        query = self.db.query(
            ProductReport.product_id,
            func.count(ProductReport.id).label('report_count'),
            func.max(ProductReport.id).label('latest_report_id'),
            first_reported_at
        ).group_by(ProductReport.product_id)
        
        # Apply search filter by product IDs
        if matching_product_ids:
            query = query.filter(ProductReport.product_id.in_(matching_product_ids))
        
        # Apply filters
        if status_filter:
            status_obj = self.db.query(ReportStatus).filter(
                ReportStatus.status == status_filter.lower()
            ).first()
            if status_obj:
                query = query.filter(ProductReport.status_id == status_obj.id)
        
        if product_id:
            try:
                product_id_int = int(product_id)
                query = query.filter(ProductReport.product_id == product_id_int)
            except (ValueError, TypeError):
                pass
        
        if user_id:
            try:
                user_id_int = int(user_id)
                query = query.filter(ProductReport.user_id == user_id_int)
            except (ValueError, TypeError):
                pass
        
        if date_from:
            query = query.filter(ProductReport.created_at >= date_from)
        
        if date_to:
            query = query.filter(ProductReport.created_at <= date_to)
        
        # Get total count
        total = query.count()
        
        # Get paginated results - order by first reported date descending
        aggregated_results = query.order_by(desc(func.min(ProductReport.created_at))).offset(offset).limit(page_size).all()
        
        # Build response
        reported_products = []
        for agg_result in aggregated_results:
            product_id_int = agg_result.product_id
            
            # Get product details
            product = self.db.query(Product).filter(Product.id == product_id_int).first()
            if not product:
                continue
            
            # Get latest report details
            latest_report = self.db.query(ProductReport).filter(
                ProductReport.id == agg_result.latest_report_id
            ).first()
            
            if not latest_report:
                continue
            
            # Get status name for latest report
            status_obj = self.db.query(ReportStatus).filter(
                ReportStatus.id == latest_report.status_id
            ).first()
            status_name = status_obj.status if status_obj else "unknown"
            
            # Get all reports for this product (ordered by created_at descending)
            all_reports_query = self.db.query(ProductReport).filter(
                ProductReport.product_id == product_id_int
            )
            
            # Apply the same filters to all reports
            if status_filter:
                status_obj = self.db.query(ReportStatus).filter(
                    ReportStatus.status == status_filter.lower()
                ).first()
                if status_obj:
                    all_reports_query = all_reports_query.filter(ProductReport.status_id == status_obj.id)
            
            if user_id:
                try:
                    user_id_int = int(user_id)
                    all_reports_query = all_reports_query.filter(ProductReport.user_id == user_id_int)
                except (ValueError, TypeError):
                    pass
            
            if date_from:
                all_reports_query = all_reports_query.filter(ProductReport.created_at >= date_from)
            
            if date_to:
                all_reports_query = all_reports_query.filter(ProductReport.created_at <= date_to)
            
            all_reports = all_reports_query.order_by(desc(ProductReport.created_at)).all()
            
            # Build list of all reports
            reports_list = []
            for report in all_reports:
                # Get status name for each report
                report_status_obj = self.db.query(ReportStatus).filter(
                    ReportStatus.id == report.status_id
                ).first()
                report_status_name = report_status_obj.status if report_status_obj else "unknown"
                
                reports_list.append(ProductReportListItem(
                    id=str(report.id),
                    user_id=str(report.user_id),
                    user_email=report.user_email,
                    user_username=report.user.username if report.user else None,
                    reason=report.reason,
                    status=report_status_name,
                    created_at=report.created_at,
                    updated_at=report.updated_at
                ))
            
            reported_products.append(ReportedProductResponse(
                product_id=str(product_id_int),
                product_title=product.title,
                product_price=product.price,
                product_is_flagged=product.is_flagged,
                product_images=product.images or [],
                product_owner_id=str(product.owner_id),
                product_owner_username=product.owner.username if product.owner else None,
                product_is_active=product.is_active,
                report_count=agg_result.report_count,
                latest_report_id=str(latest_report.id),
                latest_report_user_id=str(latest_report.user_id),
                latest_report_user_username=latest_report.user.username if latest_report.user else None,
                latest_report_reason=latest_report.reason,
                latest_report_status=status_name,
                latest_report_created_at=latest_report.created_at,
                first_reported_at=agg_result.first_reported_at,
                all_reports=reports_list
            ))
        
        total_pages = math.ceil(total / page_size) if total > 0 else 0
        
        return ReportedProductListResponse(
            reports=reported_products,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    
    def get_all_reports(
        self,
        page: int,
        page_size: int,
        search: Optional[str] = None,
        status_filter: Optional[str] = None,
        product_id: Optional[str] = None,
        user_id: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> AdminReportListResponse:
        """
        Get all reports with pagination, search, and filters (detailed admin view).
        
        Args:
            page: Page number (starts from 1)
            page_size: Number of items per page
            search: Search term for product title or report reason
            status_filter: Filter by report status
            product_id: Filter by specific product ID
            user_id: Filter by reporting user ID
            date_from: Filter reports from this date
            date_to: Filter reports to this date
            
        Returns:
            AdminReportListResponse: Paginated list of all reports
        """
        offset = (page - 1) * page_size
        
        # Base query - join with Product for search
        query = self.db.query(ProductReport)
        
        # Apply search filter
        if search:
            search_term = f"%{search}%"
            query = query.join(Product, ProductReport.product_id == Product.id).filter(
                or_(
                    Product.title.ilike(search_term),
                    ProductReport.reason.ilike(search_term)
                )
            )
        
        # Apply filters
        if status_filter:
            status_obj = self.db.query(ReportStatus).filter(
                ReportStatus.status == status_filter.lower()
            ).first()
            if status_obj:
                query = query.filter(ProductReport.status_id == status_obj.id)
        
        if product_id:
            try:
                product_id_int = int(product_id)
                query = query.filter(ProductReport.product_id == product_id_int)
            except (ValueError, TypeError):
                pass
        
        if user_id:
            try:
                user_id_int = int(user_id)
                query = query.filter(ProductReport.user_id == user_id_int)
            except (ValueError, TypeError):
                pass
        
        if date_from:
            query = query.filter(ProductReport.created_at >= date_from)
        
        if date_to:
            query = query.filter(ProductReport.created_at <= date_to)
        
        # Get total count
        total = query.count()
        
        # Get paginated results
        reports = query.order_by(desc(ProductReport.created_at)).offset(offset).limit(page_size).all()
        
        # Build response
        report_list = []
        for report in reports:
            # Get product details
            product = self.db.query(Product).filter(Product.id == report.product_id).first()
            if not product:
                continue
            
            # Get status name
            status_obj = self.db.query(ReportStatus).filter(
                ReportStatus.id == report.status_id
            ).first()
            status_name = status_obj.status if status_obj else "unknown"
            
            report_list.append(AdminReportDetailResponse(
                id=str(report.id),
                user_id=str(report.user_id),
                user_email=report.user_email,
                product_id=str(report.product_id),
                product_title=product.title,
                product_price=product.price,
                product_images=product.images or [],
                reason=report.reason,
                status=status_name,
                created_at=report.created_at,
                updated_at=report.updated_at
            ))
        
        total_pages = math.ceil(total / page_size) if total > 0 else 0
        
        return AdminReportListResponse(
            reports=report_list,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    
    def approve_report(self, report_id: str) -> Dict[str, str]:
        """
        Approve a report and deactivate the product.
        Approves all reports for the same product, not just the single report.
        
        Args:
            report_id: Report ID to approve
            
        Returns:
            Dict[str, str]: Success message
            
        Raises:
            HTTPException: If report not found
        """
        try:
            report_id_int = int(report_id)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid report ID format. Expected integer ID."
            )
        
        # Get report
        report = self.db.query(ProductReport).filter(ProductReport.id == report_id_int).first()
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )
        
        # Get approved status
        approved_status = self._get_status_by_name("approved")
        
        # Get product ID
        product_id = report.product_id
        
        # Approve ALL reports for this product
        all_product_reports = self.db.query(ProductReport).filter(
            ProductReport.product_id == product_id
        ).all()
        
        for product_report in all_product_reports:
            product_report.status_id = approved_status.id
        
        self.db.flush()
        
        # Deactivate product
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if product:
            product.is_active = False
            product.is_flagged = 1
            self.db.flush()
        
        self.db.commit()
        
        return {"message": "All reports for this product approved and product deactivated"}
    
    def review_report(self, report_id: str) -> Dict[str, str]:
        """
        review again a reported product or approved product, it will make reported product live again.
        
        Args:
            report_id: Report ID to approve
            
        Returns:
            Dict[str, str]: Success message
            
        Raises:
            HTTPException: If report not found
        """
        try:
            report_id_int = int(report_id)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid report ID format. Expected integer ID."
            )
        
        # Get report
        report = self.db.query(ProductReport).filter(ProductReport.id == report_id_int).first()
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )
        
        # Get approved status
        approved_status = self._get_status_by_name("pending")
        
        # Update report status
        report.status_id = approved_status.id
        self.db.flush()
        
        # Reactivate product
        product = self.db.query(Product).filter(Product.id == report.product_id).first()
        if product:
            product.is_active = True
            product.is_flagged = 2
            self.db.flush()
        
        self.db.commit()
        
        return {"message": "Report reviewed and product is live again"}
    
    
    def reject_report(self, report_id: str) -> Dict[str, str]:
        """
        Reject a report (hard delete).
        
        Args:
            report_id: Report ID to reject/delete
            
        Returns:
            Dict[str, str]: Success message
            
        Raises:
            HTTPException: If report not found
        """
        try:
            report_id_int = int(report_id)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid report ID format. Expected integer ID."
            )
        
        # Get report
        report = self.db.query(ProductReport).filter(ProductReport.id == report_id_int).first()
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )
        
        # Hard delete the report
        self.db.delete(report)
        self.db.commit()
        
        return {"message": "Report rejected and deleted"}

