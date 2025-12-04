"""
Search management routes.

This module contains search-related endpoints including suggestions,
recent searches, and popular searches.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.security import get_current_user_id, get_optional_user_id
from app.services.search import SearchService
from app.schemas.search import (
    SearchSuggestionsAPIResponse,
    RecentSearchesAPIResponse,
    SaveRecentSearchRequest,
    SaveRecentSearchResponse,
    PopularSearchesAPIResponse,
)

router = APIRouter()


@router.get("/suggestions", response_model=SearchSuggestionsAPIResponse)
async def get_search_suggestions(
    query: str = Query(..., min_length=1, description="Search query string"),
    limit: int = Query(5, ge=1, le=20, description="Maximum results per entity type"),
    db: Session = Depends(get_db)
):
    """
    Get search suggestions grouped by entity type (products, categories, brands, users).
    
    Args:
        query: Search query string
        limit: Maximum results per entity type (default: 5 for products, 3 for others)
        db: Database session
        
    Returns:
        SearchSuggestionsAPIResponse: Search suggestions grouped by entity type
    """
    service = SearchService(db)
    
    # Set different limits for different entity types
    product_limit = limit
    category_limit = min(limit, 3)
    brand_limit = min(limit, 3)
    user_limit = min(limit, 3)
    
    suggestions = service.get_search_suggestions(
        query=query,
        product_limit=product_limit,
        category_limit=category_limit,
        brand_limit=brand_limit,
        user_limit=user_limit
    )
    
    # Log search analytics (optional, can be done asynchronously)
    try:
        service.log_search_analytics(query=query)
    except Exception:
        # Don't fail the request if analytics logging fails
        pass
    
    return SearchSuggestionsAPIResponse(
        success=True,
        data=suggestions
    )


@router.get("/recent", response_model=RecentSearchesAPIResponse)
async def get_recent_searches(
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get user's recent search queries.
    
    Args:
        current_user_id: Current authenticated user ID
        db: Database session
        
    Returns:
        RecentSearchesAPIResponse: List of recent search queries
        
    Raises:
        HTTPException: If user is not authenticated
    """
    try:
        user_id = int(current_user_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID"
        )
    
    service = SearchService(db)
    searches = service.get_recent_searches(user_id=user_id, limit=10)
    
    return RecentSearchesAPIResponse(
        success=True,
        data={"searches": searches}
    )


@router.post("/recent", response_model=SaveRecentSearchResponse)
async def save_recent_search(
    request: SaveRecentSearchRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Save a search query to user's recent searches.
    
    Args:
        request: Request body containing search query
        current_user_id: Current authenticated user ID
        db: Database session
        
    Returns:
        SaveRecentSearchResponse: Success message
        
    Raises:
        HTTPException: If user is not authenticated or request is invalid
    """
    try:
        user_id = int(current_user_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID"
        )
    
    # Trim and validate query
    query = request.query.strip()
    if not query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query cannot be empty"
        )
    
    service = SearchService(db)
    service.save_recent_search(user_id=user_id, query=query)
    
    return SaveRecentSearchResponse(
        success=True,
        message="Search saved successfully"
    )


@router.delete("/recent", response_model=SaveRecentSearchResponse)
async def clear_recent_searches(
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Clear all recent searches for the authenticated user.
    
    Args:
        current_user_id: Current authenticated user ID
        db: Database session
        
    Returns:
        SaveRecentSearchResponse: Success message
        
    Raises:
        HTTPException: If user is not authenticated
    """
    try:
        user_id = int(current_user_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID"
        )
    
    service = SearchService(db)
    service.clear_recent_searches(user_id=user_id)
    
    return SaveRecentSearchResponse(
        success=True,
        message="Recent searches cleared successfully"
    )


@router.get("/popular", response_model=PopularSearchesAPIResponse)
async def get_popular_searches(
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
    timeframe: str = Query("week", description="Time period: 'day', 'week', or 'month'"),
    db: Session = Depends(get_db)
):
    """
    Get popular/trending search queries.
    
    Args:
        limit: Maximum number of results (default: 10)
        timeframe: Time period for popularity calculation - "day", "week", or "month" (default: "week")
        db: Database session
        
    Returns:
        PopularSearchesAPIResponse: List of popular search queries
    """
    # Validate timeframe
    if timeframe not in ["day", "week", "month"]:
        timeframe = "week"
    
    service = SearchService(db)
    searches = service.get_popular_searches(limit=limit, timeframe=timeframe)
    
    return PopularSearchesAPIResponse(
        success=True,
        data={"searches": searches}
    )

