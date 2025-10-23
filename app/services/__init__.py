"""
Services package.

This package contains all business logic services organized by domain.
"""

from app.services.auth import AuthService
from app.services.email import EmailService, email_service

# Placeholder imports for future services
# from app.services.user_service import UserService
# from app.services.product_service import ProductService
# from app.services.order_service import OrderService

__all__ = [
    "AuthService",
    "EmailService",
    "email_service",
    # "UserService",
    # "ProductService", 
    # "OrderService",
]