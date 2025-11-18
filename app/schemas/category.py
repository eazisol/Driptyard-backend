"""
Category and brand-related Pydantic schemas.

This module contains all category and brand-related response schemas.
"""

from typing import Optional, List
# Removed UUID import - using int for IDs now
from datetime import datetime

from pydantic import BaseModel, Field


class CategoryBaseResponseSchema(BaseModel):
    """Base response schema for category-related models with integer IDs."""
    
    id: int = Field(..., description="Unique identifier")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class GenderResponse(CategoryBaseResponseSchema):
    """Schema for gender response."""
    
    name: str = Field(..., description="Gender name")


class MainCategoryResponse(CategoryBaseResponseSchema):
    """Schema for main category response."""
    
    name: str = Field(..., description="Main category name")


class CategoryTypeResponse(CategoryBaseResponseSchema):
    """Schema for category type response."""
    
    name: str = Field(..., description="Category type name")
    main_category_id: int = Field(..., description="Parent main category ID")


class CategoryTypeWithParentResponse(CategoryTypeResponse):
    """Schema for category type with parent information."""
    
    parent: Optional[MainCategoryResponse] = Field(None, description="Parent main category")


class SubCategoryResponse(CategoryBaseResponseSchema):
    """Schema for sub category response."""
    
    name: str = Field(..., description="Sub category name")
    type_id: int = Field(..., description="Parent category type ID")
    gender_id: Optional[int] = Field(None, description="Gender ID (if applicable)")


class SubCategoryWithDetailsResponse(SubCategoryResponse):
    """Schema for sub category with related information."""
    
    category_type: Optional[CategoryTypeResponse] = Field(None, description="Parent category type")
    gender: Optional[GenderResponse] = Field(None, description="Gender information")


class BrandResponse(CategoryBaseResponseSchema):
    """Schema for brand response."""
    
    name: str = Field(..., description="Brand name")
    active: bool = Field(..., description="Whether the brand is active")


class MainCategoryWithTypesResponse(MainCategoryResponse):
    """Schema for main category with its category types."""
    
    category_types: List[CategoryTypeResponse] = Field(default_factory=list, description="List of category types")


class CategoryTypeWithSubCategoriesResponse(CategoryTypeResponse):
    """Schema for category type with its sub categories."""
    
    sub_categories: List[SubCategoryResponse] = Field(default_factory=list, description="List of sub categories")


class CategoriesListResponse(BaseModel):
    """Schema for list of main categories response."""
    
    main_categories: List[MainCategoryResponse] = Field(..., description="List of main categories")


class CategoryTypesListResponse(BaseModel):
    """Schema for list of category types response."""
    
    category_types: List[CategoryTypeResponse] = Field(..., description="List of category types")


class SubCategoriesListResponse(BaseModel):
    """Schema for list of sub categories response."""
    
    sub_categories: List[SubCategoryResponse] = Field(..., description="List of sub categories")


class BrandsListResponse(BaseModel):
    """Schema for list of brands response."""
    
    brands: List[BrandResponse] = Field(..., description="List of brands")


class GendersListResponse(BaseModel):
    """Schema for list of genders response."""
    
    genders: List[GenderResponse] = Field(..., description="List of genders")


class SubCategoryFullResponse(CategoryBaseResponseSchema):
    """Schema for full sub category response with simplified details."""
    
    sub_category_name: str = Field(..., description="Sub category name")
    gender_id: Optional[int] = Field(None, description="Gender ID (if applicable)")
    gender_name: Optional[str] = Field(None, description="Gender name (if applicable)")
    
    @classmethod
    def from_subcategory(cls, sub_cat, category_type=None, gender=None):
        """Create SubCategoryFullResponse from SubCategory model."""
        return cls(
            id=sub_cat.id,
            sub_category_name=sub_cat.name,
            created_at=sub_cat.created_at,
            updated_at=sub_cat.updated_at,
            gender_id=sub_cat.gender_id,
            gender_name=gender.name if gender else None
        )


class CategoryTypeWithSubCategoriesFullResponse(BaseModel):
    """Schema for category type with sub categories in the full response format."""
    
    type_id: int = Field(..., description="Category type ID")
    type_name: str = Field(..., description="Category type name")
    sub_categories: List[SubCategoryFullResponse] = Field(default_factory=list, description="List of sub categories with full details")


class CompleteCategoryResponse(BaseModel):
    """Schema for complete category hierarchy response."""
    
    category_id: int = Field(..., description="Main category ID")
    category_name: str = Field(..., description="Main category name")
    types: List[CategoryTypeWithSubCategoriesFullResponse] = Field(default_factory=list, description="List of category types with their sub categories")


class AllCategoriesCompleteResponse(BaseModel):
    """Schema for all complete categories hierarchy response."""
    
    categories: List[CompleteCategoryResponse] = Field(..., description="List of all main categories with their complete hierarchy")

