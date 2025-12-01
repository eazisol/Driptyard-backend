"""
Follow management routes.

This module contains follow/unfollow endpoints for sellers and products.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.security import get_current_user_id
from app.schemas.follow import (
    FollowSellerResponse,
    FollowProductResponse,
    FollowedSellersListResponse,
    FollowedProductsListResponse,
    FollowStatusResponse
)
from app.services.follow import FollowService

router = APIRouter()


# Seller Follow Endpoints (Current User)

@router.post("/sellers/{seller_id}", response_model=FollowSellerResponse, status_code=status.HTTP_201_CREATED)
async def follow_seller(
    seller_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Follow a seller.
    
    Args:
        seller_id: ID of the seller to follow
        current_user_id: Current authenticated user ID
        db: Database session
        
    Returns:
        FollowSellerResponse: Follow relationship details
        
    Raises:
        HTTPException: If seller not found, self-follow attempt, or already following
    """
    try:
        follower_id = int(current_user_id)
        followed_user_id = int(seller_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    service = FollowService(db)
    return service.follow_seller(follower_id, followed_user_id)


@router.delete("/sellers/{seller_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unfollow_seller(
    seller_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Unfollow a seller.
    
    Args:
        seller_id: ID of the seller to unfollow
        current_user_id: Current authenticated user ID
        db: Database session
        
    Raises:
        HTTPException: If not following this seller
    """
    try:
        follower_id = int(current_user_id)
        followed_user_id = int(seller_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    service = FollowService(db)
    service.unfollow_seller(follower_id, followed_user_id)


@router.get("/sellers", response_model=FollowedSellersListResponse)
async def get_followed_sellers(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(12, ge=1, le=100, description="Items per page"),
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get list of sellers that the current user follows.
    
    Args:
        page: Page number (starts from 1)
        page_size: Number of items per page
        current_user_id: Current authenticated user ID
        db: Database session
        
    Returns:
        FollowedSellersListResponse: Paginated list of followed sellers
    """
    try:
        follower_id = int(current_user_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    service = FollowService(db)
    return service.get_followed_sellers(follower_id, page, page_size)


@router.get("/sellers/{seller_id}", response_model=FollowStatusResponse)
async def check_following_seller(
    seller_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Check if current user is following a seller.
    
    Args:
        seller_id: ID of the seller to check
        current_user_id: Current authenticated user ID
        db: Database session
        
    Returns:
        FollowStatusResponse: Follow status
    """
    try:
        follower_id = int(current_user_id)
        followed_user_id = int(seller_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    service = FollowService(db)
    is_following = service.is_following_seller(follower_id, followed_user_id)
    
    # Get follow ID if following
    follow_id = None
    if is_following:
        from app.models.follow import SellerFollow
        follow = db.query(SellerFollow).filter(
            SellerFollow.follower_id == follower_id,
            SellerFollow.followed_user_id == followed_user_id
        ).first()
        if follow:
            follow_id = str(follow.id)
    
    return FollowStatusResponse(
        is_following=is_following,
        follow_id=follow_id
    )


# Product Follow Endpoints (Current User)

@router.post("/products/{product_id}", response_model=FollowProductResponse, status_code=status.HTTP_201_CREATED)
async def follow_product(
    product_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Follow a product.
    
    Args:
        product_id: ID of the product to follow
        current_user_id: Current authenticated user ID
        db: Database session
        
    Returns:
        FollowProductResponse: Follow relationship details
        
    Raises:
        HTTPException: If product not found or already following
    """
    try:
        user_id = int(current_user_id)
        prod_id = int(product_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ID format"
        )
    
    service = FollowService(db)
    return service.follow_product(user_id, prod_id)


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unfollow_product(
    product_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Unfollow a product.
    
    Args:
        product_id: ID of the product to unfollow
        current_user_id: Current authenticated user ID
        db: Database session
        
    Raises:
        HTTPException: If not following this product
    """
    try:
        user_id = int(current_user_id)
        prod_id = int(product_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ID format"
        )
    
    service = FollowService(db)
    service.unfollow_product(user_id, prod_id)


@router.get("/products", response_model=FollowedProductsListResponse)
async def get_followed_products(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(12, ge=1, le=100, description="Items per page"),
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get list of products that the current user follows.
    
    Args:
        page: Page number (starts from 1)
        page_size: Number of items per page
        current_user_id: Current authenticated user ID
        db: Database session
        
    Returns:
        FollowedProductsListResponse: Paginated list of followed products
    """
    try:
        user_id = int(current_user_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    service = FollowService(db)
    return service.get_followed_products(user_id, page, page_size)


@router.get("/products/{product_id}", response_model=FollowStatusResponse)
async def check_following_product(
    product_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Check if current user is following a product.
    
    Args:
        product_id: ID of the product to check
        current_user_id: Current authenticated user ID
        db: Database session
        
    Returns:
        FollowStatusResponse: Follow status
    """
    try:
        user_id = int(current_user_id)
        prod_id = int(product_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ID format"
        )
    
    service = FollowService(db)
    is_following = service.is_following_product(user_id, prod_id)
    
    # Get follow ID if following
    follow_id = None
    if is_following:
        from app.models.follow import ProductFollow
        follow = db.query(ProductFollow).filter(
            ProductFollow.user_id == user_id,
            ProductFollow.product_id == prod_id
        ).first()
        if follow:
            follow_id = str(follow.id)
    
    return FollowStatusResponse(
        is_following=is_following,
        follow_id=follow_id
    )

