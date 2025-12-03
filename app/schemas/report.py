"""
Report-related Pydantic schemas.

This module contains all report-related request and response schemas.
"""

from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field


class ProductReportRequest(BaseModel):
    """Schema for reporting a product."""
    
    reason: str = Field(..., min_length=1, description="Reason for reporting the product")


class ProductReportResponse(BaseModel):
    """Schema for product report response."""
    
    id: str = Field(..., description="Report ID")
    user_id: str = Field(..., description="User ID who reported")
    user_email: str = Field(..., description="User email who reported")
    product_id: str = Field(..., description="Product ID that was reported")
    reason: str = Field(..., description="Reason for the report")
    status: str = Field(..., description="Report status")
    created_at: datetime = Field(..., description="Report creation timestamp")
    
    class Config:
        from_attributes = True


class ReportedProductResponse(BaseModel):
    """Schema for reported product in admin listing (aggregated by product)."""
    
    product_id: str = Field(..., description="Product ID")
    product_title: str = Field(..., description="Product title")
    product_price: Decimal = Field(..., description="Product price")
    product_images: List[str] = Field(default_factory=list, description="Product images")
    product_owner_id: str = Field(..., description="Product owner ID")
    product_is_active: bool = Field(..., description="Whether product is currently active")
    report_count: int = Field(..., description="Total number of reports for this product")
    latest_report_id: str = Field(..., description="ID of the most recent report")
    latest_report_reason: str = Field(..., description="Reason from the most recent report")
    latest_report_status: str = Field(..., description="Status of the most recent report")
    latest_report_created_at: datetime = Field(..., description="Creation time of the most recent report")
    first_reported_at: datetime = Field(..., description="When the product was first reported")
    latest_report_user_id: Optional[str] = Field(None, description="User ID who made the latest report")
    latest_report_user_username: Optional[str] = Field(None, description="Username who made the latest report")
    product_owner_username: Optional[str] = Field(None, description="Username of the product owner")

class ReportedProductListResponse(BaseModel):
    """Schema for paginated list of reported products."""
    
    reports: List[ReportedProductResponse] = Field(..., description="List of reported products")
    total: int = Field(..., description="Total number of reported products")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")
    
    class Config:
        from_attributes = True


class AdminReportDetailResponse(BaseModel):
    """Schema for detailed report information in admin listing."""
    
    id: str = Field(..., description="Report ID")
    user_id: str = Field(..., description="User ID who reported")
    user_email: str = Field(..., description="User email who reported")
    product_id: str = Field(..., description="Product ID that was reported")
    product_title: str = Field(..., description="Product title")
    product_price: Decimal = Field(..., description="Product price")
    product_images: List[str] = Field(default_factory=list, description="Product images")
    reason: str = Field(..., description="Reason for the report")
    status: str = Field(..., description="Report status")
    created_at: datetime = Field(..., description="Report creation timestamp")
    updated_at: datetime = Field(..., description="Report last update timestamp")
    
    class Config:
        from_attributes = True


class AdminReportListResponse(BaseModel):
    """Schema for paginated list of all reports (admin view)."""
    
    reports: List[AdminReportDetailResponse] = Field(..., description="List of reports")
    total: int = Field(..., description="Total number of reports")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")
    
    class Config:
        from_attributes = True

