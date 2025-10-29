"""
Product management routes.

This module contains product CRUD endpoints and listing APIs.
"""

from typing import Optional, List
from uuid import UUID
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
import math

from app.database import get_db
from app.security import get_current_user_id
from app.models.product import Product
from app.models.user import User
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductListResponse,
    ProductDetailResponse,
    ProductPaginationResponse,
    SellerInfo
)
from app.services.s3 import get_s3_service

router = APIRouter()


def get_seller_info(user: User) -> SellerInfo:
    """Helper function to extract seller information."""
    return SellerInfo(
        id=str(user.id),
        username=user.username,
        rating=4.8,  # TODO: Calculate from reviews
        total_sales=156,  # TODO: Get from orders
        avatar_url=user.avatar_url
    )


def product_to_list_response(product: Product, seller: User) -> ProductListResponse:
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
        seller=get_seller_info(seller),
        created_at=product.created_at
    )


def product_to_detail_response(product: Product, seller: User) -> ProductDetailResponse:
    """Convert Product model to ProductDetailResponse."""
    return ProductDetailResponse(
        id=str(product.id),
        title=product.title,
        description=product.description,
        price=product.price,
        category=product.category,
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
        seller=get_seller_info(seller),
        created_at=product.created_at,
        updated_at=product.updated_at
    )


@router.get("/featured", response_model=ProductPaginationResponse)
async def get_featured_products(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(12, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    Get featured products listing.
    
    Returns handpicked premium items from verified sellers.
    
    Args:
        page: Page number (starts from 1)
        page_size: Number of items per page
        db: Database session
        
    Returns:
        ProductPaginationResponse: Paginated list of featured products
    """
    # Calculate offset
    offset = (page - 1) * page_size
    
    # Query featured products
    query = db.query(Product).filter(
        and_(
            Product.is_featured == True,
            Product.is_active == True,
            Product.is_sold == False
        )
    ).order_by(Product.created_at.desc())
    
    # Get total count
    total = query.count()
    
    # Get paginated results
    products = query.offset(offset).limit(page_size).all()
    
    # Get seller information for each product
    items = []
    for product in products:
        seller = db.query(User).filter(User.id == product.owner_id).first()
        if seller:
            items.append(product_to_list_response(product, seller))
    
    # Calculate pagination metadata
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


@router.get("/recommended", response_model=ProductPaginationResponse)
async def get_recommended_products(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(12, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    Get recommended products for user.
    
    Returns personalized picks based on user interests.
    
    Args:
        page: Page number (starts from 1)
        page_size: Number of items per page
        db: Database session
        
    Returns:
        ProductPaginationResponse: Paginated list of recommended products
    """
    # Calculate offset
    offset = (page - 1) * page_size
    
    # Query recommended products (non-featured, active products)
    # TODO: Implement recommendation algorithm based on user preferences
    query = db.query(Product).filter(
        and_(
            Product.is_active == True,
            Product.is_sold == False
        )
    ).order_by(Product.rating.desc(), Product.created_at.desc())
    
    # Get total count
    total = query.count()
    
    # Get paginated results
    products = query.offset(offset).limit(page_size).all()
    
    # Get seller information for each product
    items = []
    for product in products:
        seller = db.query(User).filter(User.id == product.owner_id).first()
        if seller:
            items.append(product_to_list_response(product, seller))
    
    # Calculate pagination metadata
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


@router.get("/", response_model=ProductPaginationResponse)
async def list_products(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(12, ge=1, le=100, description="Items per page"),
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search in name and description"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price"),
    condition: Optional[str] = Query(None, description="Filter by condition"),
    db: Session = Depends(get_db)
):
    """
    List all products with filtering and pagination.
    
    Args:
        page: Page number
        page_size: Items per page
        category: Filter by category
        search: Search term
        min_price: Minimum price filter
        max_price: Maximum price filter
        condition: Filter by condition
        db: Database session
        
    Returns:
        ProductPaginationResponse: Paginated list of products
    """
    # Calculate offset
    offset = (page - 1) * page_size
    
    # Build query
    query = db.query(Product).filter(
        and_(
            Product.is_active == True,
            Product.is_sold == False
        )
    )
    
    # Apply filters
    if category:
        query = query.filter(Product.category == category)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Product.name.ilike(search_term),
                Product.description.ilike(search_term),
                Product.brand.ilike(search_term)
            )
        )
    
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
    
    if condition:
        query = query.filter(Product.condition == condition)
    
    # Order by creation date (newest first)
    query = query.order_by(Product.created_at.desc())
    
    # Get total count
    total = query.count()
    
    # Get paginated results
    products = query.offset(offset).limit(page_size).all()
    
    # Get seller information for each product
    items = []
    for product in products:
        seller = db.query(User).filter(User.id == product.owner_id).first()
        if seller:
            items.append(product_to_list_response(product, seller))
    
    # Calculate pagination metadata
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


@router.get("/{product_id}", response_model=ProductDetailResponse)
async def get_product(
    product_id: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed product information by ID.
    
    Returns complete product details including specifications, 
    seller information, ratings, and policies.
    
    Args:
        product_id: Product UUID
        db: Database session
        
    Returns:
        ProductDetailResponse: Complete product details
        
    Raises:
        HTTPException: If product not found
    """
    # Get product
    try:
        product_uuid = UUID(product_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid product ID format"
        )
    
    product = db.query(Product).filter(Product.id == product_uuid).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Get seller information
    seller = db.query(User).filter(User.id == product.owner_id).first()
    
    if not seller:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Seller not found"
        )
    
    return product_to_detail_response(product, seller)


@router.post("/", response_model=ProductDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    title: str = Form(...),
    description: str = Form(...),
    price: str = Form(...),
    category: str = Form(...),
    condition: str = Form(...),
    deal_method: str = Form(..., alias="dealMethod"),
    meetup_date: Optional[str] = Form(None, alias="meetupDate"),
    meetup_location: Optional[str] = Form(None, alias="meetupLocation"),
    meetup_time: Optional[str] = Form(None, alias="meetupTime"),
    images: List[UploadFile] = File(None),
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Create a new product listing with image uploads.
    
    Args:
        title: Product title
        description: Product description
        price: Product price
        category: Product category
        condition: Product condition
        deal_method: Deal method (Meet Up or Delivery)
        meetup_date: Optional meetup date
        meetup_location: Optional meetup location
        meetup_time: Optional meetup time
        images: Optional list of product images (max 10)
        current_user_id: Current authenticated user ID
        db: Database session
        
    Returns:
        ProductDetailResponse: Created product details
    """
    # Verify user exists
    user = db.query(User).filter(User.id == UUID(current_user_id)).first()
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
    
    # Handle image uploads if provided
    image_urls = []
    if images:
        # Validate number of images
        if len(images) > 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 10 images allowed per product"
            )
        
        # Validate and upload images
        s3_service = get_s3_service()
        for img in images:
            if not img.content_type or not img.content_type.startswith('image/'):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File {img.filename} must be an image"
                )
            
            try:
                result = s3_service.upload_file(img, "product_images", current_user_id)
                image_urls.append(result["url"])
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to upload image {img.filename}: {str(e)}"
                )
    
    # Create product
    product = Product(
        owner_id=UUID(current_user_id),
        title=title,
        description=description,
        price=price_decimal,
        category=category,
        condition=condition,
        deal_method=deal_method,
        meetup_date=meetup_date,
        meetup_location=meetup_location,
        meetup_time=meetup_time,
        images=image_urls,
        stock_quantity=1,
        stock_status="In Stock"
    )
    
    db.add(product)
    db.commit()
    db.refresh(product)
    
    return product_to_detail_response(product, user)


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
        product_id: Product UUID
        product_data: Product update data
        current_user_id: Current authenticated user ID
        db: Database session
        
    Returns:
        ProductDetailResponse: Updated product details
        
    Raises:
        HTTPException: If product not found or user not authorized
    """
    # Get product
    try:
        product_uuid = UUID(product_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid product ID format"
        )
    
    product = db.query(Product).filter(Product.id == product_uuid).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Check ownership
    if str(product.owner_id) != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this product"
        )
    
    # Update product
    update_data = product_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)
    
    db.commit()
    db.refresh(product)
    
    # Get seller information
    seller = db.query(User).filter(User.id == product.owner_id).first()
    
    return product_to_detail_response(product, seller)


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
        product_id: Product UUID
        images: List of image files to upload (max 10 total)
        current_user_id: Current authenticated user ID
        db: Database session
        
    Returns:
        ProductDetailResponse: Updated product details with new images
        
    Raises:
        HTTPException: If product not found, user not authorized, or upload fails
    """
    # Get product
    try:
        product_uuid = UUID(product_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid product ID format"
        )
    
    product = db.query(Product).filter(Product.id == product_uuid).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Check ownership
    if str(product.owner_id) != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this product"
        )
    
    # Get existing images
    existing_images = product.images or []
    
    # Validate total number of images
    if len(existing_images) + len(images) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum 10 images allowed per product. You have {len(existing_images)} existing images."
        )
    
    # Upload new images
    s3_service = get_s3_service()
    new_image_urls = []
    
    for img in images:
        if not img.content_type or not img.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File {img.filename} must be an image"
            )
        
        try:
            result = s3_service.upload_file(img, "product_images", current_user_id)
            new_image_urls.append(result["url"])
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload image {img.filename}: {str(e)}"
            )
    
    # Update product images
    product.images = existing_images + new_image_urls
    db.commit()
    db.refresh(product)
    
    # Get seller information
    seller = db.query(User).filter(User.id == product.owner_id).first()
    
    return product_to_detail_response(product, seller)


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
        product_id: Product UUID
        current_user_id: Current authenticated user ID
        db: Database session
        
    Raises:
        HTTPException: If product not found or user not authorized
    """
    # Get product
    try:
        product_uuid = UUID(product_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid product ID format"
        )
    
    product = db.query(Product).filter(Product.id == product_uuid).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Check ownership
    if str(product.owner_id) != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this product"
        )
    
    # Soft delete (mark as inactive)
    product.is_active = False
    db.commit()
    
    return None
