"""
Product-related Pydantic schemas.

This module contains all product-related request and response schemas.
"""

from typing import Optional, List, Dict, Any, Union
from decimal import Decimal
from datetime import datetime
import json

from pydantic import BaseModel, Field, field_validator

from app.schemas.base import BaseCreateSchema, BaseUpdateSchema, BaseResponseSchema


class SellerInfo(BaseModel):
    """Schema for seller information."""

    id: str = Field(..., description="Seller ID")
    username: str = Field(..., description="Seller username")
    rating: float = Field(default=0.0, description="Seller rating")
    total_sales: int = Field(default=0, description="Total number of sales")
    avatar_url: Optional[str] = Field(None, description="Seller avatar URL")
    is_verified: bool = Field(default=False, description="Whether seller is verified")


class ProductCreate(BaseCreateSchema):
    """Schema for creating a product."""

    title: str = Field(..., min_length=1, max_length=255, description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: str = Field(..., description="Product price as string")
    category: Optional[str] = Field(None, description="Product category ID (integer or string)")
    condition: Optional[str] = Field(None, description="Product condition")

    # Deal method and meetup details
    dealMethod: str = Field(..., description="Deal method: 'Delivery' or 'Meet Up'")
    meetupDate: Optional[str] = Field(None, description="Meetup date (YYYY-MM-DD)")
    meetupLocation: Optional[str] = Field(None, max_length=255, description="Meetup location")
    meetupTime: Optional[str] = Field(None, description="Meetup time (HH:MM)")
    meetupLocations: Optional[str] = Field(None, description="JSON stringified meetup locations or array of location objects")

    # Inventory
    stockQuantity: Optional[str] = Field(None, description="Stock quantity as string")

    # Product classification
    gender: Optional[str] = Field(None, description="Target gender ID for the product (integer or string)")
    productType: Optional[str] = Field(None, description="Product type ID based on category (integer or string)")
    subCategory: Optional[str] = Field(None, description="Product sub-category ID (integer or string)")
    brand: Optional[str] = Field(None, description="Product brand ID (integer or string)")
    size: Optional[str] = Field(None, description="Product size")
    colors: Optional[str] = Field(None, description="JSON stringified array of colors or array of color strings")
    productStyle: Optional[str] = Field(None, description="Product style")

    # Measurements (stored as strings)
    measurementChest: Optional[str] = Field(None, description="Chest measurement")
    measurementSleeveLength: Optional[str] = Field(None, description="Sleeve length measurement")
    measurementLength: Optional[str] = Field(None, description="Length measurement")
    measurementHem: Optional[str] = Field(None, description="Hem measurement")
    measurementShoulders: Optional[str] = Field(None, description="Shoulder measurement")

    # Purchase button configuration
    purchaseButtonEnabled: Optional[Union[bool, str]] = Field(None, description="Whether the buy button is enabled (boolean or string)")

    # Delivery configuration
    deliveryMethod: Optional[str] = Field(None, description="Delivery method: own or partner")
    deliveryTime: Optional[str] = Field(None, description="Delivery timeframe identifier")
    deliveryFee: Optional[str] = Field(None, description="Delivery fee amount as string")
    deliveryFeeType: Optional[str] = Field(None, description="Delivery fee type: free or custom")
    trackingProvided: Optional[Union[bool, str]] = Field(None, description="Whether tracking is provided (boolean or string)")
    
    @field_validator('purchaseButtonEnabled', 'trackingProvided', mode='before')
    @classmethod
    def validate_boolean_fields(cls, v):
        """Accept both boolean and string values."""
        if v is None:
            return None
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v
        raise ValueError("Field must be a boolean or string")
    shippingAddress: Optional[str] = Field(None, description="Seller shipping address for partner delivery")

    # Images
    images: List[str] = Field(..., min_length=4, max_length=10, description="List of S3 image URLs (minimum 4, maximum 10)")

    # Additional fields for internal use
    currentStep: Optional[int] = Field(None, description="Current step in creation process")
    
    @field_validator('colors', mode='before')
    @classmethod
    def validate_colors(cls, v):
        """Convert list to JSON string if needed."""
        if v is None:
            return None
        if isinstance(v, list):
            return json.dumps(v)
        if isinstance(v, str):
            return v
        raise ValueError("colors must be a string or list")
    
    @field_validator('meetupLocations', mode='before')
    @classmethod
    def validate_meetup_locations(cls, v):
        """Convert list to JSON string if needed."""
        if v is None:
            return None
        if isinstance(v, list):
            return json.dumps(v)
        if isinstance(v, str):
            return v
        raise ValueError("meetupLocations must be a string or list")
    
    @field_validator('category', 'gender', 'productType', 'subCategory', 'brand', mode='before')
    @classmethod
    def validate_id_fields(cls, v):
        """Convert integer to string if needed."""
        if v is None:
            return None
        if isinstance(v, int):
            return str(v)
        if isinstance(v, str):
            return v
        raise ValueError("Field must be an integer or string")


class ProductUpdate(BaseUpdateSchema):
    """Schema for updating a product."""

    title: Optional[str] = Field(None, min_length=1, max_length=255, description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: Optional[Decimal] = Field(None, gt=0, description="Product price")
    category: Optional[str] = Field(None, max_length=100, description="Product category")
    condition: Optional[str] = Field(None, description="Product condition")
    condition_badge: Optional[str] = Field(None, description="Condition badge")

    stock_quantity: Optional[int] = Field(None, ge=0, description="Stock quantity")
    stock_status: Optional[str] = Field(None, description="Stock status")

    location: Optional[str] = Field(None, max_length=255, description="Product location")
    shipping_cost: Optional[Decimal] = Field(None, ge=0, description="Shipping cost")
    delivery_days: Optional[str] = Field(None, description="Estimated delivery time")

    brand: Optional[str] = Field(None, max_length=100, description="Product brand")
    model: Optional[str] = Field(None, max_length=100, description="Product model")
    year: Optional[int] = Field(None, ge=1900, le=2030, description="Product year")

    gender: Optional[str] = Field(None, description="Target gender for the product")
    product_type: Optional[str] = Field(None, description="Product type based on category")
    sub_category: Optional[str] = Field(None, description="Product sub-category")
    brand: Optional[str] = Field(None, description="Product brand")
    size: Optional[str] = Field(None, description="Product size")
    colors: Optional[List[str]] = Field(None, description="List of product colors")
    product_style: Optional[str] = Field(None, description="Product style")
    measurement_chest: Optional[str] = Field(None, description="Chest measurement")
    measurement_sleeve_length: Optional[str] = Field(None, description="Sleeve length measurement")
    measurement_length: Optional[str] = Field(None, description="Length measurement")
    measurement_hem: Optional[str] = Field(None, description="Hem measurement")
    measurement_shoulders: Optional[str] = Field(None, description="Shoulder measurement")

    purchase_button_enabled: Optional[bool] = Field(None, description="Whether the buy button is enabled")
    delivery_method: Optional[str] = Field(None, description="Delivery method")
    delivery_time: Optional[str] = Field(None, description="Delivery timeframe identifier")
    delivery_fee: Optional[Decimal] = Field(None, ge=0, description="Delivery fee amount")
    delivery_fee_type: Optional[str] = Field(None, description="Delivery fee type")
    tracking_provided: Optional[bool] = Field(None, description="Whether tracking is provided")
    shipping_address: Optional[str] = Field(None, description="Seller shipping address")
    meetup_locations: Optional[List[Dict[str, Any]]] = Field(None, description="Meetup locations configuration")

    images: Optional[List[str]] = Field(None, description="Product image URLs")
    specifications: Optional[Dict[str, Any]] = Field(None, description="Product specifications")
    key_features: Optional[List[str]] = Field(None, description="Key features")
    tags: Optional[List[str]] = Field(None, description="Product tags")

    return_policy: Optional[str] = Field(None, description="Return policy")
    warranty_info: Optional[str] = Field(None, description="Warranty information")
    packaging_info: Optional[str] = Field(None, description="Packaging info")

    is_active: Optional[bool] = Field(None, description="Whether product is active")
    is_spotlighted: Optional[bool] = Field(None, description="Whether product is spotlighted")


class ProductVerificationRequest(BaseModel):
    """Schema for verifying a product using a code."""

    verification_code: str = Field(..., min_length=6, max_length=6, description="6-digit verification code")

    @field_validator('verification_code')
    @classmethod
    def validate_verification_code(cls, value: str) -> str:
        if not value.isdigit():
            raise ValueError("Verification code must contain only digits")
        return value


class ProductListResponse(BaseModel):
    """Schema for product list item (card view)."""

    id: str = Field(..., description="Product ID")
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description (short)")
    price: Decimal = Field(..., description="Product price")
    condition: Optional[str] = Field(None, description="Product condition")
    images: List[str] = Field(default_factory=list, description="Product images")
    rating: float = Field(default=0.0, description="Product rating")
    review_count: int = Field(default=0, description="Number of reviews")
    stock_status: str = Field(..., description="Stock status")
    deal_method: str = Field(..., description="Deal method")
    product_type: Optional[str] = Field(None, description="Product type")
    product_style: Optional[str] = Field(None, description="Product style")
    colors: List[str] = Field(default_factory=list, description="Product colors")
    purchase_button_enabled: bool = Field(..., description="Whether the buy button is enabled")
    seller: SellerInfo = Field(..., description="Seller information")
    created_at: datetime = Field(..., description="Creation timestamp")
    is_active: bool = Field(..., description="Whether product is active")
    is_spotlighted: bool = Field(..., description="Whether product is spotlighted")

    class Config:
        from_attributes = True


class ProductDetailResponse(BaseResponseSchema):
    """Schema for product detail response (full view)."""

    # Basic info
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: Decimal = Field(..., description="Product price")
    category: Optional[str] = Field(None, description="Product category ID")
    category_name: Optional[str] = Field(None, description="Product category name")
    condition: Optional[str] = Field(None, description="Product condition")
    gender: Optional[str] = Field(None, description="Target gender ID for the product")
    gender_name: Optional[str] = Field(None, description="Target gender name for the product")
    product_type: Optional[str] = Field(None, description="Product type ID based on category")
    product_type_name: Optional[str] = Field(None, description="Product type name based on category")
    sub_category: Optional[str] = Field(None, description="Product sub-category ID")
    sub_category_name: Optional[str] = Field(None, description="Product sub-category name")
    brand: Optional[str] = Field(None, description="Product brand ID")
    brand_name: Optional[str] = Field(None, description="Product brand name")
    size: Optional[str] = Field(None, description="Product size")
    colors: List[str] = Field(default_factory=list, description="Product colors")
    product_style: Optional[str] = Field(None, description="Product style")

    # Deal method and meetup details
    deal_method: str = Field(..., description="Deal method")
    meetup_date: Optional[str] = Field(None, description="Meetup date")
    meetup_location: Optional[str] = Field(None, description="Meetup location")
    meetup_time: Optional[str] = Field(None, description="Meetup time")
    meetup_locations: Optional[List[Dict[str, Any]]] = Field(None, description="Meetup locations configuration")

    # Stock
    stock_quantity: int = Field(..., description="Stock quantity")
    stock_status: str = Field(..., description="Stock status")

    # Purchase configuration
    purchase_button_enabled: bool = Field(..., description="Whether the buy button is enabled")

    # Delivery configuration
    delivery_method: Optional[str] = Field(None, description="Delivery method")
    delivery_time: Optional[str] = Field(None, description="Delivery timeframe identifier")
    delivery_fee: Optional[Decimal] = Field(None, description="Delivery fee amount")
    delivery_fee_type: Optional[str] = Field(None, description="Delivery fee type")
    tracking_provided: bool = Field(default=False, description="Whether tracking is provided")
    shipping_address: Optional[str] = Field(None, description="Seller shipping address")

    # Measurements
    measurement_chest: Optional[str] = Field(None, description="Chest measurement")
    measurement_sleeve_length: Optional[str] = Field(None, description="Sleeve length measurement")
    measurement_length: Optional[str] = Field(None, description="Length measurement")
    measurement_hem: Optional[str] = Field(None, description="Hem measurement")
    measurement_shoulders: Optional[str] = Field(None, description="Shoulder measurement")

    # Ratings
    rating: float = Field(default=0.0, description="Product rating")
    review_count: int = Field(default=0, description="Number of reviews")

    # Images
    images: List[str] = Field(default_factory=list, description="Product image URLs")

    # Status
    is_active: bool = Field(..., description="Whether product is active")
    is_sold: bool = Field(..., description="Whether product is sold")
    is_spotlighted: bool = Field(..., description="Whether product is spotlighted")
    is_verified: bool = Field(..., description="Whether product has been verified")

    # Seller info
    seller: SellerInfo = Field(..., description="Seller information")

    class Config:
        from_attributes = True


class ProductPaginationResponse(BaseModel):
    """Schema for paginated product list response."""

    items: List[ProductListResponse] = Field(..., description="List of products")
    total: int = Field(..., description="Total number of products")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")