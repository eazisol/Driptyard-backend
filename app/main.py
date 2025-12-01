"""
FastAPI application entry point.

This module creates and configures the FastAPI application with all
necessary middleware, routers, and exception handlers.
"""

from fastapi import FastAPI, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
import uvicorn
import traceback
import logging

from app.database import settings
from app.routes.auth import router as auth_router
from app.routes.users import router as users_router
from app.routes.products import router as products_router
from app.routes.admin import router as admin_router
from app.routes.categories import router as categories_router
from app.routes.moderators import router as moderators_router
from app.routes.follows import router as follows_router


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        FastAPI: Configured FastAPI application instance
    """
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description="C2C E-commerce Backend API",
        openapi_url="/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_HOSTS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add trusted host middleware for security
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS
    )
    
    # Include API routers
    app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
    app.include_router(users_router, prefix="/users", tags=["Users"])
    app.include_router(products_router, prefix="/products", tags=["Products"])
    app.include_router(admin_router, prefix="/admin", tags=["Admin"])
    app.include_router(categories_router, prefix="/categories", tags=["Categories & Brands"])
    app.include_router(moderators_router, prefix="/moderators", tags=["Moderators"])
    app.include_router(follows_router, prefix="/follows", tags=["Follows"])
    # TODO: Add orders router when order management is implemented
    
    # Add custom exception handler for HTTP exceptions
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request, exc: HTTPException):
        """Handle HTTP exceptions."""
        if isinstance(exc.detail, dict):
            content = exc.detail
        else:
            content = {"message": str(exc.detail) if exc.detail else "An error occurred"}
        return JSONResponse(
            status_code=exc.status_code,
            content=content
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle request validation errors with consistent error structure."""
        errors = []
        for error in exc.errors():
            location = list(error.get("loc", []))
            if location and location[0] in {"body", "query", "path"}:
                location = location[1:]
            field_path = ".".join(str(part) for part in location) or "request"
            errors.append({
                "field": field_path,
                "message": error.get("msg", "Invalid value")
            })

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "message": "Invalid request payload",
                "errors": errors
            }
        )
    
    @app.exception_handler(ResponseValidationError)
    async def response_validation_exception_handler(request: Request, exc: ResponseValidationError):
        """Handle response validation errors with meaningful error messages."""
        errors = []
        for error in exc.errors():
            location = list(error.get("loc", []))
            field_path = ".".join(str(part) for part in location) or "response"
            errors.append({
                "field": field_path,
                "message": error.get("msg", "Invalid response value"),
                "input_type": str(type(error.get("input", "unknown"))),
                "expected_type": error.get("type", "unknown")
            })
        
        # Log the full error for debugging
        logging.error(f"Response validation error: {exc.errors()}")
        logging.error(f"Request path: {request.url.path}")
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "message": "Internal server error: Response validation failed",
                "error": "The server generated an invalid response. This is a server-side issue.",
                "errors": errors
            }
        )
    
    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError):
        """Handle database integrity errors."""
        error_message = str(exc.orig) if exc.orig else "Database integrity constraint violation"
        
        # Provide user-friendly messages for common integrity errors
        if "unique constraint" in error_message.lower() or "duplicate key" in error_message.lower():
            message = "A record with this information already exists"
        elif "foreign key constraint" in error_message.lower():
            message = "Cannot perform this operation due to related records"
        elif "not null constraint" in error_message.lower():
            message = "Required field is missing"
        else:
            message = "Database constraint violation"
        
        logging.error(f"Database integrity error: {error_message}")
        logging.error(f"Request path: {request.url.path}")
        
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "message": message,
                "error": "Database constraint violation"
            }
        )
    
    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError):
        """Handle general SQLAlchemy database errors."""
        error_message = str(exc) if exc else "Database error occurred"
        
        logging.error(f"Database error: {error_message}")
        logging.error(f"Request path: {request.url.path}")
        logging.error(traceback.format_exc())
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "message": "A database error occurred",
                "error": "Unable to process request due to database issue"
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle all other unhandled exceptions."""
        error_message = str(exc) if exc else "An unexpected error occurred"
        error_type = type(exc).__name__
        
        # Log the full traceback for debugging
        logging.error(f"Unhandled exception: {error_type}: {error_message}")
        logging.error(f"Request path: {request.url.path}")
        logging.error(f"Request method: {request.method}")
        logging.error(traceback.format_exc())
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "message": "An unexpected error occurred",
                "error": "Internal server error. Please try again later.",
                "error_type": error_type
            }
        )
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "version": settings.VERSION}
    
    return app


# Create the application instance
app = create_app()


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
