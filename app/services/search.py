"""
Search service for business logic operations.

This module provides search-related business logic including search suggestions,
recent searches management, and popular searches.
"""

from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import or_, func, desc
import re

from app.models.product import Product
from app.models.user import User
from app.models.category import MainCategory, Brand
from app.models.search import UserRecentSearch, SearchAnalytics
from app.schemas.search import (
    ProductSearchResult,
    CategorySearchResult,
    BrandSearchResult,
    UserSearchResult,
    SearchSuggestionsResponse,
)


def generate_slug(text: str) -> str:
    """
    Generate a URL-friendly slug from text.
    
    Args:
        text: Text to convert to slug
        
    Returns:
        str: URL-friendly slug
    """
    # Convert to lowercase
    slug = text.lower()
    # Replace spaces and special characters with hyphens
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[-\s]+', '-', slug)
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    return slug


class SearchService:
    """Service class for search operations."""
    
    def __init__(self, db: Session):
        """
        Initialize search service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def get_search_suggestions(
        self,
        query: str,
        product_limit: int = 5,
        category_limit: int = 3,
        brand_limit: int = 3,
        user_limit: int = 3
    ) -> SearchSuggestionsResponse:
        """
        Get search suggestions across products, categories, brands, and users.
        
        Args:
            query: Search query string
            product_limit: Maximum number of products to return
            category_limit: Maximum number of categories to return
            brand_limit: Maximum number of brands to return
            user_limit: Maximum number of users to return
            
        Returns:
            SearchSuggestionsResponse: Search suggestions grouped by entity type
        """
        query_lower = query.lower().strip()
        
        if not query_lower:
            return SearchSuggestionsResponse()
        
        # Search products
        products = self._search_products(query_lower, product_limit)
        
        # Search categories
        categories = self._search_categories(query_lower, category_limit)
        
        # Search brands
        brands = self._search_brands(query_lower, brand_limit)
        
        # Search users
        users = self._search_users(query_lower, user_limit)
        
        return SearchSuggestionsResponse(
            products=products,
            categories=categories,
            brands=brands,
            users=users
        )
    
    def _search_products(self, query: str, limit: int) -> List[ProductSearchResult]:
        """Search products by title, description, or category."""
        # Build search filter
        # search_filter = or_(
        #     Product.title.ilike(f"%{query}%"),
        #     Product.description.ilike(f"%{query}%"),
        # )
        search_filter = Product.title.ilike(f"{query}%")
        
        # Query products (only active, not sold)
        products = self.db.query(Product).filter(
            search_filter,
            Product.is_active == True,
            Product.is_sold == False
        ).limit(limit).all()
        
        results = []
        for product in products:
            # Get first image from images JSON array
            image_url = None
            if product.images:
                if isinstance(product.images, list) and len(product.images) > 0:
                    image_url = product.images[0]
                elif isinstance(product.images, str):
                    # Try to parse as JSON string
                    try:
                        import json
                        images = json.loads(product.images)
                        if isinstance(images, list) and len(images) > 0:
                            image_url = images[0]
                    except:
                        pass
            
            # Get category name
            category_name = None
            if product.category:
                category_name = product.category.name
            
            results.append(ProductSearchResult(
                id=product.id,
                title=product.title,
                price=float(product.price),
                image=image_url,
                category=category_name,
                slug=generate_slug(product.title)
            ))
        
        return results
    
    def _search_categories(self, query: str, limit: int) -> List[CategorySearchResult]:
        """Search categories by name."""
        categories = self.db.query(MainCategory).filter(
            MainCategory.name.ilike(f"{query}%")
        ).limit(limit).all()
        
        results = []
        for category in categories:
            # Count products in category
            product_count = self.db.query(func.count(Product.id)).filter(
                Product.category_id == category.id,
                Product.is_active == True,
                Product.is_sold == False
            ).scalar() or 0
            
            results.append(CategorySearchResult(
                id=category.id,
                name=category.name,
                slug=generate_slug(category.name),
                product_count=product_count
            ))
        
        return results
    
    def _search_brands(self, query: str, limit: int) -> List[BrandSearchResult]:
        """Search brands by name."""
        brands = self.db.query(Brand).filter(
            Brand.name.ilike(f"{query}%"),
            Brand.active == True
        ).limit(limit).all()
        
        results = []
        for brand in brands:
            # Count products for this brand
            product_count = self.db.query(func.count(Product.id)).filter(
                Product.brand_id == brand.id,
                Product.is_active == True,
                Product.is_sold == False
            ).scalar() or 0
            
            results.append(BrandSearchResult(
                id=brand.id,
                name=brand.name,
                slug=generate_slug(brand.name),
                product_count=product_count
            ))
        
        return results
    
    def _search_users(self, query: str, limit: int) -> List[UserSearchResult]:
        """Search users by name or username."""
        # Build user display name from first_name and last_name
        users = self.db.query(User).filter(
            or_(
                User.first_name.ilike(f"{query}%"),
                User.last_name.ilike(f"{query}%"),
                func.concat(User.first_name, ' ', User.last_name).ilike(f"{query}%")
            ),
            User.is_active == True,
            User.is_suspended == False
        ).limit(limit).all()
        
        results = []
        for user in users:
            # Build display name
            name_parts = []
            if user.first_name:
                name_parts.append(user.first_name)
            if user.last_name:
                name_parts.append(user.last_name)
            display_name = ' '.join(name_parts) if name_parts else user.username
            
            results.append(UserSearchResult(
                id=user.id,
                name=display_name,
                username=user.username,
                avatar=user.avatar_url,
                is_verified=user.is_verified
            ))
        
        return results
    
    def get_recent_searches(self, user_id: int, limit: int = 10) -> List[str]:
        """
        Get user's recent searches.
        
        Args:
            user_id: User ID
            limit: Maximum number of searches to return
            
        Returns:
            List[str]: List of recent search queries
        """
        recent_searches = self.db.query(UserRecentSearch).filter(
            UserRecentSearch.user_id == user_id
        ).order_by(desc(UserRecentSearch.searched_at)).limit(limit).all()
        
        return [search.query for search in recent_searches]
    
    def save_recent_search(self, user_id: int, query: str) -> None:
        """
        Save a search query to user's recent searches.
        
        Args:
            user_id: User ID
            query: Search query to save
        """
        # Trim and normalize query
        query = query.strip()
        if not query:
            return
        
        # Check if search already exists for this user
        existing_search = self.db.query(UserRecentSearch).filter(
            UserRecentSearch.user_id == user_id,
            func.lower(UserRecentSearch.query) == query.lower()
        ).first()
        
        if existing_search:
            # Update searched_at timestamp
            existing_search.searched_at = datetime.utcnow()
            self.db.commit()
        else:
            # Create new recent search
            new_search = UserRecentSearch(
                user_id=user_id,
                query=query,
                searched_at=datetime.utcnow()
            )
            self.db.add(new_search)
            self.db.commit()
            
            # Maintain maximum of 10 recent searches
            self._limit_recent_searches(user_id, max_searches=10)
    
    def _limit_recent_searches(self, user_id: int, max_searches: int = 10) -> None:
        """
        Limit the number of recent searches for a user.
        
        Args:
            user_id: User ID
            max_searches: Maximum number of searches to keep
        """
        # Get count of recent searches
        count = self.db.query(func.count(UserRecentSearch.id)).filter(
            UserRecentSearch.user_id == user_id
        ).scalar()
        
        if count > max_searches:
            # Get IDs of oldest searches to delete
            oldest_searches = self.db.query(UserRecentSearch.id).filter(
                UserRecentSearch.user_id == user_id
            ).order_by(UserRecentSearch.searched_at).limit(count - max_searches).all()
            
            # Delete oldest searches
            for search_id_tuple in oldest_searches:
                self.db.query(UserRecentSearch).filter(
                    UserRecentSearch.id == search_id_tuple[0]
                ).delete()
            
            self.db.commit()
    
    def clear_recent_searches(self, user_id: int) -> None:
        """
        Clear all recent searches for a user.
        
        Args:
            user_id: User ID
        """
        self.db.query(UserRecentSearch).filter(
            UserRecentSearch.user_id == user_id
        ).delete()
        self.db.commit()
    
    def log_search_analytics(self, query: str, user_id: Optional[int] = None, result_count: Optional[int] = None) -> None:
        """
        Log a search query for analytics (popular searches).
        
        Args:
            query: Search query
            user_id: Optional user ID
            result_count: Optional result count
        """
        query = query.strip()
        if not query:
            return
        
        search_analytics = SearchAnalytics(
            query=query,
            user_id=user_id,
            result_count=result_count,
            searched_at=datetime.utcnow()
        )
        self.db.add(search_analytics)
        self.db.commit()
    
    def get_popular_searches(
        self,
        limit: int = 10,
        timeframe: str = "week"
    ) -> List[str]:
        """
        Get popular search queries.
        
        Args:
            limit: Maximum number of searches to return
            timeframe: Time period - "day", "week", or "month"
            
        Returns:
            List[str]: List of popular search queries
        """
        # Calculate time threshold based on timeframe
        now = datetime.utcnow()
        if timeframe == "day":
            threshold = now - timedelta(days=1)
        elif timeframe == "month":
            threshold = now - timedelta(days=30)
        else:  # default to week
            threshold = now - timedelta(days=7)
        
        # Query popular searches
        popular_searches = self.db.query(
            SearchAnalytics.query,
            func.count(SearchAnalytics.id).label('count')
        ).filter(
            SearchAnalytics.searched_at >= threshold
        ).group_by(
            SearchAnalytics.query
        ).order_by(
            desc('count')
        ).limit(limit).all()
        
        return [search[0] for search in popular_searches]

