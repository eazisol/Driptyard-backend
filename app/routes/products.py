"""
Product management routes.

This module contains product CRUD endpoints and listing APIs.
"""

from typing import Optional, List, Any, Dict
from uuid import UUID
from decimal import Decimal, InvalidOperation
from datetime import datetime, timedelta
import random
import string
import json
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form, Request
from starlette.datastructures import UploadFile as StarletteUploadFile
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
import math

from app.database import get_db, settings
from app.security import get_current_user_id
from app.models.product import Product
from app.models.user import User
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductListResponse,
    ProductDetailResponse,
    ProductPaginationResponse,
    SellerInfo,
    ProductVerificationRequest
)
from app.services.s3 import get_s3_service
from app.services.email import email_service

router = APIRouter()


def _generate_verification_code() -> str:
    """Generate a 6-digit numeric verification code."""
    return ''.join(random.choices(string.digits, k=6))


def _get_verification_expiry() -> datetime:
    """Return the expiry datetime for product verification codes."""
    return datetime.utcnow() + timedelta(minutes=settings.PRODUCT_VERIFICATION_CODE_EXPIRY_MINUTES)


def _parse_bool(value: Optional[Any], default: bool = False) -> bool:
    """Parse a flexible truthy/falsey string into boolean."""
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "on"}


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
        product_type=product.product_type,
        product_style=product.product_style,
        colors=product.colors or [],
        purchase_button_enabled=product.purchase_button_enabled,
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
        is_verified=product.is_verified,
        gender=product.gender,
        product_type=product.product_type,
        sub_category=product.sub_category,
        designer=product.designer,
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
    try:
        owner_uuid = UUID(current_user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user identifier"
        )

    user = db.query(User).filter(User.id == owner_uuid).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    query = db.query(Product).filter(Product.owner_id == owner_uuid)

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

    items = [product_to_list_response(product, user) for product in products]
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
                Product.title.ilike(search_term),
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
    
    # Extract form fields
    title = form.get("title")
    description = form.get("description")
    price = form.get("price")
    category = form.get("category")
    condition = form.get("condition")
    dealMethod = form.get("dealMethod")
    meetupDate = form.get("meetupDate")
    meetupLocation = form.get("meetupLocation")
    meetupTime = form.get("meetupTime")
    meetupLocations_raw = form.get("meetupLocations")
    stockQuantity = form.get("stockQuantity")

    gender = form.get("gender")
    productType = form.get("productType")
    subCategory = form.get("subCategory")
    designer = form.get("designer")
    size = form.get("size")
    colors_raw = form.get("colors")
    productStyle = form.get("productStyle")

    measurementChest = form.get("measurementChest")
    measurementSleeveLength = form.get("measurementSleeveLength")
    measurementLength = form.get("measurementLength")
    measurementHem = form.get("measurementHem")
    measurementShoulders = form.get("measurementShoulders")

    purchaseButtonEnabled_raw = form.get("purchaseButtonEnabled")
    deliveryMethod = form.get("deliveryMethod")
    deliveryTime = form.get("deliveryTime")
    deliveryFee_raw = form.get("deliveryFee")
    deliveryFeeType = form.get("deliveryFeeType")
    trackingProvided_raw = form.get("trackingProvided")
    shippingAddress = form.get("shippingAddress")
    
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

    purchase_button_enabled = _parse_bool(purchaseButtonEnabled_raw, default=True)
    tracking_provided = _parse_bool(trackingProvided_raw, default=False)

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
    if not designer:
        required_fields.append("designer")
    if not productStyle:
        required_fields.append("productStyle")
    if required_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Missing required fields: {', '.join(required_fields)}"
        )

    normalized_category = category.lower()
    if normalized_category in {"fashion", "lifestyle"} and not gender:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="gender is required for Fashion or Lifestyle categories"
        )

    if productType and productType.lower() in {"tops", "bottoms", "footwear", "accessories"} and not size:
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
    
    # Verify user exists and fetch UUID instance
    try:
        user_uuid = UUID(current_user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user identifier"
        )

    user = db.query(User).filter(User.id == user_uuid).first()
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
    
    # Handle image uploads - parse from multipart form
    # Frontend may send as 'images', 'images[0]', 'images[1]', etc.
    image_urls = []
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
    
    # Validate minimum number of images (4 required)
    if len(files_to_process) < 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Minimum 4 product images are required. Received {len(files_to_process)} valid image(s). Debug: {debug_info}"
        )

    if files_to_process:
        # Validate number of images
        if len(files_to_process) > 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 10 images allowed per product"
            )
        
        # Validate and upload images
        s3_service = get_s3_service()
        for img in files_to_process:
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
    verification_code = _generate_verification_code()
    verification_expires_at = _get_verification_expiry()

    deal_method_value = "Delivery" if normalized_deal_method == "delivery" else "Meet Up"
    stock_status_value = "In Stock" if stock_quantity_value > 0 else "Out of Stock"

    product = Product(
        owner_id=user_uuid,
        title=title,
        description=description,
        price=price_decimal,
        category=category,
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
        gender=gender,
        product_type=productType,
        sub_category=subCategory,
        designer=designer,
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
    
    db.add(product)
    db.flush()

    email_sent = email_service.send_product_verification_email(
        email=user.email,
        product_title=title,
        verification_code=verification_code
    )

    if not email_sent:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email. Please try again later."
        )

    db.commit()
    db.refresh(product)
    
    return product_to_detail_response(product, user)


@router.post("/{product_id}/verification/send", status_code=status.HTTP_200_OK)
async def send_product_verification_code(
    product_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Send or resend the verification code for a product listing."""
    try:
        product_uuid = UUID(product_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid product ID format"
        )

    product = db.query(Product).filter(Product.id == product_uuid).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    if str(product.owner_id) != current_user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to verify this product")

    if product.is_verified:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Product is already verified")

    user = db.query(User).filter(User.id == product.owner_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Owner not found")

    product.verification_code = _generate_verification_code()
    product.verification_expires_at = _get_verification_expiry()
    product.verification_attempts = 0
    product.is_active = False

    db.flush()

    email_sent = email_service.send_product_verification_email(
        email=user.email,
        product_title=product.title,
        verification_code=product.verification_code
    )

    if not email_sent:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to send verification email")

    db.commit()

    return {"message": "Verification code sent to your registered email"}


@router.post("/{product_id}/verification", response_model=ProductDetailResponse)
async def verify_product_listing(
    product_id: str,
    verification_data: ProductVerificationRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Verify a product listing using the received verification code."""
    try:
        product_uuid = UUID(product_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid product ID format"
        )

    product = db.query(Product).filter(Product.id == product_uuid).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    if str(product.owner_id) != current_user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to verify this product")

    if product.is_verified:
        seller = db.query(User).filter(User.id == product.owner_id).first()
        if not seller:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Seller not found")
        return product_to_detail_response(product, seller)

    if not product.verification_code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No verification code found. Request a new code.")

    if product.verification_expires_at and datetime.utcnow() > product.verification_expires_at:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification code has expired. Request a new code.")

    if product.verification_attempts >= settings.PRODUCT_VERIFICATION_MAX_ATTEMPTS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Maximum verification attempts reached. Request a new code.")

    if product.verification_code != verification_data.verification_code:
        product.verification_attempts += 1
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification code")

    product.is_verified = True
    product.is_active = True
    product.verification_code = None
    product.verification_expires_at = None
    product.verification_attempts = 0

    db.commit()
    db.refresh(product)

    seller = db.query(User).filter(User.id == product.owner_id).first()
    if not seller:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Seller not found")

    return product_to_detail_response(product, seller)


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
