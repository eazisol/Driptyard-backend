"""
Search-related Pydantic schemas.

This module contains all search-related request and response schemas.
"""

from typing import Optional, List
from pydantic import BaseModel, Field


class ProductSearchResult(BaseModel):
    """Schema for product in search results."""
    
    id: int = Field(..., description="Product ID")
    title: str = Field(..., description="Product title")
    price: float = Field(..., description="Product price")
    image: Optional[str] = Field(None, description="Product image URL")
    category: Optional[str] = Field(None, description="Category name")
    slug: str = Field(..., description="Product slug (generated from title)")


class CategorySearchResult(BaseModel):
    """Schema for category in search results."""
    
    id: int = Field(..., description="Category ID")
    name: str = Field(..., description="Category name")
    slug: str = Field(..., description="Category slug")
    product_count: int = Field(..., description="Number of products in category")


class BrandSearchResult(BaseModel):
    """Schema for brand in search results."""
    
    id: int = Field(..., description="Brand ID")
    name: str = Field(..., description="Brand name")
    slug: str = Field(..., description="Brand slug")
    product_count: int = Field(..., description="Number of products for this brand")


class UserSearchResult(BaseModel):
    """Schema for user/seller in search results."""
    
    id: int = Field(..., description="User ID")
    name: str = Field(..., description="User display name")
    username: str = Field(..., description="Username")
    avatar: Optional[str] = Field(None, description="Avatar URL")
    is_verified: bool = Field(default=False, description="Whether user is verified")


class SearchSuggestionsResponse(BaseModel):
    """Schema for search suggestions response."""
    
    products: List[ProductSearchResult] = Field(default_factory=list, description="Product search results")
    categories: List[CategorySearchResult] = Field(default_factory=list, description="Category search results")
    brands: List[BrandSearchResult] = Field(default_factory=list, description="Brand search results")
    users: List[UserSearchResult] = Field(default_factory=list, description="User search results")


class SearchSuggestionsAPIResponse(BaseModel):
    """Schema for search suggestions API response."""
    
    success: bool = Field(default=True, description="Request success status")
    data: SearchSuggestionsResponse = Field(..., description="Search suggestions data")


class RecentSearchesResponse(BaseModel):
    """Schema for recent searches response."""
    
    searches: List[str] = Field(..., description="List of recent search queries")


class RecentSearchesAPIResponse(BaseModel):
    """Schema for recent searches API response."""
    
    success: bool = Field(default=True, description="Request success status")
    data: RecentSearchesResponse = Field(..., description="Recent searches data")


class SaveRecentSearchRequest(BaseModel):
    """Schema for saving a recent search."""
    
    query: str = Field(..., min_length=1, max_length=255, description="Search query to save")


class SaveRecentSearchResponse(BaseModel):
    """Schema for save recent search response."""
    
    success: bool = Field(default=True, description="Request success status")
    message: str = Field(..., description="Success message")


class PopularSearchItem(BaseModel):
    """Schema for a popular search item."""
    
    query: str = Field(..., description="Search query")
    count: int = Field(..., description="Number of searches")
    trend: Optional[str] = Field(None, description="Trend indicator: 'up', 'down', or 'stable'")


class PopularSearchesResponse(BaseModel):
    """Schema for popular searches response."""
    
    searches: List[str] = Field(..., description="List of popular search queries (simple format)")


class PopularSearchesDetailedResponse(BaseModel):
    """Schema for popular searches response with trend data."""
    
    searches: List[PopularSearchItem] = Field(..., description="List of popular search queries with metadata")


class PopularSearchesAPIResponse(BaseModel):
    """Schema for popular searches API response."""
    
    success: bool = Field(default=True, description="Request success status")
    data: PopularSearchesResponse = Field(..., description="Popular searches data")

