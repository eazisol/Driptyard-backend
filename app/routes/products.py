"""
Product management routes.

This module contains product CRUD endpoints and listing APIs.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.security import get_current_user_id
from app.schemas.product import (
    ProductUpdate,
    ProductDetailResponse,
    ProductPaginationResponse,
    ProductVerificationRequest
)
from app.services.product import ProductService

router = APIRouter()


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
    service = ProductService(db)
    return service.list_featured_products(page, page_size)


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
    service = ProductService(db)
    return service.list_recommended_products(page, page_size)


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
    search: Optional[str] = Query(None, description="Search by title or description"),
    db: Session = Depends(get_db)
):
    """
    List products created by the current authenticated user.

    Supports filtering by listing status and search term for managing listings.

    Args:
        current_user_id: Current authenticated user ID
        page: Page number
        page_size: Items per page
        status_filter: Filter by status (active, inactive, sold, verification_pending)
        search: Search term
        db: Database session

    Returns:
        ProductPaginationResponse: Paginated list of user's products
    """
    service = ProductService(db)
    return service.list_user_products(current_user_id, page, page_size, status_filter, search)


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
    service = ProductService(db)
    return service.list_products(page, page_size, category, search, min_price, max_price, condition)


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
    service = ProductService(db)
    return service.get_product(product_id)


@router.post("/", response_model=ProductDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    request: Request,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Create a new product listing with image uploads.
    
    Send as multipart/form-data.
    
    Args:
        title: Product title
        description: Product description
        price: Product price
        category: Product category
        condition: Product condition
        dealMethod: Deal method (Meet Up or Delivery)
        meetupDate: Optional meetup date
        meetupLocation: Optional meetup location
        meetupTime: Optional meetup time
        images: List of product images (minimum 4, maximum 10)
        current_user_id: Current authenticated user ID
        db: Database session
        
    Returns:
        ProductDetailResponse: Created product details

    Notes:
        A verification code is emailed to the seller after creation. The product
        remains inactive until the code is confirmed via the verification endpoint.
    """
    # Parse form data manually to handle both form fields and files
    form = await request.form()
    
    # Extract form fields into dictionary
    form_data = {}
    for key, value in form.items():
        if key not in ["images"] and not key.startswith("images["):
            form_data[key] = value
    
    # Handle image uploads - parse from multipart form
    # Frontend may send as 'images', 'images[0]', 'images[1]', etc.
    files_to_process: List[UploadFile] = []
    
    # Debug: Log what we're receiving
    debug_info = []
    for key, value in form.multi_items():
        # Check by type name instead of isinstance since there might be import issues
        type_name = type(value).__name__
        is_upload = type_name == "UploadFile" or hasattr(value, 'file')
        debug_info.append(f"Key: {key}, Type: {type_name}, IsUploadFile: {is_upload}, HasFile: {hasattr(value, 'file')}")
        
        # Check if it's a file upload by type name or has file attribute
        if type_name == "UploadFile" or hasattr(value, 'file'):
            # Check if field name matches 'images' pattern
            if key == "images" or key.startswith("images["):
                # Verify the file has a filename (not an empty upload)
                if hasattr(value, 'filename') and value.filename:
                    files_to_process.append(value)
                    debug_info.append(f"  -> Added: Filename: {value.filename}")
    
    # Validate minimum number of images (4 required) - maintain exact error message
    if len(files_to_process) < 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Minimum 4 product images are required. Received {len(files_to_process)} valid image(s). Debug: {debug_info}"
        )
    
    service = ProductService(db)
    return service.create_product(current_user_id, form_data, files_to_process)


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
        product_id: Product UUID
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
        product_id: Product UUID
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
        product_id: Product UUID
        current_user_id: Current authenticated user ID
        db: Database session
        
    Raises:
        HTTPException: If product not found or user not authorized
    """
    service = ProductService(db)
    service.delete_product(product_id, current_user_id)
    return None
