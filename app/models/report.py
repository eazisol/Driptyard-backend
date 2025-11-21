"""
Report-related database models.

This module contains models for product reports and report statuses.
"""

from sqlalchemy import Column, String, Text, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.models.base import CategoryBaseModel, UserProductBaseModel


class ReportStatus(CategoryBaseModel):
    """Report status lookup table."""
    
    __tablename__ = "report_statuses"
    
    status = Column(String(50), nullable=False, unique=True, index=True)


class ProductReport(UserProductBaseModel):
    """Product report model for storing user reports on products."""
    
    __tablename__ = "product_reports"
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    user_email = Column(String(255), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    reason = Column(Text, nullable=False)
    status_id = Column(Integer, ForeignKey("report_statuses.id"), nullable=False, index=True)
    
    # Unique constraint: one report per user per product
    __table_args__ = (
        UniqueConstraint('user_id', 'product_id', name='uq_user_product_report'),
    )
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    product = relationship("Product", foreign_keys=[product_id])
    status = relationship("ReportStatus", foreign_keys=[status_id])

