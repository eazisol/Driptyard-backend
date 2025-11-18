"""
FastAPI application entry point.

This module creates and configures the FastAPI application with all
necessary middleware, routers, and exception handlers.
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import uvicorn

from app.database import settings
from app.routes.auth import router as auth_router
from app.routes.users import router as users_router
from app.routes.products import router as products_router
from app.routes.admin import router as admin_router
from app.routes.categories import router as categories_router


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        FastAPI: Configured FastAPI application instance
    """
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
    async def validation_exception_handler(request, exc: RequestValidationError):
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
