"""
Follow service for business logic operations.

This module provides follow-related business logic including follow/unfollow operations,
validation, and data transformations.
"""

from typing import Optional
import math
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.follow import SellerFollow, ProductFollow
from app.models.user import User
from app.models.product import Product
from app.schemas.follow import (
    FollowSellerResponse,
    FollowProductResponse,
    FollowedSellerResponse,
    FollowedProductResponse,
    FollowedProductsListResponse,
    FollowedSellersListResponse,
    FollowStatusResponse
)
from app.schemas.product import SellerInfo, ProductListResponse


class FollowService:
    """Service class for follow operations."""
    
    def __init__(self, db: Session):
        """
        Initialize follow service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def _get_seller_info(self, user: User, is_followed: bool = False) -> SellerInfo:
        """Helper function to extract seller information."""
        return SellerInfo(
            id=str(user.id),
            username=user.username,
            rating=4.8,  # TODO: Calculate from reviews
            total_sales=156,  # TODO: Get from orders
            avatar_url=user.avatar_url,
            is_verified=user.is_verified,
            bio=user.bio,
            is_followed=is_followed
        )
    
    def _product_to_list_response(self, product: Product, seller: User, user_id: Optional[int] = None, is_followed: bool = False) -> ProductListResponse:
        """Convert Product model to ProductListResponse."""
        # Check if user is following the seller
        seller_is_followed = False
        if user_id:
            seller_is_followed = self.is_following_seller(user_id, seller.id)
        
        return ProductListResponse(
            id=str(product.id),
            title=product.title,
            description=product.description[:150] + "..." if product.description and len(product.description) > 150 else product.description,
            price=product.price,
            condition=product.condition,
            images=product.images or [],
            rating=product.rating,
            review_count=product.review_count,
            stock_status=product.stock_status,
            deal_method=product.deal_method,
            product_type=str(product.product_type_id) if product.product_type_id else None,
            product_style=product.product_style,
            colors=product.colors or [],
            purchase_button_enabled=product.purchase_button_enabled,
            seller=self._get_seller_info(seller, is_followed=seller_is_followed),
            created_at=product.created_at,
            is_active=product.is_active,
            is_spotlighted=product.is_spotlighted,
            is_verified=product.is_verified,
            is_followed=is_followed
        )
    
    # Seller Follow Methods
    
    def follow_seller(self, follower_id: int, followed_user_id: int) -> FollowSellerResponse:
        """
        Follow a seller.
        
        Args:
            follower_id: ID of the user who is following
            followed_user_id: ID of the user being followed
            
        Returns:
            FollowSellerResponse: Follow relationship details
            
        Raises:
            HTTPException: If self-follow attempt, user not found, or duplicate follow
        """
        # Prevent self-follow
        if follower_id == followed_user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot follow yourself"
            )
        
        # Validate users exist
        follower = self.db.query(User).filter(User.id == follower_id).first()
        if not follower:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Follower user not found"
            )
        
        followed_user = self.db.query(User).filter(User.id == followed_user_id).first()
        if not followed_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User to follow not found"
            )
        
        # Check if already following
        existing_follow = self.db.query(SellerFollow).filter(
            SellerFollow.follower_id == follower_id,
            SellerFollow.followed_user_id == followed_user_id
        ).first()
        
        if existing_follow:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Already following this seller"
            )
        
        # Create follow relationship
        follow = SellerFollow(
            follower_id=follower_id,
            followed_user_id=followed_user_id
        )
        self.db.add(follow)
        self.db.commit()
        self.db.refresh(follow)
        
        # Since we just created the follow, we know the user is following
        return FollowSellerResponse(
            id=str(follow.id),
            follower_id=str(follow.follower_id),
            followed_user_id=str(follow.followed_user_id),
            seller=self._get_seller_info(followed_user, is_followed=True),
            created_at=follow.created_at
        )
    
    def unfollow_seller(self, follower_id: int, followed_user_id: int) -> None:
        """
        Unfollow a seller.
        
        Args:
            follower_id: ID of the user who is unfollowing
            followed_user_id: ID of the user being unfollowed
            
        Raises:
            HTTPException: If follow relationship not found
        """
        follow = self.db.query(SellerFollow).filter(
            SellerFollow.follower_id == follower_id,
            SellerFollow.followed_user_id == followed_user_id
        ).first()
        
        if not follow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Not following this seller"
            )
        
        self.db.delete(follow)
        self.db.commit()
    
    def is_following_seller(self, follower_id: int, followed_user_id: int) -> bool:
        """
        Check if a user is following a seller.
        
        Args:
            follower_id: ID of the user to check
            followed_user_id: ID of the seller to check
            
        Returns:
            bool: True if following, False otherwise
        """
        follow = self.db.query(SellerFollow).filter(
            SellerFollow.follower_id == follower_id,
            SellerFollow.followed_user_id == followed_user_id
        ).first()
        
        return follow is not None
    
    def get_followed_sellers(self, follower_id: int, page: int, page_size: int) -> FollowedSellersListResponse:
        """
        Get paginated list of sellers followed by a user.
        
        Args:
            follower_id: ID of the user
            page: Page number (starts from 1)
            page_size: Number of items per page
            
        Returns:
            FollowedSellersListResponse: Paginated list of followed sellers
        """
        offset = (page - 1) * page_size
        
        # Query follows with joined user data
        query = self.db.query(SellerFollow).filter(
            SellerFollow.follower_id == follower_id
        ).order_by(SellerFollow.created_at.desc())
        
        total = query.count()
        follows = query.offset(offset).limit(page_size).all()
        
        sellers = []
        for follow in follows:
            followed_user = self.db.query(User).filter(User.id == follow.followed_user_id).first()
            if followed_user:
                # These are followed sellers, so is_followed should be True
                sellers.append(FollowedSellerResponse(
                    id=str(follow.id),
                    seller=self._get_seller_info(followed_user, is_followed=True),
                    followed_at=follow.created_at
                ))
        
        total_pages = math.ceil(total / page_size) if total > 0 else 0
        
        return FollowedSellersListResponse(
            sellers=sellers,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    
    def get_user_followed_sellers(self, user_id: int, page: int, page_size: int) -> FollowedSellersListResponse:
        """
        Get paginated list of sellers followed by any user (public endpoint).
        
        Args:
            user_id: ID of the user
            page: Page number (starts from 1)
            page_size: Number of items per page
            
        Returns:
            FollowedSellersListResponse: Paginated list of followed sellers
            
        Raises:
            HTTPException: If user not found
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return self.get_followed_sellers(user_id, page, page_size)
    
    def get_seller_followers_count(self, followed_user_id: int) -> int:
        """
        Get count of followers for a seller.
        
        Args:
            followed_user_id: ID of the seller
            
        Returns:
            int: Number of followers
        """
        return self.db.query(SellerFollow).filter(
            SellerFollow.followed_user_id == followed_user_id
        ).count()
    
    def get_seller_following_count(self, follower_id: int) -> int:
        """
        Get count of sellers a user is following.
        
        Args:
            follower_id: ID of the user
            
        Returns:
            int: Number of sellers being followed
        """
        return self.db.query(SellerFollow).filter(
            SellerFollow.follower_id == follower_id
        ).count()
    
    # Product Follow Methods
    
    def follow_product(self, user_id: int, product_id: int) -> FollowProductResponse:
        """
        Follow a product.
        
        Args:
            user_id: ID of the user who is following
            product_id: ID of the product being followed
            
        Returns:
            FollowProductResponse: Follow relationship details
            
        Raises:
            HTTPException: If user/product not found or duplicate follow
        """
        # Validate user exists
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Validate product exists
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        # Check if already following
        existing_follow = self.db.query(ProductFollow).filter(
            ProductFollow.user_id == user_id,
            ProductFollow.product_id == product_id
        ).first()
        
        if existing_follow:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Already following this product"
            )
        
        # Create follow relationship
        follow = ProductFollow(
            user_id=user_id,
            product_id=product_id
        )
        self.db.add(follow)
        self.db.commit()
        self.db.refresh(follow)
        
        # Get seller info
        seller = self.db.query(User).filter(User.id == product.owner_id).first()
        if not seller:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product owner not found"
            )
        
        # Since we just created the follow, we know the user is following the product
        return FollowProductResponse(
            id=str(follow.id),
            user_id=str(follow.user_id),
            product_id=str(follow.product_id),
            product=self._product_to_list_response(product, seller, user_id=user_id, is_followed=True),
            created_at=follow.created_at
        )
    
    def unfollow_product(self, user_id: int, product_id: int) -> None:
        """
        Unfollow a product.
        
        Args:
            user_id: ID of the user who is unfollowing
            product_id: ID of the product being unfollowed
            
        Raises:
            HTTPException: If follow relationship not found
        """
        follow = self.db.query(ProductFollow).filter(
            ProductFollow.user_id == user_id,
            ProductFollow.product_id == product_id
        ).first()
        
        if not follow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Not following this product"
            )
        
        self.db.delete(follow)
        self.db.commit()
    
    def is_following_product(self, user_id: int, product_id: int) -> bool:
        """
        Check if a user is following a product.
        
        Args:
            user_id: ID of the user to check
            product_id: ID of the product to check
            
        Returns:
            bool: True if following, False otherwise
        """
        follow = self.db.query(ProductFollow).filter(
            ProductFollow.user_id == user_id,
            ProductFollow.product_id == product_id
        ).first()
        
        return follow is not None
    
    def get_followed_products(self, user_id: int, page: int, page_size: int) -> FollowedProductsListResponse:
        """
        Get paginated list of products followed by a user.
        
        Args:
            user_id: ID of the user
            page: Page number (starts from 1)
            page_size: Number of items per page
            
        Returns:
            FollowedProductsListResponse: Paginated list of followed products
        """
        offset = (page - 1) * page_size
        
        # Query follows with joined product data
        query = self.db.query(ProductFollow).filter(
            ProductFollow.user_id == user_id
        ).order_by(ProductFollow.created_at.desc())
        
        total = query.count()
        follows = query.offset(offset).limit(page_size).all()
        
        products = []
        for follow in follows:
            product = self.db.query(Product).filter(Product.id == follow.product_id).first()
            if product:
                seller = self.db.query(User).filter(User.id == product.owner_id).first()
                if seller:
                    # These are followed products, so is_followed should be True
                    products.append({
                        'id': str(follow.id),
                        'product': self._product_to_list_response(product, seller, user_id=user_id, is_followed=True),
                        'followed_at': follow.created_at
                    })
        
        # Convert to FollowedProductResponse objects
        followed_products = [
            {
                'id': p['id'],
                'product': p['product'],
                'followed_at': p['followed_at']
            }
            for p in products
        ]
        
        total_pages = math.ceil(total / page_size) if total > 0 else 0
        
        # Create response objects manually since we can't use from_attributes
        response_items = [
            FollowedProductResponse(
                id=p['id'],
                product=p['product'],
                followed_at=p['followed_at']
            )
            for p in followed_products
        ]
        
        return FollowedProductsListResponse(
            products=response_items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    
    def get_user_followed_products(self, user_id: int, page: int, page_size: int) -> FollowedProductsListResponse:
        """
        Get paginated list of products followed by any user (public endpoint).
        
        Args:
            user_id: ID of the user
            page: Page number (starts from 1)
            page_size: Number of items per page
            
        Returns:
            FollowedProductsListResponse: Paginated list of followed products
            
        Raises:
            HTTPException: If user not found
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return self.get_followed_products(user_id, page, page_size)
    
    def get_product_followers_count(self, product_id: int) -> int:
        """
        Get count of followers for a product.
        
        Args:
            product_id: ID of the product
            
        Returns:
            int: Number of followers
        """
        return self.db.query(ProductFollow).filter(
            ProductFollow.product_id == product_id
        ).count()

