"""
Main API router for v1 endpoints.

This module aggregates all v1 API routers and provides the main
API router for the application.
"""

from fastapi import APIRouter

from app.api.v1 import auth, users, products, orders, payments, chat

# Create main API router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(orders.router, prefix="/orders", tags=["orders"])
api_router.include_router(payments.router, prefix="/payments", tags=["payments"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
