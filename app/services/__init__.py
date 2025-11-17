"""
Services package.

This package contains all business logic services organized by domain.
"""

from app.services.auth import AuthService
from app.services.email import EmailService, email_service
from app.services.product import ProductService
from app.services.user import UserService

# Placeholder imports for future services
# from app.services.order_service import OrderService

__all__ = [
    "AuthService",
    "EmailService",
    "email_service",
    "ProductService",
    "UserService",
    # "OrderService",
]