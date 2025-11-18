"""
Category and brand management routes.

This module contains endpoints for retrieving categories and brands.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.category import (
    MainCategory,
    CategoryType,
    SubCategory,
    Brand,
    Gender
)
from app.schemas.category import (
    MainCategoryResponse,
    CategoryTypeResponse,
    SubCategoryResponse,
    BrandResponse,
    GenderResponse,
    CategoriesListResponse,
    CategoryTypesListResponse,
    SubCategoriesListResponse,
    BrandsListResponse,
    GendersListResponse,
    MainCategoryWithTypesResponse,
    CategoryTypeWithSubCategoriesResponse,
    SubCategoryWithDetailsResponse,
    CompleteCategoryResponse,
    CategoryTypeWithSubCategoriesFullResponse,
    SubCategoryFullResponse,
    AllCategoriesCompleteResponse
)

router = APIRouter()


@router.get("/genders", response_model=GendersListResponse)
async def get_genders(
    db: Session = Depends(get_db)
):
    """
    Get all genders.
    
    Returns:
        List of all genders (male, female, unisex)
    """
    genders = db.query(Gender).order_by(Gender.name).all()
    return GendersListResponse(genders=[GenderResponse.model_validate(g, from_attributes=True) for g in genders])


@router.get("/main-categories", response_model=CategoriesListResponse)
async def get_main_categories(
    db: Session = Depends(get_db)
):
    """
    Get all main categories.
    
    Returns:
        List of all main categories (Fashion, Collectibles, Lifestyle)
    """
    main_categories = db.query(MainCategory).order_by(MainCategory.name).all()
    return CategoriesListResponse(
        main_categories=[MainCategoryResponse.model_validate(mc, from_attributes=True) for mc in main_categories]
    )


@router.get("/main-categories/{main_category_id}", response_model=MainCategoryWithTypesResponse)
async def get_main_category_with_types(
    main_category_id: str,
    db: Session = Depends(get_db)
):
    """
    Get a main category with its category types.
    
    Args:
        main_category_id: ID of the main category (integer)
        
    Returns:
        Main category with its category types
    """
    main_category = db.query(MainCategory).filter(MainCategory.id == main_category_id).first()
    if not main_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Main category not found"
        )
    
    category_types = db.query(CategoryType).filter(
        CategoryType.main_category_id == main_category.id
    ).order_by(CategoryType.name).all()
    
    return MainCategoryWithTypesResponse(
        **MainCategoryResponse.model_validate(main_category, from_attributes=True).model_dump(),
        category_types=[CategoryTypeResponse.model_validate(ct, from_attributes=True) for ct in category_types]
    )


@router.get("/category-types", response_model=CategoryTypesListResponse)
async def get_category_types(
    main_category_id: Optional[str] = Query(None, description="Filter by main category ID"),
    db: Session = Depends(get_db)
):
    """
    Get all category types.
    
    Args:
        main_category_id: Optional filter by main category ID
        
    Returns:
        List of category types
    """
    query = db.query(CategoryType)
    
    if main_category_id:
        query = query.filter(CategoryType.main_category_id == main_category_id)
    
    category_types = query.order_by(CategoryType.name).all()
    return CategoryTypesListResponse(
        category_types=[CategoryTypeResponse.model_validate(ct, from_attributes=True) for ct in category_types]
    )


@router.get("/category-types/{category_type_id}", response_model=CategoryTypeWithSubCategoriesResponse)
async def get_category_type_with_sub_categories(
    category_type_id: str,
    db: Session = Depends(get_db)
):
    """
    Get a category type with its sub categories.
    
    Args:
        category_type_id: int - ID of the category type
        
    Returns:
        Category type with its sub categories
    """
    category_type = db.query(CategoryType).filter(CategoryType.id == category_type_id).first()
    if not category_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category type not found"
        )
    
    sub_categories = db.query(SubCategory).filter(
        SubCategory.type_id == category_type.id
    ).order_by(SubCategory.name).all()
    
    return CategoryTypeWithSubCategoriesResponse(
        **CategoryTypeResponse.model_validate(category_type, from_attributes=True).model_dump(),
        sub_categories=[SubCategoryResponse.model_validate(sc, from_attributes=True) for sc in sub_categories]
    )


@router.get("/sub-categories", response_model=SubCategoriesListResponse)
async def get_sub_categories(
    category_type_id: Optional[str] = Query(None, description="Filter by category type ID"),
    gender_id: Optional[str] = Query(None, description="Filter by gender ID"),
    db: Session = Depends(get_db)
):
    """
    Get all sub categories.
    
    Args:
        category_type_id: Optional filter by category type ID
        gender_id: Optional filter by gender ID
        
    Returns:
        List of sub categories
    """
    query = db.query(SubCategory)
    
    if category_type_id:
        query = query.filter(SubCategory.type_id == category_type_id)
    
    if gender_id:
        query = query.filter(SubCategory.gender_id == gender_id)
    
    sub_categories = query.order_by(SubCategory.name).all()
    return SubCategoriesListResponse(
        sub_categories=[SubCategoryResponse.model_validate(sc, from_attributes=True) for sc in sub_categories]
    )


@router.get("/sub-categories/{sub_category_id}", response_model=SubCategoryWithDetailsResponse)
async def get_sub_category_with_details(
    sub_category_id: str,
    db: Session = Depends(get_db)
):
    """
    Get a sub category with its details (category type and gender).
    
    Args:
        sub_category_id: int - ID of the sub category
        
    Returns:
        Sub category with its related information
    """
    sub_category = db.query(SubCategory).filter(SubCategory.id == sub_category_id).first()
    if not sub_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sub category not found"
        )
    
    category_type = None
    gender = None
    
    if sub_category.type_id:
        category_type = db.query(CategoryType).filter(CategoryType.id == sub_category.type_id).first()
    
    if sub_category.gender_id:
        gender = db.query(Gender).filter(Gender.id == sub_category.gender_id).first()
    
    return SubCategoryWithDetailsResponse(
        **SubCategoryResponse.model_validate(sub_category, from_attributes=True).model_dump(),
        category_type=CategoryTypeResponse.model_validate(category_type, from_attributes=True) if category_type else None,
        gender=GenderResponse.model_validate(gender, from_attributes=True) if gender else None
    )


@router.get("/brands", response_model=BrandsListResponse)
async def get_brands(
    active_only: bool = Query(True, description="Return only active brands"),
    db: Session = Depends(get_db)
):
    """
    Get all brands.
    
    Args:
        active_only: If True, return only active brands
        
    Returns:
        List of brands
    """
    query = db.query(Brand)
    
    if active_only:
        query = query.filter(Brand.active == True)
    
    brands = query.order_by(Brand.name).all()
    return BrandsListResponse(
        brands=[BrandResponse.model_validate(b, from_attributes=True) for b in brands]
    )


@router.get("/brands/{brand_id}", response_model=BrandResponse)
async def get_brand(
    brand_id: str,
    db: Session = Depends(get_db)
):
    """
    Get a specific brand by ID.
    
    Args:
        brand_id: int - ID of the brand
        
    Returns:
        Brand information
    """
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brand not found"
        )
    
    return BrandResponse.model_validate(brand, from_attributes=True)


@router.get("/complete/{main_category_id}", response_model=CompleteCategoryResponse)
async def get_complete_category(
    main_category_id: str,
    db: Session = Depends(get_db)
):
    """
    Get complete category hierarchy in a single response.
    
    Returns the main category with all its types and sub-categories in a nested structure:
    - category_id and category_name
    - types array with type_id, type_name
    - sub_categories array with full sub category objects
    
    Args:
        main_category_id: ID of the main category (integer)
        
    Returns:
        Complete category hierarchy with all nested data
    """
    # Get main category
    main_category = db.query(MainCategory).filter(MainCategory.id == main_category_id).first()
    if not main_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Main category not found"
        )
    
    return _build_complete_category(main_category, db)


def _build_complete_category(main_category: MainCategory, db: Session) -> CompleteCategoryResponse:
    """
    Helper function to build complete category response for a main category.
    
    Args:
        main_category: MainCategory model instance
        db: Database session
        
    Returns:
        CompleteCategoryResponse with all nested data
    """
    # Get all category types for this main category
    category_types = db.query(CategoryType).filter(
        CategoryType.main_category_id == main_category.id
    ).order_by(CategoryType.name).all()
    
    # Build the response structure
    types_list = []
    
    for category_type in category_types:
        # Get all sub categories for this category type
        sub_categories = db.query(SubCategory).filter(
            SubCategory.type_id == category_type.id
        ).order_by(SubCategory.name).all()
        
        # Build sub categories with full details
        sub_categories_list = []
        for sub_cat in sub_categories:
            # Get related gender if exists
            gender = None
            if sub_cat.gender_id:
                gender = db.query(Gender).filter(Gender.id == sub_cat.gender_id).first()
            
            # Create full sub category response using the helper method
            sub_cat_data = SubCategoryFullResponse.from_subcategory(
                sub_cat, 
                category_type=category_type, 
                gender=gender
            )
            
            sub_categories_list.append(sub_cat_data)
        
        # Create category type with sub categories
        type_data = CategoryTypeWithSubCategoriesFullResponse(
            type_id=category_type.id,
            type_name=category_type.name,
            sub_categories=sub_categories_list
        )
        types_list.append(type_data)
    
    return CompleteCategoryResponse(
        category_id=main_category.id,
        category_name=main_category.name,
        types=types_list
    )


@router.get("/complete", response_model=AllCategoriesCompleteResponse)
async def get_all_complete_categories(
    db: Session = Depends(get_db)
):
    """
    Get complete category hierarchy for ALL main categories in a single response.
    
    Returns all main categories (Fashion, Collectibles, Lifestyle) with their complete
    nested structure including types and sub-categories.
    
    Returns:
        Complete category hierarchy for all main categories
    """
    # Get all main categories
    main_categories = db.query(MainCategory).order_by(MainCategory.name).all()
    
    # Build complete response for each main category
    categories_list = []
    for main_category in main_categories:
        complete_category = _build_complete_category(main_category, db)
        categories_list.append(complete_category)
    
    return AllCategoriesCompleteResponse(categories=categories_list)

