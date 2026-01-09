"""
Product management routes.

This module contains product CRUD endpoints and listing APIs.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.security import get_current_user_id, get_optional_user_id
from app.models.product import Product
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductDetailResponse,
    ProductPaginationResponse,
    ProductVerificationRequest
)
from app.schemas.report import ProductReportRequest, ProductReportResponse
from app.schemas.spotlight import ProductSpotlightStatusResponse
from app.services.product import ProductService
from app.services.report import ProductReportService
from app.services.spotlight import SpotlightService
from app.services.follow import FollowService

router = APIRouter()


@router.get("/spotlighted", response_model=ProductPaginationResponse)
async def get_spotlighted_products(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(12, ge=1, le=100, description="Items per page"),
    category: Optional[str] = Query(None, description="Filter by category"),
    product_type: Optional[str] = Query(None, description="Filter by product type"),
    sub_category: Optional[str] = Query(None, description="Filter by sub-category"),
    gender: Optional[str] = Query(None, description="Filter by gender"),
    location: Optional[str] = Query(None, description="Filter by location"),
    search: Optional[str] = Query(None, description="Search in name and description"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price"),
    sort: Optional[str] = Query("newest", description="Sort order: newest, price_low_high, price_high_low, verified, popular, grid_manager"),
    brands: Optional[List[str]] = Query(None, description="Filter by brands/designers (array)"),
    sizes: Optional[List[str]] = Query(None, description="Filter by sizes (array)"),
    colors: Optional[List[str]] = Query(None, description="Filter by colors (array)"),
    conditions: Optional[List[str]] = Query(None, description="Filter by conditions (array)"),
    delivery: Optional[List[str]] = Query(None, description="Filter by delivery method (array)"),
    db: Session = Depends(get_db)
):
    """
    Get spotlighted products listing with filtering and sorting.
    
    Returns admin-promoted products that are prioritized in the feed.
    Spotlighted products are manually promoted by admins for limited durations.
    
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
        brands: Filter by brands/designers (array)
        sizes: Filter by sizes (array)
        colors: Filter by colors (array)
        conditions: Filter by conditions (array)
        delivery: Filter by delivery method (array)
        db: Database session
        
    Returns:
        ProductPaginationResponse: Paginated list of spotlighted products
    """
    service = ProductService(db)
    return service.list_featured_products(
        page=page,
        page_size=page_size,
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


@router.get("/recommended", response_model=ProductPaginationResponse)
async def get_recommended_products(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(12, ge=1, le=100, description="Items per page"),
    category: Optional[str] = Query(None, description="Filter by category"),
    product_type: Optional[str] = Query(None, description="Filter by product type"),
    sub_category: Optional[str] = Query(None, description="Filter by sub-category"),
    gender: Optional[str] = Query(None, description="Filter by gender"),
    location: Optional[str] = Query(None, description="Filter by location"),
    search: Optional[str] = Query(None, description="Search in name and description"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price"),
    sort: Optional[str] = Query("popular", description="Sort order: newest, price_low_high, price_high_low, verified, popular, grid_manager"),
    brands: Optional[List[str]] = Query(None, description="Filter by brands/designers (array)"),
    sizes: Optional[List[str]] = Query(None, description="Filter by sizes (array)"),
    colors: Optional[List[str]] = Query(None, description="Filter by colors (array)"),
    conditions: Optional[List[str]] = Query(None, description="Filter by conditions (array)"),
    delivery: Optional[List[str]] = Query(None, description="Filter by delivery method (array)"),
    db: Session = Depends(get_db)
):
    """
    Get recommended products for user with filtering and sorting.
    
    Returns personalized picks based on user interests.
    
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
        brands: Filter by brands/designers (array)
        sizes: Filter by sizes (array)
        colors: Filter by colors (array)
        conditions: Filter by conditions (array)
        delivery: Filter by delivery method (array)
        db: Database session
        
    Returns:
        ProductPaginationResponse: Paginated list of recommended products
    """
    service = ProductService(db)
    return service.list_recommended_products(
        page=page,
        page_size=page_size,
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


@router.get("/my-listings", response_model=ProductPaginationResponse)
async def list_my_products(
    current_user_id: str = Depends(get_current_user_id),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(12, ge=1, le=100, description="Items per page"),
    status_filter: Optional[str] = Query(
        None,
        alias="status",
        description="Filter by status: active, inactive, sold, verification_pending"
    ),
    category: Optional[str] = Query(None, description="Filter by category"),
    product_type: Optional[str] = Query(None, description="Filter by product type"),
    sub_category: Optional[str] = Query(None, description="Filter by sub-category"),
    gender: Optional[str] = Query(None, description="Filter by gender"),
    location: Optional[str] = Query(None, description="Filter by location"),
    search: Optional[str] = Query(None, description="Search in name and description"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price"),
    sort: Optional[str] = Query("newest", description="Sort order: newest, price_low_high, price_high_low, verified, popular, grid_manager"),
    brands: Optional[List[str]] = Query(None, description="Filter by brands/designers (array)"),
    sizes: Optional[List[str]] = Query(None, description="Filter by sizes (array)"),
    colors: Optional[List[str]] = Query(None, description="Filter by colors (array)"),
    conditions: Optional[List[str]] = Query(None, description="Filter by conditions (array)"),
    delivery: Optional[List[str]] = Query(None, description="Filter by delivery method (array)"),
    db: Session = Depends(get_db)
):
    """
    List products created by the current authenticated user.

    Supports comprehensive filtering including status, category, price range, brands, sizes, colors, conditions, delivery methods, and search.

    Args:
        current_user_id: Current authenticated user ID
        page: Page number
        page_size: Items per page
        status_filter: Filter by status (active, inactive, sold, verification_pending)
        category: Filter by category
        product_type: Filter by product type
        sub_category: Filter by sub-category
        gender: Filter by gender
        location: Filter by location
        search: Search term
        min_price: Minimum price filter
        max_price: Maximum price filter
        sort: Sort order (newest, price_low_high, price_high_low, verified, popular, grid_manager)
        brands: Filter by brands/designers (array)
        sizes: Filter by sizes (array)
        colors: Filter by colors (array)
        conditions: Filter by conditions (array)
        delivery: Filter by delivery method (array)
        db: Database session

    Returns:
        ProductPaginationResponse: Paginated list of user's products
    """
    service = ProductService(db)
    return service.list_user_products(
        current_user_id,current_user_id, page, page_size, status_filter, search,
        category=category,
        product_type=product_type,
        sub_category=sub_category,
        gender=gender,
        location=location,
        min_price=min_price,
        max_price=max_price,
        sort=sort,
        brands=brands,
        sizes=sizes,
        colors=colors,
        conditions=conditions,
        delivery=delivery
    )


@router.get("/", response_model=ProductPaginationResponse)
async def list_products(
    
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(12, ge=1, le=100, description="Items per page"),
    type: Optional[str] = Query(None, description="Filter type: 'spotlighted' for spotlighted products, 'recommended' for recommended products, or omit for all products"),
    category: Optional[str] = Query(None, description="Filter by category"),
    product_type: Optional[str] = Query(None, description="Filter by product type"),
    sub_category: Optional[str] = Query(None, description="Filter by sub-category"),
    gender: Optional[str] = Query(None, description="Filter by gender"),
    location: Optional[str] = Query(None, description="Filter by location"),
    search: Optional[str] = Query(None, description="Search in name and description"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price"),
    sort: Optional[str] = Query("newest", description="Sort order: newest, price_low_high, price_high_low, verified, popular, grid_manager"),
    brands: Optional[List[str]] = Query(None, description="Filter by brands/designers (array)"),
    sizes: Optional[List[str]] = Query(None, description="Filter by sizes (array)"),
    colors: Optional[List[str]] = Query(None, description="Filter by colors (array)"),
    conditions: Optional[List[str]] = Query(None, description="Filter by conditions (array)"),
    delivery: Optional[List[str]] = Query(None, description="Filter by delivery method (array)"),
    current_user_id: Optional[str] = Depends(get_optional_user_id),
    db: Session = Depends(get_db)
):
    """
    List products with filtering and pagination.
    
    Use the 'type' parameter to filter:
    - type=spotlighted: Get only spotlighted products (admin-promoted)
    - type=recommended: Get only recommended products (non-spotlighted)
    - type=None or omitted: Get all products (default)
    
    Args:
        page: Page number (starts from 1)
        page_size: Items per page
        type: Filter type ('spotlighted', 'recommended', or None for all)
        category: Filter by category
        product_type: Filter by product type
        sub_category: Filter by sub-category
        gender: Filter by gender
        location: Filter by location
        search: Search term
        min_price: Minimum price filter
        max_price: Maximum price filter
        sort: Sort order (newest, price_low_high, price_high_low, verified, popular, grid_manager)
        brands: Filter by brands/designers (array)
        sizes: Filter by sizes (array)
        colors: Filter by colors (array)
        conditions: Filter by conditions (array)
        delivery: Filter by delivery method (array)
        db: Database session
        
    Returns:
        ProductPaginationResponse: Paginated list of products
    """
    service = ProductService(db)
    
    # Convert user_id to int if authenticated
    user_id_int = None
    if current_user_id:
        try:
            user_id_int = int(current_user_id)
        except (ValueError, TypeError):
            user_id_int = None
    
    # Route to appropriate method based on type parameter
    if type and type.lower() == "spotlighted":
        return service.list_featured_products(
            page=page,
            page_size=page_size,
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
            delivery=delivery,
            user_id=user_id_int
        )
    elif type and type.lower() == "recommended":
        return service.list_recommended_products(
            page=page,
            page_size=page_size,
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
            delivery=delivery,
            user_id=user_id_int
        )
    else:
        # Default: all products
        return service.list_products(
            page=page,
            page_size=page_size,
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
            delivery=delivery,
            user_id=user_id_int
        )


@router.get("/seller/{seller_id}/listings", response_model=ProductPaginationResponse)
async def get_seller_listings(
    seller_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(12, ge=1, le=100, description="Items per page"),
    category: Optional[str] = Query(None, description="Filter by category"),
    product_type: Optional[str] = Query(None, description="Filter by product type"),
    sub_category: Optional[str] = Query(None, description="Filter by sub-category"),
    gender: Optional[str] = Query(None, description="Filter by gender"),
    location: Optional[str] = Query(None, description="Filter by location"),
    search: Optional[str] = Query(None, description="Search in name and description"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price"),
    sort: Optional[str] = Query("newest", description="Sort order: newest, price_low_high, price_high_low, verified, popular, grid_manager"),
    brands: Optional[List[str]] = Query(None, description="Filter by brands/designers (array)"),
    sizes: Optional[List[str]] = Query(None, description="Filter by sizes (array)"),
    colors: Optional[List[str]] = Query(None, description="Filter by colors (array)"),
    conditions: Optional[List[str]] = Query(None, description="Filter by conditions (array)"),
    delivery: Optional[List[str]] = Query(None, description="Filter by delivery method (array)"),
    db: Session = Depends(get_db),
    current_user_id: Optional[str] = Depends(get_current_user_id)
):
    """
    Get all product listings for a specific seller (open route, no authentication required).
    
    Returns all products created by the specified seller with comprehensive filtering support.
    This is a public endpoint that can be accessed without authentication.
    
    Args:
        seller_id: Seller ID (integer)
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
        brands: Filter by brands/designers (array)
        sizes: Filter by sizes (array)
        colors: Filter by colors (array)
        conditions: Filter by conditions (array)
        delivery: Filter by delivery method (array)
        db: Database session
        
    Returns:
        ProductPaginationResponse: Paginated list of seller's products
        
    Raises:
        HTTPException: If seller not found
    """
    service = ProductService(db)
    # Return all products for the seller (no status filter)
    return service.list_user_products(
        current_user_id,seller_id, page, page_size, None, search,
        category=category,
        product_type=product_type,
        sub_category=sub_category,
        gender=gender,
        location=location,
        min_price=min_price,
        max_price=max_price,
        sort=sort,
        brands=brands,
        sizes=sizes,
        colors=colors,
        conditions=conditions,
        delivery=delivery
    )


@router.get("/{product_id}", response_model=ProductDetailResponse)
async def get_product(
    product_id: str,
    current_user_id: Optional[str] = Depends(get_optional_user_id),
    db: Session = Depends(get_db)
):
    """
    Get detailed product information by ID.
    
    Returns complete product details including specifications, 
    seller information, ratings, and policies.
    Includes seller follow status if user is authenticated.
    
    Args:
        product_id: Product ID (integer)
        current_user_id: Optional authenticated user ID
        db: Database session
        
    Returns:
        ProductDetailResponse: Complete product details with seller follow status
        
    Raises:
        HTTPException: If product not found
    """
    service = ProductService(db)
    
    # Convert user_id to int if authenticated
    user_id_int = None
    if current_user_id:
        try:
            user_id_int = int(current_user_id)
        except (ValueError, TypeError):
            user_id_int = None
    
    return service.get_product(product_id, user_id_int)


@router.get("/{product_id}/followers")
async def get_product_followers_count(
    product_id: str,
    db: Session = Depends(get_db)
):
    """
    Get count of followers for a product (public endpoint).
    
    Args:
        product_id: Product ID
        db: Database session
        
    Returns:
        dict: Product followers count
        
    Raises:
        HTTPException: If product not found
    """
    try:
        prod_id = int(product_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid product ID format"
        )
    
    # Validate product exists
    product = db.query(Product).filter(Product.id == prod_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    service = FollowService(db)
    followers_count = service.get_product_followers_count(prod_id)
    
    return {
        "product_id": str(prod_id),
        "followers_count": followers_count
    }


@router.get("/{product_id}/spotlight", response_model=ProductSpotlightStatusResponse)
async def get_product_spotlight_status(
    product_id: str,
    db: Session = Depends(get_db)
):
    """
    Get spotlight status for a specific product.
    
    Returns whether the product is currently spotlighted, and if so,
    provides all spotlight details including start time, end time,
    duration, and who applied it.
    
    Args:
        product_id: Product ID (integer)
        db: Database session
        
    Returns:
        ProductSpotlightStatusResponse: Spotlight status and details
        
    Raises:
        HTTPException: If product not found
    """
    # Convert product_id to int
    try:
        product_id_int = int(product_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid product ID format. Expected integer ID."
        )
    
    # Get spotlight status
    service = SpotlightService(db)
    return service.get_product_spotlight_status(product_id_int)


@router.post("/{product_id}/report", response_model=ProductReportResponse, status_code=status.HTTP_201_CREATED)
async def report_product(
    product_id: str,
    report_data: ProductReportRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Report a product with a reason.
    
    Users can report products they find inappropriate or violating platform rules.
    Each user can only report a product once.
    
    Args:
        product_id: Product ID (integer) to report
        report_data: Report data containing reason
        current_user_id: Current authenticated user ID
        db: Database session
        
    Returns:
        ProductReportResponse: Created report details
        
    Raises:
        HTTPException: If product not found, user already reported, or validation fails
    """
    service = ProductReportService(db)
    return service.report_product(current_user_id, product_id, report_data.reason)


@router.post("/", response_model=ProductDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: ProductCreate,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Create a new product listing with S3 image URLs.
    
    Send as application/json. Images should already be uploaded to S3 by the frontend.
    
    Args:
        product_data: Product creation data including S3 image URLs
        current_user_id: Current authenticated user ID
        db: Database session
        
    Returns:
        ProductDetailResponse: Created product details

    Notes:
        A verification code is emailed to the seller after creation. The product
        remains inactive until the code is confirmed via the verification endpoint.
    """
    # Convert Pydantic model to dict for service method
    form_data = product_data.model_dump(exclude={'images'})
    # Add images separately as they're now URLs
    image_urls = product_data.images
    
    service = ProductService(db)
    return service.create_product(current_user_id, form_data, image_urls)


@router.post("/{product_id}/verification/send", status_code=status.HTTP_200_OK)
async def send_product_verification_code(
    product_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Send or resend the verification code for a product listing."""
    service = ProductService(db)
    return service.send_verification_code(product_id, current_user_id)


@router.post("/{product_id}/verification", response_model=ProductDetailResponse)
async def verify_product_listing(
    product_id: str,
    verification_data: ProductVerificationRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Verify a product listing using the received verification code."""
    service = ProductService(db)
    return service.verify_product(product_id, verification_data, current_user_id)


@router.put("/{product_id}", response_model=ProductDetailResponse)
async def update_product(
    product_id: str,
    product_data: ProductUpdate,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Update a product listing (JSON only, no image uploads).
    
    Only the product owner can update their products.
    Use POST /{product_id}/images to add/update product images.
    
    Args:
        product_id: Product ID (integer)
        product_data: Product update data
        current_user_id: Current authenticated user ID
        db: Database session
        
    Returns:
        ProductDetailResponse: Updated product details
        
    Raises:
        HTTPException: If product not found or user not authorized
    """
    service = ProductService(db)
    return service.update_product(product_id, product_data, current_user_id)


@router.post("/{product_id}/images", response_model=ProductDetailResponse)
async def add_product_images(
    product_id: str,
    images: List[UploadFile] = File(...),
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Add or replace images for an existing product.
    
    Only the product owner can update product images.
    
    Args:
        product_id: Product ID (integer)
        images: List of image files to upload (max 10 total)
        current_user_id: Current authenticated user ID
        db: Database session
        
    Returns:
        ProductDetailResponse: Updated product details with new images
        
    Raises:
        HTTPException: If product not found, user not authorized, or upload fails
    """
    service = ProductService(db)
    return service.add_product_images(product_id, images, current_user_id)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Delete a product listing.
    
    Only the product owner can delete their products.
    
    Args:
        product_id: Product ID (integer)
        current_user_id: Current authenticated user ID
        db: Database session
        
    Raises:
        HTTPException: If product not found or user not authorized
    """
    service = ProductService(db)
    service.delete_product(product_id, current_user_id)
    return None
