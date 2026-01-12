"""
Models package.

This package contains all SQLAlchemy database models organized by domain.
"""

from app.models.base import Base
from app.models.user import User, EmailVerification, RegistrationData
from app.models.category import (
    MainCategory,
    CategoryType,
    SubCategory,
    Brand,
    Gender
)
from app.models.report import ReportStatus, ProductReport
from app.models.follow import SellerFollow, ProductFollow
from app.models.audit_log import AuditLog
from app.models.search import UserRecentSearch, SearchAnalytics
from app.models.recent_view import RecentView

# Placeholder imports for future models
from app.models.product import Product
# from app.models.order import Order

__all__ = [
    "Base",
    "User", 
    "EmailVerification", 
    "RegistrationData",
    "MainCategory",
    "CategoryType",
    "SubCategory",
    "Brand",
    "Gender",
    "ReportStatus",
    "ProductReport",
    "SellerFollow",
    "ProductFollow",
    "AuditLog",
    "UserRecentSearch",
    "SearchAnalytics",
    "RecentView",
    "Product",
    # "Order",
]