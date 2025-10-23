"""
Schemas package.

This package contains all Pydantic schemas organized by domain.
"""

from app.schemas.user import UserBaseSchema, UserCreate, UserUpdate, UserResponse, UserPublicResponse
from app.schemas.auth import UserRegister, UserLogin, EmailVerificationRequest, RegistrationResponse, TokenResponse

# Placeholder imports for future schemas
# from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse
# from app.schemas.order import OrderCreate, OrderUpdate, OrderResponse

__all__ = [
    # User schemas
    "UserBaseSchema",
    "UserCreate",
    "UserUpdate", 
    "UserResponse",
    "UserPublicResponse",
    
    # Auth schemas
    "UserRegister",
    "UserLogin",
    "EmailVerificationRequest",
    "RegistrationResponse",
    "TokenResponse",
    
    # Future schemas
    # "ProductCreate",
    # "ProductUpdate", 
    # "ProductResponse",
    # "OrderCreate",
    # "OrderUpdate",
    # "OrderResponse",
]