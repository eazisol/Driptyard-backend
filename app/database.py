"""
Database configuration and session management.

This module handles SQLAlchemy database connection, session management,
configuration settings, and provides the base class for all models.
"""

from typing import List, Optional, Generator
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Create declarative base class for models
Base = declarative_base()


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
    
    # Email Configuration
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
    
    # AWS S3 Configuration
    AWS_ACCESS_KEY_ID: Optional[str] = Field(
        default=None,
        description="AWS Access Key ID for S3"
    )
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(
        default=None,
        description="AWS Secret Access Key for S3"
    )
    AWS_REGION: str = Field(
        default="us-east-1",
        description="AWS region for S3"
    )
    S3_BUCKET_NAME: Optional[str] = Field(
        default=None,
        description="S3 bucket name for file storage"
    )
    S3_BASE_URL: Optional[str] = Field(
        default=None,
        description="S3 base URL for file access"
    )
    
    # Redis Configuration (for future caching/sessions)
    REDIS_URL: Optional[str] = Field(
        default=None,
        description="Redis URL for caching and sessions"
    )
    
    # Email Configuration
    EMAIL_FROM_NAME: str = Field(
        default="Driptyard",
        description="Email sender name"
    )
    EMAIL_FROM_ADDRESS: str = Field(
        default="noreply@driptyard.com",
        description="Email sender address"
    )
    VERIFICATION_CODE_EXPIRY_MINUTES: int = Field(
        default=15,
        description="Email verification code expiry time in minutes"
    )
    
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


# Global settings instance
settings = Settings()

# Create SQLAlchemy engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=300,    # Recycle connections every 5 minutes
    echo=False,          # Set to True for SQL query logging
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get database session.
    
    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables() -> None:
    """
    Create all database tables.
    
    This function should be called after all models are imported.
    """
    Base.metadata.create_all(bind=engine)


def drop_tables() -> None:
    """
    Drop all database tables.
    
    Warning: This will delete all data!
    """
    Base.metadata.drop_all(bind=engine)
