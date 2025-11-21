"""
Product service for business logic operations.

This module provides product-related business logic including CRUD operations,
validation, verification, and data transformations.
"""

from typing import Optional, List, Any, Dict, Tuple
from typing import Union
from decimal import Decimal, InvalidOperation
from datetime import datetime, timedelta
import random
import string
import json
import math
from urllib.parse import urlparse
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func, case
from sqlalchemy.dialects.postgresql import JSONB

from app.database import settings
from app.models.product import Product
from app.models.user import User
from app.models.category import (
    MainCategory,
    CategoryType,
    SubCategory,
    Brand,
    Gender
)
from app.schemas.product import (
    ProductListResponse,
    ProductDetailResponse,
    ProductPaginationResponse,
    SellerInfo,
    ProductVerificationRequest,
    ProductUpdate
)
from app.services.s3 import get_s3_service
from app.services.email import email_service


class ProductService:
    """Service class for product operations."""
    
    def __init__(self, db: Session):
        """
        Initialize product service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def _generate_verification_code(self) -> str:
        """Generate a 6-digit numeric verification code."""
        return ''.join(random.choices(string.digits, k=6))
    
    def _get_verification_expiry(self) -> datetime:
        """Return the expiry datetime for product verification codes."""
        return datetime.utcnow() + timedelta(minutes=settings.PRODUCT_VERIFICATION_CODE_EXPIRY_MINUTES)
    
    def _parse_bool(self, value: Optional[Any], default: bool = False) -> bool:
        """Parse a flexible truthy/falsey string into boolean."""
        if value is None:
            return default
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in {"true", "1", "yes", "on"}
    
    def _get_seller_info(self, user: User) -> SellerInfo:
        """Helper function to extract seller information."""
        return SellerInfo(
            id=str(user.id),
            username=user.username,
            rating=4.8,  # TODO: Calculate from reviews
            total_sales=156,  # TODO: Get from orders
            avatar_url=user.avatar_url,
            is_verified=user.is_verified
        )
    
    def _product_to_list_response(self, product: Product, seller: User) -> ProductListResponse:
        """Convert Product model to ProductListResponse."""
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
            seller=self._get_seller_info(seller),
            created_at=product.created_at
        )
    
    def _product_to_detail_response(self, product: Product, seller: User) -> ProductDetailResponse:
        """Convert Product model to ProductDetailResponse."""
        # Fetch related category names
        category_name = None
        if product.category_id:
            category = self.db.query(MainCategory).filter(MainCategory.id == product.category_id).first()
            category_name = category.name if category else None
        
        gender_name = None
        if product.gender_id:
            gender = self.db.query(Gender).filter(Gender.id == product.gender_id).first()
            gender_name = gender.name if gender else None
        
        product_type_name = None
        if product.product_type_id:
            product_type = self.db.query(CategoryType).filter(CategoryType.id == product.product_type_id).first()
            product_type_name = product_type.name if product_type else None
        
        sub_category_name = None
        if product.sub_category_id:
            sub_category = self.db.query(SubCategory).filter(SubCategory.id == product.sub_category_id).first()
            sub_category_name = sub_category.name if sub_category else None
        
        brand_name = None
        if product.brand_id:
            brand = self.db.query(Brand).filter(Brand.id == product.brand_id).first()
            brand_name = brand.name if brand else None
        
        return ProductDetailResponse(
            id=str(product.id),
            title=product.title,
            description=product.description,
            price=product.price,
            category=str(product.category_id) if product.category_id else None,
            category_name=category_name,
            condition=product.condition,
            deal_method=product.deal_method,
            meetup_date=product.meetup_date,
            meetup_location=product.meetup_location,
            meetup_time=product.meetup_time,
            stock_quantity=product.stock_quantity,
            stock_status=product.stock_status,
            rating=product.rating,
            review_count=product.review_count,
            images=product.images or [],
            is_active=product.is_active,
            is_sold=product.is_sold,
            is_featured=product.is_featured,
            is_verified=product.is_verified,
            gender=str(product.gender_id) if product.gender_id else None,
            gender_name=gender_name,
            product_type=str(product.product_type_id) if product.product_type_id else None,
            product_type_name=product_type_name,
            sub_category=str(product.sub_category_id) if product.sub_category_id else None,
            sub_category_name=sub_category_name,
            brand=str(product.brand_id) if product.brand_id else None,
            brand_name=brand_name,
            size=product.size,
            colors=product.colors or [],
            product_style=product.product_style,
            purchase_button_enabled=product.purchase_button_enabled,
            delivery_method=product.delivery_method,
            delivery_time=product.delivery_time,
            delivery_fee=product.delivery_fee,
            delivery_fee_type=product.delivery_fee_type,
            tracking_provided=product.tracking_provided,
            shipping_address=product.shipping_address,
            meetup_locations=product.meetup_locations,
            measurement_chest=product.measurement_chest,
            measurement_sleeve_length=product.measurement_sleeve_length,
            measurement_length=product.measurement_length,
            measurement_hem=product.measurement_hem,
            measurement_shoulders=product.measurement_shoulders,
            seller=self._get_seller_info(seller),
            created_at=product.created_at,
            updated_at=product.updated_at
        )
    
    def _apply_filters_and_sorting(
        self,
        query,
        category: Optional[str] = None,
        product_type: Optional[str] = None,
        sub_category: Optional[str] = None,
        gender: Optional[str] = None,
        location: Optional[str] = None,
        search: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        sort: Optional[str] = "newest",
        brands: Optional[List[str]] = None,
        sizes: Optional[List[str]] = None,
        colors: Optional[List[str]] = None,
        conditions: Optional[List[str]] = None,
        delivery: Optional[List[str]] = None
    ):
        """
        Apply filters and sorting to a product query.
        
        Args:
            query: Base SQLAlchemy query
            category: Filter by category
            product_type: Filter by product type
            sub_category: Filter by sub-category
            gender: Filter by gender
            location: Filter by location
            search: Search term
            min_price: Minimum price filter
            max_price: Maximum price filter
            sort: Sort order
            brands: Filter by brands/brands (array)
            sizes: Filter by sizes (array)
            colors: Filter by colors (array)
            conditions: Filter by conditions (array)
            delivery: Filter by delivery method (array)
            
        Returns:
            Modified query with filters and sorting applied
        """
        # Basic filters - now using integer IDs
        if category:
            try:
                category_id = int(category)
                query = query.filter(Product.category_id == category_id)
            except (ValueError, TypeError):
                # If not a valid integer, try to find by name (backward compatibility)
                main_category = self.db.query(MainCategory).filter(MainCategory.name.ilike(f"%{category}%")).first()
                if main_category:
                    query = query.filter(Product.category_id == main_category.id)
        
        if product_type:
            try:
                product_type_id = int(product_type)
                query = query.filter(Product.product_type_id == product_type_id)
            except (ValueError, TypeError):
                # If not a valid integer, try to find by name (backward compatibility)
                category_type = self.db.query(CategoryType).filter(func.lower(CategoryType.name) == func.lower(product_type)).first()
                if category_type:
                    query = query.filter(Product.product_type_id == category_type.id)
        
        if sub_category:
            try:
                sub_category_id = int(sub_category)
                query = query.filter(Product.sub_category_id == sub_category_id)
            except (ValueError, TypeError):
                # If not a valid integer, try to find by name (backward compatibility)
                sub_cat = self.db.query(SubCategory).filter(func.lower(SubCategory.name) == func.lower(sub_category)).first()
                if sub_cat:
                    query = query.filter(Product.sub_category_id == sub_cat.id)
        
        if gender:
            try:
                gender_id = int(gender)
                query = query.filter(Product.gender_id == gender_id)
            except (ValueError, TypeError):
                # If not a valid integer, try to find by name (backward compatibility)
                gender_obj = self.db.query(Gender).filter(func.lower(Gender.name) == func.lower(gender)).first()
                if gender_obj:
                    query = query.filter(Product.gender_id == gender_obj.id)
        
        if location:
            # Location can match meetup_location or location field
            query = query.filter(
                or_(
                    Product.location.ilike(f"%{location}%"),
                    Product.meetup_location.ilike(f"%{location}%")
                )
            )
        
        # Search filter
        if search:
            search_term = f"%{search}%"
            search_conditions = [
                Product.title.ilike(search_term),
                Product.description.ilike(search_term)
            ]
            # Search in related brand/brand names via join
            # Note: brand search removed as it's now a UUID relationship
            # For full text search on brand names, would need a join which is complex
            if hasattr(Product, 'brand'):
                search_conditions.append(Product.brand.ilike(search_term))
            query = query.filter(or_(*search_conditions))
        
        # Price filters
        if min_price is not None:
            query = query.filter(Product.price >= min_price)
        
        if max_price is not None:
            query = query.filter(Product.price <= max_price)
        
        # Array filters - brands (mapped to brand_id field, integer ID or name lookup)
        if brands:
            brand_conditions = []
            for brand in brands:
                try:
                    brand_id = int(brand)
                    brand_conditions.append(Product.brand_id == brand_id)
                except (ValueError, TypeError):
                    # If not a valid integer, try to find by name (backward compatibility)
                    brand_obj = self.db.query(Brand).filter(func.lower(Brand.name) == func.lower(brand)).first()
                    if brand_obj:
                        brand_conditions.append(Product.brand_id == brand_obj.id)
            if brand_conditions:
                query = query.filter(or_(*brand_conditions))
        
        # Array filters - sizes (case-insensitive exact match)
        if sizes:
            size_conditions = []
            for size in sizes:
                size_conditions.append(
                    func.lower(Product.size) == func.lower(size)
                )
            if size_conditions:
                query = query.filter(or_(*size_conditions))
        
        # Array filters - colors (stored as JSON array)
        if colors:
            # PostgreSQL JSON array contains check
            color_conditions = []
            for color in colors:
                # Using jsonb_path_exists to check if any array element equals the color
                color_conditions.append(
                    func.jsonb_path_exists(
                        func.cast(Product.colors, JSONB),
                        f'$[*] ? (@ == "{color}")'
                    )
                )
            if color_conditions:
                query = query.filter(or_(*color_conditions))
        
        # Array filters - conditions (case-insensitive exact match)
        if conditions:
            # Use case-insensitive exact matching for conditions
            condition_conditions = []
            for condition_value in conditions:
                # Use func.lower for case-insensitive exact match
                condition_conditions.append(
                    func.lower(Product.condition) == func.lower(condition_value)
                )
            if condition_conditions:
                query = query.filter(or_(*condition_conditions))
        
        # Array filters - delivery (mapped to deal_method and delivery_method)
        if delivery:
            delivery_conditions = []
            for delivery_method in delivery:
                if delivery_method.lower() in ["buyer_protection", "delivery"]:
                    delivery_conditions.append(Product.deal_method.ilike("%delivery%"))
                elif delivery_method.lower() == "meetup":
                    delivery_conditions.append(
                        or_(
                            Product.deal_method.ilike("%meet%"),
                            Product.deal_method.ilike("%meetup%")
                        )
                    )
            if delivery_conditions:
                query = query.filter(or_(*delivery_conditions))
        
        # Sorting logic
        if sort == "price_low_high":
            query = query.order_by(Product.price.asc(), Product.created_at.desc())
        elif sort == "price_high_low":
            query = query.order_by(Product.price.desc(), Product.created_at.desc())
        elif sort == "verified":
            # Recently verified products first
            query = query.order_by(
                Product.is_verified.desc(),
                Product.created_at.desc()
            )
        elif sort == "popular":
            # Most popular (by rating and review count)
            query = query.order_by(
                Product.rating.desc(),
                Product.review_count.desc(),
                Product.created_at.desc()
            )
        elif sort == "grid_manager":
            # Grid manager sort (similar to newest but may have custom logic)
            query = query.order_by(Product.created_at.desc())
        else:  # Default: newest
            query = query.order_by(Product.created_at.desc())
        
        return query
    
    def list_featured_products(
        self,
        page: int,
        page_size: int,
        category: Optional[str] = None,
        product_type: Optional[str] = None,
        sub_category: Optional[str] = None,
        gender: Optional[str] = None,
        location: Optional[str] = None,
        search: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        sort: Optional[str] = "newest",
        brands: Optional[List[str]] = None,
        sizes: Optional[List[str]] = None,
        colors: Optional[List[str]] = None,
        conditions: Optional[List[str]] = None,
        delivery: Optional[List[str]] = None
    ) -> ProductPaginationResponse:
        """
        Get featured products listing with filtering and sorting.
        
        Args:
            page: Page number (starts from 1)
            page_size: Number of items per page
            category: Filter by category
            product_type: Filter by product type
            sub_category: Filter by sub-category
            gender: Filter by gender
            location: Filter by location
            search: Search term
            min_price: Minimum price filter
            max_price: Maximum price filter
            sort: Sort order (newest, price_low_high, price_high_low, verified, popular, grid_manager)
            brands: Filter by brands/brands (array)
            sizes: Filter by sizes (array)
            colors: Filter by colors (array)
            conditions: Filter by conditions (array)
            delivery: Filter by delivery method (array)
            
        Returns:
            ProductPaginationResponse: Paginated list of featured products
        """
        offset = (page - 1) * page_size
        
        # Base query for featured products
        query = self.db.query(Product).filter(
            and_(
                Product.is_featured == True,
                Product.is_active == True,
                Product.is_sold == False
            )
        )
        
        # Apply filters and sorting
        query = self._apply_filters_and_sorting(
            query,
            category=category,
            product_type=product_type,
            sub_category=sub_category,
            gender=gender,
            location=location,
            search=search,
            min_price=min_price,
            max_price=max_price,
            sort=sort,
            brands=brands,
            sizes=sizes,
            colors=colors,
            conditions=conditions,
            delivery=delivery
        )
        
        total = query.count()
        products = query.offset(offset).limit(page_size).all()
        
        items = []
        for product in products:
            seller = self.db.query(User).filter(User.id == product.owner_id).first()
            if seller:
                items.append(self._product_to_list_response(product, seller))
        
        total_pages = math.ceil(total / page_size) if total > 0 else 0
        
        return ProductPaginationResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )
    
    def list_recommended_products(
        self,
        page: int,
        page_size: int,
        category: Optional[str] = None,
        product_type: Optional[str] = None,
        sub_category: Optional[str] = None,
        gender: Optional[str] = None,
        location: Optional[str] = None,
        search: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        sort: Optional[str] = "popular",
        brands: Optional[List[str]] = None,
        sizes: Optional[List[str]] = None,
        colors: Optional[List[str]] = None,
        conditions: Optional[List[str]] = None,
        delivery: Optional[List[str]] = None
    ) -> ProductPaginationResponse:
        """
        Get recommended products for user with filtering and sorting.
        
        Args:
            page: Page number (starts from 1)
            page_size: Number of items per page
            category: Filter by category
            product_type: Filter by product type
            sub_category: Filter by sub-category
            gender: Filter by gender
            location: Filter by location
            search: Search term
            min_price: Minimum price filter
            max_price: Maximum price filter
            sort: Sort order (newest, price_low_high, price_high_low, verified, popular, grid_manager)
            brands: Filter by brands/brands (array)
            sizes: Filter by sizes (array)
            colors: Filter by colors (array)
            conditions: Filter by conditions (array)
            delivery: Filter by delivery method (array)
            
        Returns:
            ProductPaginationResponse: Paginated list of recommended products
        """
        offset = (page - 1) * page_size
        
        # Base query for recommended products (excludes featured)
        query = self.db.query(Product).filter(
            and_(
                Product.is_active == True,
                Product.is_sold == False,
                Product.is_featured == False
            )
        )
        
        # Apply filters and sorting
        query = self._apply_filters_and_sorting(
            query,
            category=category,
            product_type=product_type,
            sub_category=sub_category,
            gender=gender,
            location=location,
            search=search,
            min_price=min_price,
            max_price=max_price,
            sort=sort,
            brands=brands,
            sizes=sizes,
            colors=colors,
            conditions=conditions,
            delivery=delivery
        )
        
        total = query.count()
        products = query.offset(offset).limit(page_size).all()
        
        items = []
        for product in products:
            seller = self.db.query(User).filter(User.id == product.owner_id).first()
            if seller:
                items.append(self._product_to_list_response(product, seller))
        
        total_pages = math.ceil(total / page_size) if total > 0 else 0
        
        return ProductPaginationResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )
    
    def list_user_products(
        self,
        user_id: str,
        page: int,
        page_size: int,
        status_filter: Optional[str] = None,
        search: Optional[str] = None
    ) -> ProductPaginationResponse:
        """
        List products created by a user.
        
        Args:
            user_id: User ID (integer)
            page: Page number
            page_size: Items per page
            status_filter: Filter by status (active, inactive, sold, verification_pending)
            search: Search term
            
        Returns:
            ProductPaginationResponse: Paginated list of user's products
            
        Raises:
            HTTPException: If user not found or invalid status filter
        """
        try:
            owner_id = int(user_id)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user identifier. Expected integer ID."
            )
        
        user = self.db.query(User).filter(User.id == owner_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        query = self.db.query(Product).filter(Product.owner_id == owner_id)
        
        if status_filter:
            normalized_status = status_filter.lower()
            if normalized_status == "active":
                query = query.filter(and_(Product.is_active == True, Product.is_sold == False))
            elif normalized_status == "inactive":
                query = query.filter(Product.is_active == False)
            elif normalized_status == "sold":
                query = query.filter(Product.is_sold == True)
            elif normalized_status == "verification_pending":
                query = query.filter(Product.is_verified == False)
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid status filter. Allowed values: active, inactive, sold, verification_pending"
                )
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Product.title.ilike(search_term),
                    Product.description.ilike(search_term)
                )
            )
        
        total = query.count()
        offset = (page - 1) * page_size
        products = query.order_by(Product.created_at.desc()).offset(offset).limit(page_size).all()
        
        items = [self._product_to_list_response(product, user) for product in products]
        total_pages = math.ceil(total / page_size) if total > 0 else 0
        
        return ProductPaginationResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )
    
    def list_products(
        self,
        page: int,
        page_size: int,
        category: Optional[str] = None,
        product_type: Optional[str] = None,
        sub_category: Optional[str] = None,
        gender: Optional[str] = None,
        location: Optional[str] = None,
        search: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        sort: Optional[str] = "newest",
        brands: Optional[List[str]] = None,
        sizes: Optional[List[str]] = None,
        colors: Optional[List[str]] = None,
        conditions: Optional[List[str]] = None,
        delivery: Optional[List[str]] = None
    ) -> ProductPaginationResponse:
        """
        List all products with filtering and pagination.
        
        Args:
            page: Page number
            page_size: Items per page
            category: Filter by category
            product_type: Filter by product type
            sub_category: Filter by sub-category
            gender: Filter by gender
            location: Filter by location
            search: Search term
            min_price: Minimum price filter
            max_price: Maximum price filter
            sort: Sort order (newest, price_low_high, price_high_low, verified, popular, grid_manager)
            brands: Filter by brands/brands (array)
            sizes: Filter by sizes (array)
            colors: Filter by colors (array)
            conditions: Filter by conditions (array)
            delivery: Filter by delivery method (array)
            
        Returns:
            ProductPaginationResponse: Paginated list of products
        """
        offset = (page - 1) * page_size
        
        # Base query for all products
        query = self.db.query(Product).filter(
            and_(
                Product.is_active == True,
                Product.is_sold == False
            )
        )
        
        # Apply filters and sorting
        query = self._apply_filters_and_sorting(
            query,
            category=category,
            product_type=product_type,
            sub_category=sub_category,
            gender=gender,
            location=location,
            search=search,
            min_price=min_price,
            max_price=max_price,
            sort=sort,
            brands=brands,
            sizes=sizes,
            colors=colors,
            conditions=conditions,
            delivery=delivery
        )
        
        total = query.count()
        products = query.offset(offset).limit(page_size).all()
        
        items = []
        for product in products:
            seller = self.db.query(User).filter(User.id == product.owner_id).first()
            if seller:
                items.append(self._product_to_list_response(product, seller))
        
        total_pages = math.ceil(total / page_size) if total > 0 else 0
        
        return ProductPaginationResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )
    
    def get_product(self, product_id: str) -> ProductDetailResponse:
        """
        Get detailed product information by ID.
        
        Args:
            product_id: Product ID (integer)
            
        Returns:
            ProductDetailResponse: Complete product details
            
        Raises:
            HTTPException: If product or seller not found
        """
        try:
            product_id_int = int(product_id)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid product ID format. Expected integer ID."
            )
        
        product = self.db.query(Product).filter(Product.id == product_id_int).first()
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        seller = self.db.query(User).filter(User.id == product.owner_id).first()
        
        if not seller:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Seller not found"
            )
        
        return self._product_to_detail_response(product, seller)
    
    def create_product(
        self,
        user_id: str,
        form_data: Dict[str, Any],
        image_urls: List[str]
    ) -> ProductDetailResponse:
        """
        Create a new product listing with S3 image URLs.
        
        Args:
            user_id: Current authenticated user ID
            form_data: Parsed form data dictionary
            image_urls: List of S3 image URLs
            
        Returns:
            ProductDetailResponse: Created product details
            
        Raises:
            HTTPException: If validation fails or creation fails
        """
        # Extract form fields
        title = form_data.get("title")
        description = form_data.get("description")
        price = form_data.get("price")
        category = form_data.get("category")
        condition = form_data.get("condition")
        dealMethod = form_data.get("dealMethod")
        meetupDate = form_data.get("meetupDate")
        meetupLocation = form_data.get("meetupLocation")
        meetupTime = form_data.get("meetupTime")
        meetupLocations_raw = form_data.get("meetupLocations")
        stockQuantity = form_data.get("stockQuantity")
        
        gender = form_data.get("gender")
        productType = form_data.get("productType")
        subCategory = form_data.get("subCategory")
        brand = form_data.get("brand")
        size = form_data.get("size")
        colors_raw = form_data.get("colors")
        productStyle = form_data.get("productStyle")
        
        measurementChest = form_data.get("measurementChest")
        measurementSleeveLength = form_data.get("measurementSleeveLength")
        measurementLength = form_data.get("measurementLength")
        measurementHem = form_data.get("measurementHem")
        measurementShoulders = form_data.get("measurementShoulders")
        
        purchaseButtonEnabled_raw = form_data.get("purchaseButtonEnabled")
        deliveryMethod = form_data.get("deliveryMethod")
        deliveryTime = form_data.get("deliveryTime")
        deliveryFee_raw = form_data.get("deliveryFee")
        deliveryFeeType = form_data.get("deliveryFeeType")
        trackingProvided_raw = form_data.get("trackingProvided")
        shippingAddress = form_data.get("shippingAddress")
        
        # Validate required fields
        if not all([title, description, price, category, condition, dealMethod]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required fields: title, description, price, category, condition, dealMethod"
            )
        
        # Normalize deal method for validation
        normalized_deal_method = dealMethod.strip().lower()
        if normalized_deal_method not in {"delivery", "meet up", "meetup"}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="dealMethod must be either 'Delivery' or 'Meet Up'"
            )
        
        purchase_button_enabled = self._parse_bool(purchaseButtonEnabled_raw, default=True)
        tracking_provided = self._parse_bool(trackingProvided_raw, default=False)
        
        # Parse colors JSON
        colors: List[str] = []
        if colors_raw:
            try:
                parsed_colors = json.loads(colors_raw)
                if not isinstance(parsed_colors, list):
                    raise ValueError("colors must be a JSON array")
                colors = [str(color) for color in parsed_colors if str(color).strip()]
            except (json.JSONDecodeError, ValueError, TypeError) as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid colors format: {exc}"
                )
        
        # colors are required per documentation
        if not colors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="colors is required and must contain at least one value"
            )
        
        # Validate required classification fields
        required_fields = []
        if not productType:
            required_fields.append("productType")
        if not brand:
            required_fields.append("brand")
        if not productStyle:
            required_fields.append("productStyle")
        if required_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required fields: {', '.join(required_fields)}"
            )
        
        # Validate integer IDs for category-related fields and store them directly
        category_id = None
        product_type_id = None
        sub_category_id = None
        gender_id = None
        brand_id = None
        
        # Validate and get main category ID
        try:
            category_id = int(category)
            main_category = self.db.query(MainCategory).filter(MainCategory.id == category_id).first()
            if not main_category:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid category ID: {category}"
                )
        except HTTPException:
            raise
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid category format. Expected integer ID, got: {category}"
            )
        
        # Validate and get category type ID
        try:
            product_type_id = int(productType)
            category_type = self.db.query(CategoryType).filter(CategoryType.id == product_type_id).first()
            if not category_type:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid productType ID: {productType}"
                )
        except HTTPException:
            raise
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid productType format. Expected integer ID, got: {productType}"
            )
        
        # Validate and get sub category ID
        if subCategory:
            try:
                sub_category_id = int(subCategory)
                sub_cat = self.db.query(SubCategory).filter(SubCategory.id == sub_category_id).first()
                if not sub_cat:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid subCategory ID: {subCategory}"
                    )
            except HTTPException:
                raise
            except (ValueError, TypeError):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid subCategory format. Expected integer ID, got: {subCategory}"
                )
        
        # Validate and get gender ID
        if gender:
            try:
                gender_id = int(gender)
                gender_obj = self.db.query(Gender).filter(Gender.id == gender_id).first()
                if not gender_obj:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid gender ID: {gender}"
                    )
            except HTTPException:
                raise
            except (ValueError, TypeError):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid gender format. Expected integer ID, got: {gender}"
                )
        
        # Validate and get brand ID
        try:
            brand_id = int(brand)
            brand = self.db.query(Brand).filter(Brand.id == brand_id).first()
            if not brand:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid brand ID: {brand}"
                )
            if not brand.active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Brand '{brand.name}' is not active"
                )
        except HTTPException:
            raise
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid brand format. Expected integer ID, got: {brand}"
            )
        
        # Validate category-specific requirements (need to get category name for validation)
        main_category_obj = self.db.query(MainCategory).filter(MainCategory.id == category_id).first()
        category_name = main_category_obj.name.lower() if main_category_obj else ""
        
        if category_name in {"fashion"} and not gender_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="gender is required for Fashion Category"
            )
        
        # Get category type name for validation
        category_type_obj = self.db.query(CategoryType).filter(CategoryType.id == product_type_id).first()
        product_type_name = category_type_obj.name.lower() if category_type_obj else ""
        
        if product_type_name in {"tops", "bottoms", "footwear", "accessories"} and not size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="size is required for Fashion items (Tops, Bottoms, Footwear, Accessories)"
            )
        
        # Parse stock quantity
        stock_quantity_value = 1
        if stockQuantity:
            try:
                stock_quantity_value = int(stockQuantity)
                if stock_quantity_value < 0:
                    raise ValueError
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="stockQuantity must be a positive integer"
                )
        
        # Parse delivery fee
        delivery_fee_decimal: Optional[Decimal] = None
        if deliveryFee_raw not in (None, ""):
            try:
                delivery_fee_decimal = Decimal(deliveryFee_raw)
            except (InvalidOperation, ValueError):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="deliveryFee must be a numeric value"
                )
            if delivery_fee_decimal < 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="deliveryFee cannot be negative"
                )
        
        # Parse meetup locations
        meetup_locations: Optional[List[Dict[str, Any]]] = None
        if meetupLocations_raw:
            try:
                parsed_locations = json.loads(meetupLocations_raw)
                if not isinstance(parsed_locations, list):
                    raise ValueError("meetupLocations must be a JSON array")
                meetup_locations = parsed_locations
            except (json.JSONDecodeError, ValueError, TypeError) as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid meetupLocations format: {exc}"
                )
        
        # Validate deal method specific requirements
        if normalized_deal_method in {"meet up", "meetup"}:
            if not meetupDate or not meetupTime:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="meetupDate and meetupTime are required when dealMethod is 'Meet Up'"
                )
            if purchase_button_enabled:
                if not meetup_locations or len(meetup_locations) == 0:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="At least one meetup location is required when purchaseButtonEnabled is true for Meet Up"
                    )
        elif normalized_deal_method == "delivery":
            if purchase_button_enabled:
                missing_delivery_fields = [
                    field_name for field_name, value in {
                        "deliveryMethod": deliveryMethod,
                        "deliveryTime": deliveryTime,
                        "deliveryFee": deliveryFee_raw,
                        "deliveryFeeType": deliveryFeeType
                    }.items() if value in (None, "")
                ]
                if missing_delivery_fields:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Missing required delivery fields: {', '.join(missing_delivery_fields)}"
                    )
            if deliveryMethod and deliveryMethod.strip().lower() == "partner" and not shippingAddress:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="shippingAddress is required when deliveryMethod is 'partner'"
                )
        
        delivery_method_normalized: Optional[str] = None
        if deliveryMethod:
            delivery_method_normalized = deliveryMethod.strip().lower()
            if delivery_method_normalized not in {"own", "partner"}:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="deliveryMethod must be either 'own' or 'partner'"
                )
        
        delivery_fee_type_normalized: Optional[str] = None
        if deliveryFeeType:
            delivery_fee_type_normalized = deliveryFeeType.strip().lower()
            if delivery_fee_type_normalized not in {"free", "custom"}:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="deliveryFeeType must be either 'free' or 'custom'"
                )
        
        delivery_time_normalized: Optional[str] = None
        if deliveryTime:
            delivery_time_normalized = deliveryTime.strip().lower()
            if delivery_time_normalized not in {"same_day", "1_3_days", "2_5_days", "4_7_days"}:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="deliveryTime must be one of: same_day, 1_3_days, 2_5_days, 4_7_days"
                )
        
        # Verify user exists and fetch user ID
        try:
            user_id_int = int(user_id)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user identifier. Expected integer ID."
            )
        
        user = self.db.query(User).filter(User.id == user_id_int).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Convert price to Decimal
        try:
            price_decimal = Decimal(price)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid price format"
            )
        
        # Validate minimum number of images (4 required)
        if len(image_urls) < 4:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Minimum 4 product images are required. Received {len(image_urls)} image URL(s)."
            )
        
        # Validate maximum number of images (10 allowed)
        if len(image_urls) > 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 10 images allowed per product"
            )
        
        # Validate image URLs format
        for idx, url in enumerate(image_urls):
            if not url or not isinstance(url, str):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Image URL at index {idx} must be a valid string"
                )
            
            # Validate URL format using urllib.parse
            try:
                parsed = urlparse(url)
                if not parsed.scheme or not parsed.netloc:
                    raise ValueError("Invalid URL format")
                if parsed.scheme not in ('http', 'https'):
                    raise ValueError("URL must use http or https scheme")
            except (ValueError, Exception) as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid image URL format at index {idx}: {url}"
                )
        
        # Create product
        verification_code = self._generate_verification_code()
        verification_expires_at = self._get_verification_expiry()
        
        deal_method_value = "Delivery" if normalized_deal_method == "delivery" else "Meet Up"
        stock_status_value = "In Stock" if stock_quantity_value > 0 else "Out of Stock"
        
        product = Product(
            owner_id=user_id_int,
            title=title,
            description=description,
            price=price_decimal,
            category_id=category_id,
            condition=condition,
            deal_method=deal_method_value,
            meetup_date=meetupDate,
            meetup_location=meetupLocation,
            meetup_time=meetupTime,
            images=image_urls,
            stock_quantity=stock_quantity_value,
            stock_status=stock_status_value,
            is_active=False,
            is_verified=False,
            verification_code=verification_code,
            verification_expires_at=verification_expires_at,
            verification_attempts=0,
            gender_id=gender_id,
            product_type_id=product_type_id,
            sub_category_id=sub_category_id,
            brand_id=brand_id,
            size=size,
            colors=colors,
            product_style=productStyle,
            measurement_chest=measurementChest,
            measurement_sleeve_length=measurementSleeveLength,
            measurement_length=measurementLength,
            measurement_hem=measurementHem,
            measurement_shoulders=measurementShoulders,
            purchase_button_enabled=purchase_button_enabled,
            delivery_method=delivery_method_normalized,
            delivery_time=delivery_time_normalized,
            delivery_fee=delivery_fee_decimal,
            delivery_fee_type=delivery_fee_type_normalized,
            tracking_provided=tracking_provided,
            shipping_address=shippingAddress.strip() if shippingAddress else None,
            meetup_locations=meetup_locations
        )
        
        self.db.add(product)
        self.db.flush()
        
        email_sent = email_service.send_product_verification_email(
            email=user.email,
            product_title=title,
            verification_code=verification_code
        )
        
        if not email_sent:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send verification email. Please try again later."
            )
        
        self.db.commit()
        self.db.refresh(product)
        
        return self._product_to_detail_response(product, user)
    
    def send_verification_code(self, product_id: str, user_id: str) -> Dict[str, str]:
        """
        Send or resend the verification code for a product listing.
        
        Args:
            product_id: Product ID (integer)
            user_id: Current authenticated user ID
            
        Returns:
            Dict[str, str]: Success message
            
        Raises:
            HTTPException: If product not found, unauthorized, or already verified
        """
        try:
            product_id_int = int(product_id)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid product ID format. Expected integer ID."
            )
        
        product = self.db.query(Product).filter(Product.id == product_id_int).first()
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        
        try:
            user_id_int = int(user_id)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user identifier. Expected integer ID."
            )
        
        if product.owner_id != user_id_int:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to verify this product")
        
        if product.is_verified:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Product is already verified")
        
        user = self.db.query(User).filter(User.id == product.owner_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Owner not found")
        
        product.verification_code = self._generate_verification_code()
        product.verification_expires_at = self._get_verification_expiry()
        product.verification_attempts = 0
        product.is_active = False
        
        self.db.flush()
        
        email_sent = email_service.send_product_verification_email(
            email=user.email,
            product_title=product.title,
            verification_code=product.verification_code
        )
        
        if not email_sent:
            self.db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to send verification email")
        
        self.db.commit()
        
        return {"message": "Verification code sent to your registered email"}
    
    def verify_product(self, product_id: str, verification_data: ProductVerificationRequest, user_id: str) -> ProductDetailResponse:
        """
        Verify a product listing using the received verification code.
        
        Args:
            product_id: Product ID (integer)
            verification_data: Verification request with code
            user_id: Current authenticated user ID
            
        Returns:
            ProductDetailResponse: Verified product details
            
        Raises:
            HTTPException: If verification fails
        """
        try:
            product_id_int = int(product_id)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid product ID format. Expected integer ID."
            )
        
        product = self.db.query(Product).filter(Product.id == product_id_int).first()
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        
        try:
            user_id_int = int(user_id)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user identifier. Expected integer ID."
            )
        
        if product.owner_id != user_id_int:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to verify this product")
        
        if product.is_verified:
            seller = self.db.query(User).filter(User.id == product.owner_id).first()
            if not seller:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Seller not found")
            return self._product_to_detail_response(product, seller)
        
        if not product.verification_code:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No verification code found. Request a new code.")
        
        if product.verification_expires_at and datetime.utcnow() > product.verification_expires_at:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification code has expired. Request a new code.")
        
        if product.verification_attempts >= settings.PRODUCT_VERIFICATION_MAX_ATTEMPTS:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Maximum verification attempts reached. Request a new code.")
        
        if product.verification_code != verification_data.verification_code:
            product.verification_attempts += 1
            self.db.commit()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification code")
        
        product.is_verified = True
        product.is_active = True
        product.verification_code = None
        product.verification_expires_at = None
        product.verification_attempts = 0
        
        self.db.commit()
        self.db.refresh(product)
        
        seller = self.db.query(User).filter(User.id == product.owner_id).first()
        if not seller:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Seller not found")
        
        return self._product_to_detail_response(product, seller)
    
    def update_product(self, product_id: str, product_data: ProductUpdate, user_id: str) -> ProductDetailResponse:
        """
        Update a product listing.
        
        Args:
            product_id: Product ID (integer)
            product_data: Product update data
            user_id: Current authenticated user ID
            
        Returns:
            ProductDetailResponse: Updated product details
            
        Raises:
            HTTPException: If product not found or user not authorized
        """
        try:
            product_id_int = int(product_id)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid product ID format. Expected integer ID."
            )
        
        product = self.db.query(Product).filter(Product.id == product_id_int).first()
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        try:
            user_id_int = int(user_id)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user identifier. Expected integer ID."
            )
        
        if product.owner_id != user_id_int:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update this product"
            )
        
        update_data = product_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(product, field, value)
        
        self.db.commit()
        self.db.refresh(product)
        
        seller = self.db.query(User).filter(User.id == product.owner_id).first()
        
        return self._product_to_detail_response(product, seller)
    
    def add_product_images(self, product_id: str, images: List[UploadFile], user_id: str) -> ProductDetailResponse:
        """
        Add or replace images for an existing product.
        
        Args:
            product_id: Product ID (integer)
            images: List of image files to upload
            user_id: Current authenticated user ID
            
        Returns:
            ProductDetailResponse: Updated product details with new images
            
        Raises:
            HTTPException: If product not found, user not authorized, or upload fails
        """
        try:
            product_id_int = int(product_id)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid product ID format. Expected integer ID."
            )
        
        product = self.db.query(Product).filter(Product.id == product_id_int).first()
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        try:
            user_id_int = int(user_id)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user identifier. Expected integer ID."
            )
        
        if product.owner_id != user_id_int:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update this product"
            )
        
        existing_images = product.images or []
        
        if len(existing_images) + len(images) > 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Maximum 10 images allowed per product. You have {len(existing_images)} existing images."
            )
        
        s3_service = get_s3_service()
        new_image_urls = []
        
        for img in images:
            if not img.content_type or not img.content_type.startswith('image/'):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File {img.filename} must be an image"
                )
            
            try:
                result = s3_service.upload_file(img, "product_images", user_id)
                new_image_urls.append(result["url"])
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to upload image {img.filename}: {str(e)}"
                )
        
        product.images = existing_images + new_image_urls
        self.db.commit()
        self.db.refresh(product)
        
        seller = self.db.query(User).filter(User.id == product.owner_id).first()
        
        return self._product_to_detail_response(product, seller)
    
    def delete_product(self, product_id: str, user_id: str) -> None:
        """
        Delete a product listing (soft delete).
        
        Args:
            product_id: Product ID (integer)
            user_id: Current authenticated user ID
            
        Raises:
            HTTPException: If product not found or user not authorized
        """
        try:
            product_id_int = int(product_id)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid product ID format. Expected integer ID."
            )
        
        product = self.db.query(Product).filter(Product.id == product_id_int).first()
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        try:
            user_id_int = int(user_id)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user identifier. Expected integer ID."
            )
        
        if product.owner_id != user_id_int:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this product"
            )
        
        product.is_active = False
        self.db.commit()

