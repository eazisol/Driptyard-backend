"""
Application configuration settings.

This module handles all configuration settings using Pydantic BaseSettings
for environment variable management and validation.
"""

from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application Configuration
    PROJECT_NAME: str = Field(default="Driptyard Backend", description="Project name")
    VERSION: str = Field(default="1.0.0", description="Application version")
    API_V1_STR: str = Field(default="/api/v1", description="API v1 prefix")
    
    # Database Configuration
    DATABASE_URL: str = Field(..., description="PostgreSQL database URL")
    
    # Security Configuration
    SECRET_KEY: str = Field(..., description="Secret key for JWT tokens")
    ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30, 
        description="Access token expiration time in minutes"
    )
    
    # CORS Configuration
    ALLOWED_HOSTS: List[str] = Field(
        default=["*"], 
        description="Allowed CORS origins"
    )
    
    # Email Configuration (for future use)
    SMTP_TLS: bool = Field(default=True, description="Use TLS for SMTP")
    SMTP_PORT: int = Field(default=587, description="SMTP port")
    SMTP_HOST: Optional[str] = Field(default=None, description="SMTP host")
    SMTP_USER: Optional[str] = Field(default=None, description="SMTP username")
    SMTP_PASSWORD: Optional[str] = Field(default=None, description="SMTP password")
    
    # File Upload Configuration
    MAX_FILE_SIZE: int = Field(
        default=10485760,  # 10MB
        description="Maximum file upload size in bytes"
    )
    UPLOAD_DIR: str = Field(
        default="static/uploads",
        description="Directory for file uploads"
    )
    
    # Redis Configuration (for future caching/sessions)
    REDIS_URL: Optional[str] = Field(
        default=None,
        description="Redis URL for caching and sessions"
    )
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
