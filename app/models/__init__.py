"""
Models package.

This package contains all SQLAlchemy database models organized by domain.
"""

from app.models.base import Base
from app.models.user import User, EmailVerification, RegistrationData

# Placeholder imports for future models
# from app.models.product import Product
# from app.models.order import Order

__all__ = [
    "Base",
    "User", 
    "EmailVerification", 
    "RegistrationData",
    # "Product",
    # "Order",
]